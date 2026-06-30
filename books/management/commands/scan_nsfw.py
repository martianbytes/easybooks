"""
books/management/commands/scan_nsfw.py
─────────────────────────────────────────────────────────────────────────────
Retroactively scans all existing BookImages and user avatars for NSFW content.

Usage:
    # Dry-run: just report, don't delete anything
    python manage.py scan_nsfw

    # Actually delete flagged images from disk + DB / clear avatar fields
    python manage.py scan_nsfw --delete

    # Scan only book images or only avatars
    python manage.py scan_nsfw --books-only
    python manage.py scan_nsfw --avatars-only

    # Re-scan images that were already checked (skips clean ones by default)
    python manage.py scan_nsfw --force

Example output:
    Scanning 42 book images...
    [CLEAN]   book_images/atomic_habit.jpg
    [FLAGGED] book_images/bad_cover.jpg  →  FEMALE_BREAST_EXPOSED (0.87)
    ...
    Scanning 8 avatars...
    [CLEAN]   avatars/2026/05/abc123.png
    ...
    ──────────────────────────────────────────────────────
    Book images : 42 scanned | 1 flagged
    Avatars     :  8 scanned | 0 flagged
    Total       : 50 scanned | 1 flagged
    (dry-run — pass --delete to remove flagged files)
─────────────────────────────────────────────────────────────────────────────
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand

from books.nsfw import check_path_nsfw


class Command(BaseCommand):
    help = "Scan existing uploaded images for NSFW content using NudeNet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            default=False,
            help="Delete flagged images from disk and remove their DB records / clear avatar fields.",
        )
        parser.add_argument(
            "--books-only",
            action="store_true",
            default=False,
            help="Only scan BookImage records.",
        )
        parser.add_argument(
            "--avatars-only",
            action="store_true",
            default=False,
            help="Only scan user avatars.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Re-scan all images even if they were previously checked.",
        )

    def handle(self, *args, **options):
        delete = options["delete"]
        books_only = options["books_only"]
        avatars_only = options["avatars_only"]

        book_flagged = book_scanned = 0
        avatar_flagged = avatar_scanned = 0

        if not avatars_only:
            book_scanned, book_flagged = self._scan_book_images(delete)

        if not books_only:
            avatar_scanned, avatar_flagged = self._scan_avatars(delete)

        total_scanned = book_scanned + avatar_scanned
        total_flagged = book_flagged + avatar_flagged

        self.stdout.write("")
        self.stdout.write("─" * 58)
        self.stdout.write(
            f"Book images : {book_scanned:4d} scanned | {book_flagged} flagged"
        )
        self.stdout.write(
            f"Avatars     : {avatar_scanned:4d} scanned | {avatar_flagged} flagged"
        )
        self.stdout.write(
            f"Total       : {total_scanned:4d} scanned | {total_flagged} flagged"
        )

        if not delete and total_flagged:
            self.stdout.write(
                self.style.WARNING(
                    "\n(dry-run — pass --delete to remove flagged files)"
                )
            )
        elif delete and total_flagged:
            self.stdout.write(
                self.style.SUCCESS(f"\n{total_flagged} flagged file(s) removed.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("\nAll clean!"))

    # ── Book images ───────────────────────────────────────────────────────────

    def _scan_book_images(self, delete):
        from books.models import BookImage  # local import to avoid AppRegistryNotReady

        qs = BookImage.objects.select_related("book").order_by("id")
        total = qs.count()
        self.stdout.write(f"\nScanning {total} book image(s)...")

        scanned = flagged = 0

        for obj in qs:
            if not obj.image:
                continue

            abs_path = os.path.join(settings.MEDIA_ROOT, str(obj.image))

            if not os.path.exists(abs_path):
                self.stdout.write(
                    self.style.WARNING(f"  [MISSING]  {obj.image}")
                )
                continue

            scanned += 1
            is_flagged, detections = check_path_nsfw(abs_path)

            if is_flagged:
                flagged += 1
                detail = "  |  ".join(
                    f"{d['class']} ({d['score']:.2f})" for d in detections
                )
                self.stdout.write(
                    self.style.ERROR(f"  [FLAGGED]  {obj.image}  →  {detail}")
                )
                if delete:
                    self._delete_book_image(obj, abs_path)
            else:
                self.stdout.write(f"  [CLEAN]    {obj.image}")

        return scanned, flagged

    def _delete_book_image(self, obj, abs_path):
        """Delete the file from disk and the BookImage DB record."""
        try:
            os.remove(abs_path)
        except OSError as exc:
            self.stdout.write(
                self.style.WARNING(f"    Could not remove file: {exc}")
            )
        obj.delete()
        self.stdout.write(
            self.style.SUCCESS(f"    Deleted DB record + file.")
        )

    # ── Avatars ───────────────────────────────────────────────────────────────

    def _scan_avatars(self, delete):
        from accounts.models import Profile  # local import

        qs = Profile.objects.exclude(avatar="").exclude(avatar__isnull=True).select_related("user")
        total = qs.count()
        self.stdout.write(f"\nScanning {total} avatar(s)...")

        scanned = flagged = 0

        for profile in qs:
            if not profile.avatar:
                continue

            abs_path = os.path.join(settings.MEDIA_ROOT, str(profile.avatar))

            if not os.path.exists(abs_path):
                self.stdout.write(
                    self.style.WARNING(f"  [MISSING]  {profile.avatar}")
                )
                continue

            scanned += 1
            is_flagged, detections = check_path_nsfw(abs_path)

            if is_flagged:
                flagged += 1
                detail = "  |  ".join(
                    f"{d['class']} ({d['score']:.2f})" for d in detections
                )
                self.stdout.write(
                    self.style.ERROR(
                        f"  [FLAGGED]  {profile.avatar}"
                        f"  (user: {profile.user.username})"
                        f"  →  {detail}"
                    )
                )
                if delete:
                    self._delete_avatar(profile, abs_path)
            else:
                self.stdout.write(f"  [CLEAN]    {profile.avatar}")

        return scanned, flagged

    def _delete_avatar(self, profile, abs_path):
        """Delete the avatar file from disk and clear the avatar field."""
        try:
            os.remove(abs_path)
        except OSError as exc:
            self.stdout.write(
                self.style.WARNING(f"    Could not remove file: {exc}")
            )
        profile.avatar = None
        profile.save(update_fields=["avatar"])
        self.stdout.write(
            self.style.SUCCESS(
                f"    Cleared avatar for user '{profile.user.username}'."
            )
        )