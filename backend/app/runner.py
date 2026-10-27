
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from playwright.sync_api import sync_playwright

from .database import test_runs_collection
from .healing import find_element
from .comparison import (
    compare_url,
    compare_page_title,
    compare_page_text,
)


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = BACKEND_DIR / "evidence"

EVIDENCE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# BASIC HELPERS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc)


def iso_time(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return value


def safe_filename(value):
    value = str(value or "test")

    safe = "".join(
        character
        if character.isalnum() or character in "-_"
        else "_"
        for character in value
    )

    return safe[:80] or "test"


def screenshot_path(run_key, name):
    filename = (
        f"{safe_filename(run_key)}_"
        f"{safe_filename(name)}_"
        f"{uuid4().hex[:8]}.png"
    )

    return EVIDENCE_DIR / filename


def capture_screenshot(page, run_key, name):
    try:
        path = screenshot_path(run_key, name)

        page.screenshot(
            path=str(path),
            full_page=True,
            timeout=10000,
        )

        return str(path)

    except Exception as error:
        print("Unable to capture screenshot:", error)
        return None


def evidence_url(path):
    if not path:
        return None

    return "/evidence/" + Path(str(path)).name


def serialize_result(result):
    serialized = dict(result)

    for field in ["started_at", "finished_at"]:
        if serialized.get(field):
            serialized[field] = iso_time(
                serialized[field]
            )

    if serialized.get("screenshot"):
        serialized["screenshot"] = evidence_url(
            serialized["screenshot"]
        )

    return serialized


# ============================================================
# SENSITIVE FIELD CHECK
# ============================================================

SENSITIVE_TERMS = (
    "password",
    "passwd",
    "passcode",
    "secret",
    "token",
    "api_key",
    "authorization",
)


def is_sensitive_step(step):
    target = step.get("target")

    if not isinstance(target, dict):
        target = {}

    combined = " ".join(
        str(value).lower()
        for value in [
            target.get("name"),
            target.get("label"),
            target.get("id"),
            target.get("nameAttr"),
            target.get("placeholder"),
            target.get("type"),
            target.get("autocomplete"),
        ]
        if value
    )

    return any(
        term in combined
        for term in SENSITIVE_TERMS
    )


def safe_target_details(target):
    """
    Return diagnostic information without exposing
    recorded input values or sensitive field details.
    """
    if not isinstance(target, dict):
        return {}

    fields = [
        "role",
        "name",
        "text",
        "label",
        "placeholder",
        "id",
        "css",
        "tag",
    ]

    details = {}

    for field in fields:
        value = target.get(field)

        if value is not None and value != "":
            details[field] = str(value)[:200]

    combined = " ".join(
        str(value).lower()
        for value in target.values()
        if isinstance(value, (str, int, float))
    )

    if any(term in combined for term in SENSITIVE_TERMS):
        return {"target": "[Sensitive field]"}

    return details


# ============================================================
# PHASE 2: APPROVAL-REQUIRED EXCEPTION
# ============================================================

class HealingApprovalRequired(AssertionError):
    def __init__(self, healing_result):
        self.healing_result = healing_result
        super().__init__(
            healing_result.get(
                "reason",
                "Locator replacement requires approval."
            )
        )


# ============================================================
# ELEMENT RESOLUTION
# ============================================================

def resolve_element(page, target):
    """
    Resolve a recorded element through the self-healing
    engine.

    Provides meaningful diagnostics if the element
    cannot be located.
    """

    if not isinstance(target, dict) or not target:
        raise ValueError(
            "Recorded element target is missing or invalid."
        )

    # TEST_AI_ASYNC_ELEMENT_WAIT_V1
    # Wait for asynchronously rendered original elements
    # before invoking semantic self-healing.
    css = target.get("css")

    if isinstance(css, str) and css.strip():
        try:
            original_locator = page.locator(css)

            original_locator.first.wait_for(
                state="visible",
                timeout=8000,
            )

            # Never silently choose between multiple matches.
            if original_locator.count() == 1:
                if original_locator.is_enabled():
                    return original_locator, {
                        "locator": original_locator,
                        "healed": False,
                        "resolution_status": "ORIGINAL",
                        "reason": "Original selector became available.",
                    }

        except Exception:
            # The original element may genuinely have changed.
            # Continue through the existing AI healing engine.
            pass

    healing_result = find_element(
        page,
        target,
    )

    if not isinstance(healing_result, dict):
        raise ValueError(
            "Invalid response from self-healing engine."
        )

    locator = healing_result.get("locator")

    if locator is None:
        if healing_result.get("resolution_status") == "REVIEW_REQUIRED":
            raise HealingApprovalRequired(healing_result)

        reason = healing_result.get(
            "reason",
            "No matching element was found.",
        )

        details = safe_target_details(target)

        current_url = page.url

        login_hint = ""

        if current_url.rstrip("/").lower().endswith(
            ("/login", "/signin", "/sign-in")
        ):
            login_hint = (
                " Browser is on a login page. "
                "Check whether an earlier step failed "
                "to establish authentication or caused "
                "an unexpected redirect."
            )

        raise AssertionError(
            "Recorded element could not be located. "
            f"Reason: {reason}. "
            f"Recorded target: {details}. "
            f"Current URL: {current_url}."
            f"{login_hint}"
        )

    return locator, healing_result


def healing_details_from(result):
    """
    Preserve Phase 2 confidence and approval metadata.

    Recorded fallback is not genuine self-healing.
    """

    if not isinstance(result, dict):
        return None

    status = result.get("resolution_status")

    if status in ("FALLBACK", "REVIEW_REQUIRED", "AUTO_HEALED"):
        return {
            "healed": status == "AUTO_HEALED",
            "resolution_status": status,
            "original_locator": result.get("original_locator"),
            "replacement_locator": result.get("replacement_locator"),
            "confidence": result.get("confidence"),
            "healing_decision": result.get("healing_decision"),
            "healing_decision_reason": result.get(
                "healing_decision_reason"
            ),
            "reason": result.get("reason"),
            "replacement_target": result.get("replacement_target"),
            "ai_model": result.get("ai_model"),
            "ai_similarity": result.get("ai_similarity"),
            "ai_margin": result.get("ai_margin"),
        }

    if result.get("healed"):
        return {
            "healed": True,
            "resolution_status": status or "HEALED",
            "original_locator": result.get("original_locator"),
            "replacement_locator": result.get("replacement_locator"),
            "confidence": result.get("confidence"),
            "healing_decision": result.get("healing_decision"),
            "healing_decision_reason": result.get(
                "healing_decision_reason"
            ),
            "reason": result.get("reason"),
            "replacement_target": result.get("replacement_target"),
            "ai_model": result.get("ai_model"),
            "ai_similarity": result.get("ai_similarity"),
            "ai_margin": result.get("ai_margin"),
        }

    return None


# ============================================================
# RECORDED ACTION EXECUTION
# ============================================================

def execute_action(
    page,
    step,
    run_key,
    step_number,
):
    started_at = utc_now()
    started_clock = perf_counter()

    action = str(
        step.get("action", "")
    ).strip().lower()

    result = {
        "step": step_number,
        "action": action,
        "status": "PASS",
        "message": "",
        "started_at": started_at,
    }

    sensitive = is_sensitive_step(step)

    if not sensitive and step.get("value") is not None:
        result["value"] = str(step["value"])

    try:
        result["url_before"] = page.url

        target = step.get("target")
        value = step.get("value")

        # ----------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------

        if action in ["navigate", "goto", "open"]:
            url = str(
                step.get("url")
                or value
                or ""
            ).strip()

            if not url:
                raise ValueError(
                    "Navigation URL is missing."
                )

            if not url.startswith(("http://", "https://")):
                raise ValueError(
                    "Navigation requires an HTTP(S) URL."
                )

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            result["url"] = page.url
            result["message"] = "Navigation completed."

        # ----------------------------------------------------
        # CLICK
        # ----------------------------------------------------

        elif action in ["click", "tap"]:
            url_before = page.url

            locator, healing = resolve_element(
                page,
                target,
            )

            locator.click(timeout=10000)

            # Wait briefly for document navigation when
            # the click has changed the current URL.
            if page.url != url_before:
                try:
                    page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=3000,
                    )
                except Exception:
                    pass

            url_after = page.url

            result["url_before"] = url_before
            result["url_after"] = url_after

            if url_before != url_after:
                result["message"] = (
                    "Click completed. Navigation: "
                    f"{url_before} -> {url_after}"
                )
            else:
                result["message"] = "Click completed."

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # DOUBLE CLICK
        # ----------------------------------------------------

        elif action in ["double_click", "dblclick"]:
            locator, healing = resolve_element(
                page,
                target,
            )

            locator.dblclick(timeout=10000)

            result["message"] = "Double click completed."

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # INPUT / FILL
        # ----------------------------------------------------

        elif action in [
            "fill",
            "input",
            "type",
            "change",
        ]:
            locator, healing = resolve_element(
                page,
                target,
            )

            fill_value = str(
                value if value is not None else ""
            )

            if sensitive:
                import os

                fill_value = os.environ.get(
                    "TEST_AI_TEST_PASSWORD", ""
                )

                if not fill_value:
                    raise ValueError(
                        "Sensitive test input requires a "
                        "configured test credential."
                    )

            locator.fill(
                fill_value,
                timeout=10000,
            )

            result["message"] = (
                "Sensitive input completed."
                if sensitive
                else "Input completed."
            )

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # SELECT
        # ----------------------------------------------------

        elif action in ["select", "select_option"]:
            locator, healing = resolve_element(
                page,
                target,
            )

            if value is None:
                raise ValueError(
                    "Select action has no value."
                )

            locator.select_option(
                str(value),
                timeout=10000,
            )

            result["message"] = "Selection completed."

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # CHECK
        # ----------------------------------------------------

        elif action == "check":
            locator, healing = resolve_element(
                page,
                target,
            )

            locator.check(timeout=10000)

            result["message"] = "Checkbox checked."

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # UNCHECK
        # ----------------------------------------------------

        elif action == "uncheck":
            locator, healing = resolve_element(
                page,
                target,
            )

            locator.uncheck(timeout=10000)

            result["message"] = "Checkbox unchecked."

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # PRESS KEY
        # ----------------------------------------------------

        elif action in ["press", "keypress", "key"]:
            key = str(
                step.get("key")
                or value
                or ""
            ).strip()

            if not key:
                raise ValueError(
                    "Keyboard key is missing."
                )

            if isinstance(target, dict):
                locator, healing = resolve_element(
                    page,
                    target,
                )

                locator.press(
                    key,
                    timeout=10000,
                )

                details = healing_details_from(healing)

                if details:
                    result["status"] = "HEALED" if details.get("healed") else "PASS"
                    result["resolution_status"] = details.get("resolution_status", "HEALED")
                    result["healing"] = details

            else:
                page.keyboard.press(key)

            result["message"] = "Key pressed."

        # ----------------------------------------------------
        # WAIT
        # ----------------------------------------------------

        elif action == "wait":
            milliseconds = int(
                step.get("ms")
                or value
                or 1000
            )

            if milliseconds < 0 or milliseconds > 30000:
                raise ValueError(
                    "Wait must be between 0 and 30000 ms."
                )

            page.wait_for_timeout(milliseconds)

            result["message"] = "Wait completed."

        # ----------------------------------------------------
        # SCROLL
        # ----------------------------------------------------

        elif action == "scroll":
            x = float(step.get("x", 0))

            y = float(
                step.get("y")
                or step.get("deltaY")
                or 500
            )

            page.mouse.wheel(x, y)

            result["message"] = "Scroll completed."

        # ----------------------------------------------------
        # VERIFY ELEMENT
        # ----------------------------------------------------

        elif action in [
            "verify_element",
            "assert_element",
        ]:
            locator, healing = resolve_element(
                page,
                target,
            )

            locator.wait_for(
                state="visible",
                timeout=10000,
            )

            result["message"] = (
                "Element verification passed."
            )

            details = healing_details_from(healing)

            if details:
                result["status"] = "HEALED" if details.get("healed") else "PASS"
                result["resolution_status"] = details.get("resolution_status", "HEALED")
                result["healing"] = details

        # ----------------------------------------------------
        # UNKNOWN ACTION
        # ----------------------------------------------------

        else:
            raise ValueError(
                f"Unsupported test action: "
                f"{action or 'empty'}"
            )

    except Exception as error:
        result["status"] = "FAIL"
        result["error"] = str(error)

        if isinstance(error, HealingApprovalRequired):
            result["resolution_status"] = "REVIEW_REQUIRED"
            result["healing"] = healing_details_from(
                error.healing_result
            )
        result["message"] = (
            f"Step {step_number} failed."
        )

        # Save safe target information for debugging.
        if isinstance(step.get("target"), dict):
            result["target_details"] = safe_target_details(
                step["target"]
            )

        try:
            result["current_url"] = page.url
        except Exception:
            pass

        evidence = capture_screenshot(
            page,
            run_key,
            f"step_{step_number}_failed",
        )

        if evidence:
            result["screenshot"] = evidence

    finally:
        try:
            result["url_after"] = page.url
        except Exception:
            pass

        result["finished_at"] = utc_now()

        result["duration_ms"] = round(
            (perf_counter() - started_clock) * 1000,
            2,
        )

    return result


# ============================================================
# EXPECTED VS ACTUAL VERIFICATION ENGINE
# ============================================================

def execute_verification(
    page,
    verification,
    run_key,
    verification_number,
):
    verification_type = str(
        verification.get("type", "")
    ).strip().lower()

    condition = str(
        verification.get("condition", "contains")
    ).strip().lower()

    expected = verification.get("value")

    result = {
        "type": verification_type,
        "condition": condition,
        "status": "PASS",
    }

    if expected is not None:
        result["expected"] = str(expected)

    try:
        # ----------------------------------------------------
        # URL COMPARISON
        # ----------------------------------------------------

        if verification_type == "url":
            comparison = compare_url(
                expected=expected,
                actual_url=page.url,
                condition=condition,
            )

            result.update(comparison)

            if not comparison["matched"]:
                raise AssertionError(
                    comparison["message"]
                )

        # ----------------------------------------------------
        # PAGE TITLE COMPARISON
        # ----------------------------------------------------

        elif verification_type == "page_title":
            comparison = compare_page_title(
                expected=expected,
                actual_title=page.title(),
                condition=condition,
            )

            result.update(comparison)

            if not comparison["matched"]:
                raise AssertionError(
                    comparison["message"]
                )

        # ----------------------------------------------------
        # PAGE TEXT COMPARISON
        # ----------------------------------------------------

        elif verification_type == "text":
            actual_text = page.locator(
                "body"
            ).inner_text(timeout=10000)

            comparison = compare_page_text(
                expected=expected,
                actual_page_text=actual_text,
                condition=condition,
            )

            result.update(comparison)

            if not comparison["matched"]:
                raise AssertionError(
                    comparison["message"]
                )

        # ----------------------------------------------------
        # ELEMENT EXISTS
        # ----------------------------------------------------

        elif verification_type == "element":
            target = verification.get("target")

            if not isinstance(target, dict):
                target = {}

            target = dict(target)

            expected_text = str(
                verification.get("value") or ""
            ).strip()

            # Older UI versions store CSS selectors as a name.
            if not expected_text:
                expected_text = str(
                    target.get("name") or ""
                ).strip()

            def looks_like_css(value):
                return (
                    value.startswith(("#", ".", "["))
                    or "[" in value
                    or ">" in value
                    or value.startswith((
                        "button.", "button#",
                        "input.", "input#",
                        "a.", "a#",
                    ))
                )

            if expected_text and looks_like_css(expected_text):
                # Treat the provided value as CSS, not an
                # accessible name.
                locator = page.locator(expected_text)

                locator.first.wait_for(
                    state="visible",
                    timeout=10000,
                )

                if locator.count() != 1:
                    raise AssertionError(
                        "Expected CSS selector must match "
                        "exactly one visible element."
                    )

                result["expected"] = expected_text
                result["actual"] = (
                    "Visible element matched CSS selector"
                )
                result["matched"] = True
                result["message"] = (
                    "Element Exists verification passed."
                )

            else:
                if expected_text and not target:
                    target = {"name": expected_text}

                if not target:
                    raise ValueError(
                        "Element verification has no target."
                    )

                locator, healing = resolve_element(
                    page,
                    target,
                )

                locator.wait_for(
                    state="visible",
                    timeout=10000,
                )

                result["expected"] = "Element visible"
                result["actual"] = "Element visible"
                result["matched"] = True
                result["message"] = (
                    "Element verification passed."
                )

                details = healing_details_from(healing)

                if details:
                    result["healing"] = details
                    result["resolution_status"] = (
                        details.get("resolution_status")
                    )

        # ----------------------------------------------------
        # UNKNOWN VERIFICATION
        # ----------------------------------------------------

        else:
            raise ValueError(
                "Unsupported verification type: "
                f"{verification_type}"
            )

    except Exception as error:
        result["status"] = "FAIL"
        result["matched"] = False
        result["error"] = str(error)

        if isinstance(error, HealingApprovalRequired):
            result["resolution_status"] = "REVIEW_REQUIRED"
            result["healing"] = healing_details_from(
                error.healing_result
            )

        if not result.get("message"):
            result["message"] = (
                "Expected vs actual comparison failed."
            )

        evidence = capture_screenshot(
            page,
            run_key,
            f"verification_{verification_number}_failed",
        )

        if evidence:
            result["screenshot"] = evidence

    return result


# ============================================================
# OVERALL RUN STATUS
# ============================================================

def calculate_run_status(
    step_results,
    verification_results,
):
    all_results = (
        list(step_results)
        + list(verification_results)
    )

    if not all_results:
        return "FAIL"

    if any(
        result.get("status") == "FAIL"
        for result in all_results
    ):
        return "FAIL"

    if any(
        result.get("status") == "HEALED"
        for result in all_results
    ):
        return "HEALED"

    return "PASS"


# ============================================================
# RUN COMPLETE TEST CASE
# ============================================================

def run_test(test_case):
    started_at = utc_now()
    started_clock = perf_counter()

    test_case_id = str(test_case["_id"])

    test_name = test_case.get(
        "name",
        "Unnamed Test",
    )

    target_url = test_case.get(
        "target_url",
        "",
    )

    steps = test_case.get("steps", [])
    verifications = test_case.get(
        "verifications",
        [],
    )

    run_key = (
        f"{test_case_id}_{uuid4().hex[:8]}"
    )

    step_results = []
    verification_results = []

    top_level_error = None
    final_screenshot = None

    # --------------------------------------------------------
    # VALIDATE TEST CONTENT
    # --------------------------------------------------------

    if not isinstance(steps, list):
        top_level_error = (
            "Recorded steps must be a list."
        )

    elif not isinstance(verifications, list):
        top_level_error = (
            "Expected results must be a list."
        )

    elif not steps:
        top_level_error = (
            "Test case has no recorded steps."
        )

    elif not verifications:
        top_level_error = (
            "Test case has no expected results."
        )

    # --------------------------------------------------------
    # START PLAYWRIGHT
    # --------------------------------------------------------

    if top_level_error is None:
        try:
            with sync_playwright() as playwright:
                browser = None
                context = None
                page = None

                try:
                    browser = playwright.chromium.launch(
                        headless=True,
                    )

                    context = browser.new_context(
                        viewport={
                            "width": 1440,
                            "height": 900,
                        },
                        ignore_https_errors=False,
                    )

                    page = context.new_page()
                    page.set_default_timeout(10000)

                    # ----------------------------------------
                    # OPEN TARGET
                    # ----------------------------------------

                    if target_url:
                        first_action = str(
                            steps[0].get(
                                "action",
                                "",
                            )
                        ).strip().lower()

                        if first_action not in [
                            "navigate",
                            "goto",
                            "open",
                        ]:
                            page.goto(
                                target_url,
                                wait_until="domcontentloaded",
                                timeout=30000,
                            )

                    # ----------------------------------------
                    # EXECUTE RECORDED STEPS
                    # ----------------------------------------

                    workflow_failed = False

                    for index, step in enumerate(
                        steps,
                        start=1,
                    ):
                        step_result = execute_action(
                            page,
                            step,
                            run_key,
                            index,
                        )

                        step_results.append(
                            step_result
                        )

                        if (
                            step_result.get("status")
                            == "FAIL"
                        ):
                            workflow_failed = True
                            break

                    # ----------------------------------------
                    # EXECUTE EXPECTED COMPARISONS
                    # ----------------------------------------

                    if not workflow_failed:
                        for index, verification in enumerate(
                            verifications,
                            start=1,
                        ):
                            verification_result = (
                                execute_verification(
                                    page,
                                    verification,
                                    run_key,
                                    index,
                                )
                            )

                            verification_results.append(
                                verification_result
                            )

                    # ----------------------------------------
                    # FINAL SCREENSHOT
                    # ----------------------------------------

                    final_screenshot = capture_screenshot(
                        page,
                        run_key,
                        "final",
                    )

                finally:
                    if context is not None:
                        try:
                            context.close()
                        except Exception:
                            pass

                    if browser is not None:
                        try:
                            browser.close()
                        except Exception:
                            pass

        except Exception as error:
            top_level_error = str(error)

    # ========================================================
    # CALCULATE STATUS
    # ========================================================

    if top_level_error:
        overall_status = "FAIL"
    else:
        overall_status = calculate_run_status(
            step_results,
            verification_results,
        )

    # ========================================================
    # HEALING INFORMATION
    # ========================================================

    healing_details = []

    for step_result in step_results:
        healing = step_result.get("healing")

        if (
            isinstance(healing, dict)
            and healing.get("healed")
        ):
            healing_details.append({
                "step": step_result.get("step"),
                "action": step_result.get("action"),
                **healing,
            })

    for index, verification_result in enumerate(
        verification_results,
        start=1,
    ):
        healing = verification_result.get(
            "healing"
        )

        if (
            isinstance(healing, dict)
            and healing.get("healed")
        ):
            healing_details.append({
                "verification": index,
                "type": verification_result.get(
                    "type"
                ),
                **healing,
            })

    # ========================================================
    # PHASE 2: HEALING HISTORY
    # ========================================================

    healing_history = []

    for step_result in step_results:
        healing = step_result.get("healing")

        if isinstance(healing, dict):
            healing_history.append({
                "source": "step",
                "step": step_result.get("step"),
                "action": step_result.get("action"),
                "execution_status": step_result.get("status"),
                **healing,
            })

    for index, verification_result in enumerate(
        verification_results,
        start=1,
    ):
        healing = verification_result.get("healing")

        if isinstance(healing, dict):
            healing_history.append({
                "source": "verification",
                "verification": index,
                "type": verification_result.get("type"),
                "execution_status": verification_result.get("status"),
                **healing,
            })

    approval_required_count = sum(
        1
        for event in healing_history
        if event.get("resolution_status") == "REVIEW_REQUIRED"
    )

    # ========================================================
    # COMPARISON SUMMARY
    # ========================================================

    comparison_passed = sum(
        1
        for result in verification_results
        if result.get("status") in [
            "PASS",
            "HEALED",
        ]
    )

    comparison_failed = sum(
        1
        for result in verification_results
        if result.get("status") == "FAIL"
    )

    comparison_skipped = max(
        0,
        len(verifications) - len(verification_results),
    )

    if (
        comparison_skipped > 0
        and any(
            step.get("status") == "FAIL"
            for step in step_results
        )
    ):
        comparison_message = (
            "Expected-result checks were skipped "
            "because a recorded action failed."
        )

    elif comparison_skipped > 0:
        comparison_message = (
            "Some expected-result checks were not executed."
        )

    else:
        comparison_message = (
            "Expected-result execution completed."
        )

    comparison_summary = {
        "total": len(verifications),
        "executed": len(verification_results),
        "passed": comparison_passed,
        "failed": comparison_failed,
        "skipped": comparison_skipped,
        "message": comparison_message,
    }

    # ========================================================
    # EXECUTION TIMING
    # ========================================================

    finished_at = utc_now()

    duration_ms = round(
        (perf_counter() - started_clock) * 1000,
        2,
    )

    # ========================================================
    # MESSAGE
    # ========================================================

    if overall_status == "PASS":
        message = (
            "Test completed successfully. "
            "All expected results matched."
        )

    elif overall_status == "HEALED":
        message = (
            "Test completed successfully "
            "with automatic self-healing."
        )

    else:
        message = (
            "Test execution failed or one or more "
            "expected results did not match."
        )

    # ========================================================
    # DATABASE DOCUMENT
    # ========================================================

    run_document = {
        "test_case_id": test_case_id,
        "test_name": test_name,
        "target_url": target_url,
        "status": overall_status,
        "message": message,
        "steps": step_results,
        "verifications": verification_results,
        "comparison_summary": comparison_summary,
        "healed": len(healing_details) > 0,
        "healing_count": len(healing_details),
        "healing_details": healing_details,
        "healing_history": healing_history,
        "approval_required_count": approval_required_count,
        "screenshot": final_screenshot,
        "error": top_level_error,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "created_at": finished_at,
    }

    # ========================================================
    # SAVE RUN TO MONGODB
    # ========================================================

    inserted = test_runs_collection.insert_one(
        run_document
    )

    run_id = str(inserted.inserted_id)

    # ========================================================
    # API RESPONSE
    # ========================================================

    return {
        "id": run_id,
        "test_run_id": run_id,
        "test_case_id": test_case_id,
        "test_name": test_name,
        "target_url": target_url,
        "status": overall_status,
        "message": message,
        "steps": [
            serialize_result(result)
            for result in step_results
        ],
        "verifications": [
            serialize_result(result)
            for result in verification_results
        ],
        "comparison_summary": comparison_summary,
        "healed": len(healing_details) > 0,
        "healing_count": len(healing_details),
        "healing_details": healing_details,
        "healing_history": healing_history,
        "approval_required_count": approval_required_count,
        "screenshot": evidence_url(
            final_screenshot
        ),
        "error": top_level_error,
        "started_at": iso_time(started_at),
        "finished_at": iso_time(finished_at),
        "duration_ms": duration_ms,
    }
