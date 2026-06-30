"""
books/nsfw.py
─────────────────────────────────────────────────────────────────────────────
NSFW image screening powered by NudeNet.

Usage (in a Django form clean_* method):
    from .nsfw import check_image_nsfw
    check_image_nsfw(self.cleaned_data["image"])   # raises ValidationError if flagged

Usage (in a management command / script, with a file-system path):
    from books.nsfw import check_path_nsfw
    flagged, detections = check_path_nsfw("/media/book_images/foo.jpg")
─────────────────────────────────────────────────────────────────────────────
"""

import os
import logging
import tempfile

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ─── Detector singleton ───────────────────────────────────────────────────────
# Loaded once per worker process on first use — ~92 MB model stays in memory.
_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        try:
            from nudenet import NudeDetector
            _detector = NudeDetector()
            logger.info("NudeNet detector loaded.")
        except ImportError:
            logger.error(
                "nudenet is not installed. Run: pip install nudenet"
            )
            raise
    return _detector


# ─── Label configuration ──────────────────────────────────────────────────────
# Only block genuinely explicit content; remove COVERED variants if you want
# to be less strict (e.g. a swimwear book cover should be fine).
NSFW_LABELS = {
    "FEMALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_COVERED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
    "ANUS_COVERED",
}

# 0.0–1.0.  Lower = stricter (more false positives).  0.6 is a safe default.
NSFW_CONFIDENCE_THRESHOLD = 0.6


# ─── Public helpers ───────────────────────────────────────────────────────────

def check_image_nsfw(image_file):
    """
    Validate a Django uploaded file object for NSFW content.

    Args:
        image_file: InMemoryUploadedFile or TemporaryUploadedFile from
                    request.FILES / form.cleaned_data["image"].

    Raises:
        ValidationError: if NSFW content is detected above the threshold.
        ValidationError: if the detector cannot be loaded (missing package).
    """
    if not image_file or not hasattr(image_file, "name"):
        return  # nothing to check

    try:
        detector = _get_detector()
    except ImportError:
        raise ValidationError(
            "Image screening is temporarily unavailable. Please try again later."
        )

    suffix = os.path.splitext(image_file.name)[1] or ".jpg"

    # NudeDetector.detect() requires a file-system path, not a file object.
    # Write to a temp file, run detection, clean up immediately.
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        detections = detector.detect(tmp_path)

    except Exception as exc:
        logger.exception("NudeNet detection error for %s: %s", image_file.name, exc)
        # Do NOT block the upload on unexpected detector errors —
        # a broken detector should not bring down the whole listing form.
        return

    finally:
        # Always reset the file pointer so Django can still save the file.
        try:
            image_file.seek(0)
        except Exception:
            pass
        # Clean up temp file if it was created
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    flagged = _flagged_detections(detections)
    if flagged:
        labels = ", ".join(sorted({d["class"] for d in flagged}))
        logger.warning(
            "NSFW image blocked: file=%s labels=%s", image_file.name, labels
        )
        raise ValidationError(
            "This image was flagged as inappropriate and cannot be uploaded. "
            "Please use a suitable image."
        )


def check_path_nsfw(file_path):
    """
    Screen an image already on disk (used by the management command).

    Args:
        file_path (str): Absolute path to the image file.

    Returns:
        tuple[bool, list]: (is_flagged, list_of_flagged_detections)
    """
    try:
        detector = _get_detector()
    except ImportError:
        logger.error("nudenet not available — cannot screen %s", file_path)
        return False, []

    try:
        detections = detector.detect(file_path)
    except Exception as exc:
        logger.exception("NudeNet detection error for %s: %s", file_path, exc)
        return False, []

    flagged = _flagged_detections(detections)
    return bool(flagged), flagged


# ─── Private ──────────────────────────────────────────────────────────────────

def _flagged_detections(detections):
    """Return only the detections that exceed threshold for blocked labels."""
    return [
        d for d in (detections or [])
        if d.get("class") in NSFW_LABELS
        and d.get("score", 0) >= NSFW_CONFIDENCE_THRESHOLD
    ]