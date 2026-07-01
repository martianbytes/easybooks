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
from typing import Any, Optional

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ─── Detector singleton ───────────────────────────────────────────────────────
# Loaded once per worker process on first use — ~92 MB model stays in memory.

class NSFWDetector:
    _instance: Optional["NSFWDetector"] = None
    detector: Any = None  # declare attribute so type checkers know it exists

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NSFWDetector, cls).__new__(cls)
            try:
                from nudenet import NudeDetector
                cls._instance.detector = NudeDetector()
                logger.info("NudeNet detector loaded.")
            except ImportError:
                logger.error("nudenet is not installed. Run: pip install nudenet")
                cls._instance.detector = None
                raise
        return cls._instance

    def detect_path(self, path):
        if self.detector is None:
            raise RuntimeError("NudeNet detector not initialized")
        return self.detector.detect(path)


# ─── Label configuration ──────────────────────────────────────────────────────
NSFW_LABELS = {
    "FEMALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_COVERED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
    "ANUS_COVERED",
    # temporarily adding these two below
    "MALE_BREAST_EXPOSED",
    "BELLY_EXPOSED"
}

NSFW_CONFIDENCE_THRESHOLD = 0.6


# ─── Public helpers ───────────────────────────────────────────────────────────

def check_image_nsfw(image_file):
    """
    Validate a Django uploaded file object for NSFW content.

    Raises ValidationError if NSFW content is detected or if screening is unavailable.
    """
    if not image_file or not hasattr(image_file, "name"):
        return  # nothing to check

    # Ensure detector available
    try:
        detector = NSFWDetector()
    except ImportError:
        raise ValidationError(
            "Image screening is temporarily unavailable. Please try again later."
        )

    suffix = os.path.splitext(image_file.name)[1] or ".jpg"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        detections = detector.detect_path(tmp_path)

    except Exception as exc:
        logger.exception("NudeNet detection error for %s: %s", getattr(image_file, "name", "<unknown>"), exc)
        # Do NOT block the upload on unexpected detector errors
        return

    finally:
        try:
            image_file.seek(0)
        except Exception:
            pass
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    flagged = _flagged_detections(detections)
    if flagged:
        labels = ", ".join(sorted({d.get("class") for d in flagged}))
        logger.warning("NSFW image blocked: file=%s labels=%s", image_file.name, labels)
        raise ValidationError(
            "This image was flagged as inappropriate and cannot be uploaded. "
            "Please use a suitable image."
        )


def check_path_nsfw(file_path):
    """
    Screen an image already on disk.

    Returns (is_flagged, list_of_flagged_detections)
    """
    try:
        detector = NSFWDetector()
    except ImportError:
        logger.error("nudenet not available — cannot screen %s", file_path)
        return False, []

    try:
        detections = detector.detect_path(file_path)
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