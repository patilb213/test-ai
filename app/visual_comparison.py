
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance


def compare_screenshots(
    baseline_path,
    actual_path,
    difference_path,
    tolerance_percent=0.5,
):
    """
    Compare an approved baseline against an actual screenshot.

    The images must have identical dimensions.
    A difference image is generated for visual inspection.
    """

    baseline_path = Path(baseline_path)
    actual_path = Path(actual_path)
    difference_path = Path(difference_path)

    tolerance_percent = float(tolerance_percent)

    if not 0 <= tolerance_percent <= 100:
        raise ValueError(
            "Tolerance must be between 0 and 100."
        )

    if not baseline_path.is_file():
        raise FileNotFoundError(
            "Baseline screenshot was not found."
        )

    if not actual_path.is_file():
        raise FileNotFoundError(
            "Actual screenshot was not found."
        )

    difference_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with Image.open(baseline_path) as baseline_image:
        baseline = baseline_image.convert("RGB")

    with Image.open(actual_path) as actual_image:
        actual = actual_image.convert("RGB")

    if baseline.size != actual.size:
        return {
            "status": "FAIL",
            "matched": False,
            "difference_percent": None,
            "tolerance_percent": tolerance_percent,
            "baseline_dimensions": list(baseline.size),
            "actual_dimensions": list(actual.size),
            "difference_path": None,
            "message": (
                "Screenshot dimensions differ. "
                "A like-for-like comparison is not possible."
            ),
        }

    difference = ImageChops.difference(
        baseline,
        actual,
    )

    width, height = baseline.size
    total_pixels = width * height

    if total_pixels == 0:
        raise ValueError("Screenshot has no pixels.")

    # Count pixels with at least one changed RGB channel.
    changed_mask = difference.convert("L").point(
        lambda value: 255 if value > 0 else 0
    )

    histogram = changed_mask.histogram()
    changed_pixels = total_pixels - histogram[0]

    difference_percent = round(
        (changed_pixels / total_pixels) * 100,
        4,
    )

    # Brighten the changed areas for easier inspection.
    enhanced_difference = ImageEnhance.Contrast(
        difference
    ).enhance(3.0)

    enhanced_difference.save(difference_path)

    matched = difference_percent <= tolerance_percent

    return {
        "status": "PASS" if matched else "FAIL",
        "matched": matched,
        "difference_percent": difference_percent,
        "tolerance_percent": tolerance_percent,
        "changed_pixels": changed_pixels,
        "total_pixels": total_pixels,
        "baseline_dimensions": list(baseline.size),
        "actual_dimensions": list(actual.size),
        "difference_path": str(difference_path),
        "message": (
            "Visual comparison passed."
            if matched
            else "Visual difference exceeded the allowed tolerance."
        ),
    }
