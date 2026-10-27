
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from .visual_comparison import compare_screenshots


BACKEND_DIR = Path(__file__).resolve().parent.parent

EVIDENCE_DIR = BACKEND_DIR / "evidence"
BASELINE_DIR = EVIDENCE_DIR / "baselines"
DIFFERENCE_DIR = EVIDENCE_DIR / "differences"

BASELINE_DIR.mkdir(parents=True, exist_ok=True)
DIFFERENCE_DIR.mkdir(parents=True, exist_ok=True)


def safe_test_id(test_case_id):
    value = str(test_case_id)

    if not value or not all(
        char.isalnum() or char in "-_"
        for char in value
    ):
        raise ValueError("Invalid test case ID.")

    return value


def baseline_path(test_case_id):
    test_id = safe_test_id(test_case_id)
    return BASELINE_DIR / f"{test_id}.png"


def get_baseline(test_case_id):
    path = baseline_path(test_case_id)

    if not path.is_file():
        return None

    return path


def approve_baseline(test_case_id, screenshot_path):
    """
    Explicitly approve a screenshot as the baseline.

    This function must only be called from an
    authorized baseline approval workflow.
    """
    source = Path(screenshot_path).resolve()
    evidence_root = EVIDENCE_DIR.resolve()

    if (
        not source.is_file()
        or source.suffix.lower() != ".png"
        or not source.is_relative_to(evidence_root)
    ):
        raise ValueError("Invalid screenshot source.")

    destination = baseline_path(test_case_id)

    if source == destination.resolve():
        raise ValueError(
            "Cannot approve a baseline from itself."
        )

    temporary = destination.with_name(
        f"{destination.stem}_{uuid4().hex}.tmp"
    )

    try:
        copy2(source, temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)

    return {
        "status": "APPROVED",
        "test_case_id": str(test_case_id),
        "baseline": str(destination),
        "message": "Baseline screenshot approved.",
    }


def run_visual_comparison(
    test_case_id,
    actual_screenshot,
    run_key,
    tolerance_percent=0.5,
):
    """
    Compare the current screenshot with the
    previously approved baseline.

    Never creates or replaces a baseline.
    """
    baseline = get_baseline(test_case_id)

    if baseline is None:
        return {
            "status": "NOT_CONFIGURED",
            "matched": None,
            "baseline": None,
            "actual": actual_screenshot,
            "difference": None,
            "difference_percent": None,
            "tolerance_percent": tolerance_percent,
            "message": (
                "No approved baseline screenshot exists."
            ),
        }

    if not actual_screenshot:
        return {
            "status": "FAIL",
            "matched": False,
            "baseline": str(baseline),
            "actual": None,
            "difference": None,
            "difference_percent": None,
            "tolerance_percent": tolerance_percent,
            "message": "Actual screenshot is missing.",
        }

    difference_path = (
        DIFFERENCE_DIR
        / f"{safe_test_id(test_case_id)}_{uuid4().hex}.png"
    )

    try:
        result = compare_screenshots(
            baseline_path=baseline,
            actual_path=actual_screenshot,
            difference_path=difference_path,
            tolerance_percent=tolerance_percent,
        )

        return {
            **result,
            "baseline": str(baseline),
            "actual": str(actual_screenshot),
            "difference": result.get("difference_path"),
        }

    except Exception as error:
        return {
            "status": "FAIL",
            "matched": False,
            "baseline": str(baseline),
            "actual": str(actual_screenshot),
            "difference": None,
            "difference_percent": None,
            "tolerance_percent": tolerance_percent,
            "message": f"Visual comparison error: {error}",
        }
