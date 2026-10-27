
from typing import Any


SUPPORTED_CONDITIONS = {
    "contains",
    "equals",
    "not_contains",
    "not_equals",
    "starts_with",
    "ends_with",
}


def compare_values(
    expected: Any,
    actual: Any,
    condition: str = "contains",
    *,
    case_sensitive: bool = True,
) -> dict:
    """
    Compare an expected value with a real observed value.

    Returns a structured comparison result suitable
    for storing in MongoDB and displaying in Test AI.
    """

    condition = str(condition).strip().lower()

    if condition not in SUPPORTED_CONDITIONS:
        raise ValueError(
            f"Unsupported comparison condition: {condition}"
        )

    if expected is None:
        raise ValueError(
            "Expected value cannot be empty."
        )

    if actual is None:
        raise ValueError(
            "Actual value is unavailable."
        )

    expected_text = str(expected)
    actual_text = str(actual)

    if not expected_text.strip():
        raise ValueError(
            "Expected value cannot be empty."
        )

    left = actual_text
    right = expected_text

    if not case_sensitive:
        left = left.casefold()
        right = right.casefold()

    comparisons = {
        "contains": lambda: right in left,
        "equals": lambda: left == right,
        "not_contains": lambda: right not in left,
        "not_equals": lambda: left != right,
        "starts_with": lambda: left.startswith(right),
        "ends_with": lambda: left.endswith(right),
    }

    passed = comparisons[condition]()

    if passed:
        message = (
            "Actual result satisfies the expected condition."
        )
    else:
        message = (
            f"Comparison failed: actual result does not "
            f"satisfy '{condition}' for the expected value."
        )

    return {
        "expected": expected_text,
        "actual": actual_text,
        "condition": condition,
        "case_sensitive": case_sensitive,
        "matched": passed,
        "status": "PASS" if passed else "FAIL",
        "message": message,
    }


def compare_page_text(
    expected: str,
    actual_page_text: str,
    condition: str = "contains",
) -> dict:
    """
    Compare expected text with actual visible page text.

    Preserve the actual text as evidence rather than
    returning only 'Expected text found/not found'.
    """

    result = compare_values(
        expected=expected,
        actual=actual_page_text,
        condition=condition,
    )

    result["verification_type"] = "text"

    return result


def compare_url(
    expected: str,
    actual_url: str,
    condition: str = "contains",
) -> dict:
    result = compare_values(
        expected=expected,
        actual=actual_url,
        condition=condition,
    )

    result["verification_type"] = "url"

    return result


def compare_page_title(
    expected: str,
    actual_title: str,
    condition: str = "contains",
) -> dict:
    result = compare_values(
        expected=expected,
        actual=actual_title,
        condition=condition,
    )

    result["verification_type"] = "page_title"

    return result
