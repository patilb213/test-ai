from typing import Any

from .healing_scoring import evaluate_healing_candidate


# ============================================================
# CONFIGURATION
# ============================================================

PRIMARY_WAIT_MS = 5000
FALLBACK_WAIT_MS = 1500


# ============================================================
# LOCATOR DESCRIPTION
# ============================================================

def locator_to_string(target: dict | None) -> str:
    """
    Convert recorded target information into readable text.
    """

    if not isinstance(target, dict) or not target:
        return "unknown"

    parts = []

    for key in [
        "role",
        "name",
        "label",
        "placeholder",
        "id",
        "nameAttr",
        "text",
        "css",
        "tag",
    ]:
        value = target.get(key)

        if value:
            parts.append(f"{key}={value}")

    return ", ".join(parts) if parts else "unknown"


# ============================================================
# CSS ESCAPING
# ============================================================

def escape_attribute(value: str) -> str:
    """
    Escape values used inside CSS attribute selectors.
    """

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )


def escape_css(value: str) -> str:
    """
    Escape a CSS identifier.
    """

    value = str(value)
    result = ""

    for char in value:
        if char.isalnum() or char in ["-", "_"]:
            result += char
        else:
            result += "\\" + format(ord(char), "x") + " "

    return result


# ============================================================
# LOCATOR VALIDATION
# ============================================================

def locator_exists(locator, timeout=PRIMARY_WAIT_MS) -> bool:
    """
    Wait for an element to become visible.

    Unlike an immediate count(), this allows time for
    asynchronous page rendering.
    """

    try:
        locator.first.wait_for(
            state="visible",
            timeout=timeout,
        )
        return True

    except Exception:
        return False


def unique_visible_locator(locator, timeout=FALLBACK_WAIT_MS):
    """
    Return a locator only if exactly one element matches
    and that element becomes visible.
    """

    try:
        locator.first.wait_for(
            state="visible",
            timeout=timeout,
        )

        if locator.count() == 1:
            return locator.first

    except Exception:
        pass

    return None


# ============================================================
# PRIMARY LOCATOR
# ============================================================

def build_primary_locator(page, target: dict):
    """
    Build the original locator from recorded information.

    Priority:
    1. Role + accessible name
    2. Label
    3. ID
    4. Placeholder
    5. Name attribute
    6. CSS selector
    7. Text
    8. Tag
    """

    if not isinstance(target, dict) or not target:
        return None, "No target information"

    role = target.get("role")
    name = target.get("name")

    if role and name:
        return (
            page.get_by_role(
                str(role),
                name=str(name),
                exact=True,
            ),
            f"role={role}, name={name}",
        )

    label = target.get("label")

    if label:
        return (
            page.get_by_label(
                str(label),
                exact=True,
            ),
            f"label={label}",
        )

    element_id = target.get("id")

    if element_id:
        return (
            page.locator(
                f"#{escape_css(element_id)}"
            ),
            f"id={element_id}",
        )

    placeholder = target.get("placeholder")

    if placeholder:
        return (
            page.get_by_placeholder(
                str(placeholder),
                exact=True,
            ),
            f"placeholder={placeholder}",
        )

    name_attr = target.get("nameAttr")

    if name_attr:
        return (
            page.locator(
                f'[name="{escape_attribute(name_attr)}"]'
            ),
            f"name={name_attr}",
        )

    css = target.get("css")

    if css:
        return (
            page.locator(str(css)),
            f"css={css}",
        )

    text = target.get("text") or name

    if text:
        return (
            page.get_by_text(
                str(text),
                exact=True,
            ),
            f"text={text}",
        )

    tag = target.get("tag")

    if tag:
        return (
            page.locator(str(tag)),
            f"tag={tag}",
        )

    return None, "No usable locator"


# ============================================================
# FALLBACK LOCATOR CANDIDATES
# ============================================================

def build_fallback_candidates(page, target: dict):
    """
    Generate alternative locator strategies.

    Each candidate includes:
    (locator, description, confidence, reason)
    """

    candidates = []

    if not isinstance(target, dict):
        return candidates

    role = target.get("role")
    name = target.get("name")
    label = target.get("label")
    placeholder = target.get("placeholder")
    element_id = target.get("id")
    name_attr = target.get("nameAttr")
    css = target.get("css")
    text = target.get("text")
    tag = target.get("tag")

    # --------------------------------------------------------
    # ACCESSIBILITY ROLE
    # --------------------------------------------------------

    if role and name:
        candidates.append((
            page.get_by_role(
                str(role),
                name=str(name),
                exact=True,
            ),
            f"role={role}, name={name}",
            0.98,
            "Matched original accessibility role and name",
        ))

        candidates.append((
            page.get_by_role(
                str(role),
                name=str(name),
                exact=False,
            ),
            f"role={role}, name~={name}",
            0.92,
            "Matched accessibility role with similar name",
        ))

    # --------------------------------------------------------
    # LABEL
    # --------------------------------------------------------

    if label:
        candidates.append((
            page.get_by_label(
                str(label),
                exact=True,
            ),
            f"label={label}",
            0.96,
            "Matched form label",
        ))

        candidates.append((
            page.get_by_label(
                str(label),
                exact=False,
            ),
            f"label~={label}",
            0.88,
            "Matched similar form label",
        ))

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    if element_id:
        candidates.append((
            page.locator(
                f"#{escape_css(element_id)}"
            ),
            f"id={element_id}",
            0.95,
            "Matched element ID",
        ))

    # --------------------------------------------------------
    # PLACEHOLDER
    # --------------------------------------------------------

    if placeholder:
        candidates.append((
            page.get_by_placeholder(
                str(placeholder),
                exact=True,
            ),
            f"placeholder={placeholder}",
            0.94,
            "Matched exact placeholder",
        ))

        candidates.append((
            page.get_by_placeholder(
                str(placeholder),
                exact=False,
            ),
            f"placeholder~={placeholder}",
            0.86,
            "Matched similar placeholder",
        ))

    # --------------------------------------------------------
    # NAME ATTRIBUTE
    # --------------------------------------------------------

    if name_attr:
        candidates.append((
            page.locator(
                f'[name="{escape_attribute(name_attr)}"]'
            ),
            f"name={name_attr}",
            0.90,
            "Matched name attribute",
        ))

    # --------------------------------------------------------
    # VISIBLE TEXT
    # --------------------------------------------------------

    visible_text = text or name

    if visible_text:
        candidates.append((
            page.get_by_text(
                str(visible_text),
                exact=True,
            ),
            f"text={visible_text}",
            0.90,
            "Matched exact visible text",
        ))

        candidates.append((
            page.get_by_text(
                str(visible_text),
                exact=False,
            ),
            f"text~={visible_text}",
            0.82,
            "Matched similar visible text",
        ))

    # --------------------------------------------------------
    # CSS SELECTOR
    # --------------------------------------------------------

    if css:
        candidates.append((
            page.locator(str(css)),
            f"css={css}",
            0.80,
            "Matched recorded CSS selector",
        ))

    # --------------------------------------------------------
    # TAG + TEXT
    # --------------------------------------------------------

    if tag and visible_text:
        candidates.append((
            page.locator(str(tag)).filter(
                has_text=str(visible_text)
            ),
            f"{tag}:has-text({visible_text})",
            0.78,
            "Matched tag and visible text",
        ))

    return candidates


# ============================================================
# SELF-HEAL LOCATOR
# ============================================================

def find_element(page, target: dict) -> dict[str, Any]:
    """
    Locate a recorded element.

    First:
        Try the original recorded locator.

    Then:
        Try safe alternative locator strategies.

    Returns a result compatible with runner.py.
    """

    primary, primary_description = build_primary_locator(
        page,
        target,
    )

    # --------------------------------------------------------
    # ORIGINAL LOCATOR
    # --------------------------------------------------------

    if primary is not None:
        original_match = unique_visible_locator(
            primary,
            timeout=PRIMARY_WAIT_MS,
        )

        if original_match is not None:
            return {
                "locator": original_match,
                "healed": False,
                "original_locator": primary_description,
                "replacement_locator": None,
                "confidence": 1.0,
                "reason": "Original locator matched successfully",
            }

    # --------------------------------------------------------
    # FALLBACK SELF-HEALING
    # --------------------------------------------------------

    candidates = build_fallback_candidates(
        page,
        target,
    )

    for (
        locator,
        description,
        confidence,
        reason,
    ) in candidates:

        try:
            match = unique_visible_locator(
                locator,
                timeout=FALLBACK_WAIT_MS,
            )

            if match is not None:
                # TEST_AI_UPGRADE_1
                # Validate recorded container context.
                similarity = None
                recorded_context = str(
                    target.get("containerText") or ""
                ).strip()

                if recorded_context:
                    try:
                        live_context = match.evaluate(
                            """el => {
                                const p = el.closest(
                                    '[data-testid*="product"], article, li, [class*="product"], [class*="card"]'
                                );
                                return (
                                    p || el.parentElement || el
                                ).innerText || '';
                            }"""
                        )

                        def tokens(text):
                            import re
                            return set(
                                re.findall(
                                    r"[a-z0-9]{3,}",
                                    str(text).lower()
                                )
                            )

                        expected_tokens = tokens(
                            recorded_context
                        )
                        actual_tokens = tokens(
                            live_context
                        )

                        if expected_tokens:
                            similarity = len(
                                expected_tokens & actual_tokens
                            ) / len(expected_tokens)

                            if similarity < 0.6:
                                continue

                    except Exception:
                        continue

                # PHASE 2: Score the candidate after context validation.
                decision = evaluate_healing_candidate(
                    base_confidence=confidence,
                    context_similarity=similarity,
                    unique=True,
                )

                if decision.status == "REJECTED":
                    continue

                # PHASE 2: Approval safety gate.
                # Do not execute a candidate that requires review.
                if decision.status == "REVIEW_REQUIRED":
                    return {
                        "locator": None,
                        "healed": False,
                        "resolution_status": "REVIEW_REQUIRED",
                        "original_locator": primary_description,
                        "replacement_locator": description,
                        "confidence": decision.confidence,
                        "healing_decision": decision.status,
                        "healing_decision_reason": decision.reason,
                        "reason": (
                            "A fallback locator was found, but "
                            "human approval is required before "
                            "the test can execute this action."
                        ),
                    }

                # Avoid reporting an identical locator as healed.
                if description == primary_description:
                    return {
                        "locator": match,
                        "healed": False,
                        "original_locator": primary_description,
                        "replacement_locator": None,
                        "confidence": 1.0,
                        "reason": "Original locator matched after waiting",
                    }

                return {
                    "locator": match,
                    "healed": False,
                    "resolution_status": "FALLBACK",
                    "original_locator": primary_description,
                    "replacement_locator": description,
                    "confidence": decision.confidence,
                    "healing_decision": decision.status,
                    "healing_decision_reason": decision.reason,
                    "reason": "Existing recorded locator fallback: " + reason,
                }

        except Exception:
            continue


    # ========================================================
    # TEST_AI_SEMANTIC_HEALING_V1
    # AI-ASSISTED RECOVERY
    # ========================================================

    # Existing recorded locators have already been tried.
    # AI now examines live DOM candidates for semantic matches.
    #
    # AI suggestions are never executed automatically here.
    # They must pass further validation and human approval.

    try:
        from .ai_semantic_healing import (
            rank_semantic_candidates,
            evaluate_semantic_recovery,
        )

        original = {
            "role": target.get("role"),
            "name": target.get("name"),
            "label": target.get("label"),
            "placeholder": target.get("placeholder"),
            "text": target.get("text"),
            "tag": target.get("tag"),
            "type": target.get("type"),
        }

        selector = (
            "button, a, input:not([type='password']), "
            "select, textarea, [role='button'], "
            "[role='link'], [role='textbox']"
        )

        elements = page.locator(selector)

        live_candidates = elements.evaluate_all(
            """nodes => nodes.slice(0, 150).map((el, index) => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                const visible =
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    rect.width > 0 &&
                    rect.height > 0;

                const type = (
                    el.getAttribute('type') || ''
                ).toLowerCase();

                const sensitive =
                    type === 'password' ||
                    type === 'hidden' ||
                    type === 'file';

                const label =
                    el.labels && el.labels.length
                    ? el.labels[0].innerText
                    : '';

                return {
                    index,
                    visible: visible && !sensitive,
                    role: (
                        el.getAttribute('role') ||
                        (el.tagName.toLowerCase() === 'button'
                            ? 'button'
                            : el.tagName.toLowerCase() === 'a'
                            ? 'link'
                            : el.tagName.toLowerCase() === 'select'
                            ? 'combobox'
                            : ['input', 'textarea'].includes(
                                el.tagName.toLowerCase()
                              )
                            ? 'textbox'
                            : '')
                    ),
                    name: (
                        el.getAttribute('aria-label') ||
                        (el.innerText || '').trim()
                    ).slice(0, 120),
                    label: String(label || '').slice(0, 120),
                    placeholder: (
                        el.getAttribute('placeholder') || ''
                    ).slice(0, 120),
                    text: (
                        el.getAttribute('aria-label')
                            ? (el.innerText || '').slice(0, 120)
                            : ''
                    ),
                    tag: el.tagName.toLowerCase(),
                    type,
                };
            })"""
        )

        live_candidates = [
            item
            for item in live_candidates
            if item.get("visible")
        ]

        if live_candidates:
            ranked = rank_semantic_candidates(
                original,
                live_candidates,
                limit=5,
            )

            decision = evaluate_semantic_recovery(
                ranked,
                minimum_similarity=0.80,
                minimum_margin=0.08,
            )

            if decision["status"] == "VALIDATION_REQUIRED":
                suggested = decision["recommended_candidate"]

                suggested_index = suggested.get("index")

                if isinstance(suggested_index, int):
                    proposed_locator = elements.nth(
                        suggested_index
                    )

                    # Confirm that the proposed element
                    # still exists and is visible.
                    if (
                        proposed_locator.count() == 1
                        and proposed_locator.is_visible()
                    ):
                        # Build a reusable locator from live DOM attributes.
                        # Never persist the temporary DOM index as a selector.
                        candidate = proposed_locator.evaluate(
                            """el => ({
                                role: el.getAttribute('role') ||
                                    (el.tagName.toLowerCase() === 'button'
                                        ? 'button'
                                        : el.tagName.toLowerCase() === 'a'
                                        ? 'link' : ''),
                                name: el.getAttribute('aria-label') ||
                                    (el.innerText || '').trim().slice(0, 120),
                                id: el.id || '',
                                label: el.labels && el.labels.length
                                    ? (el.labels[0].innerText || '').trim()
                                    : '',
                                placeholder: el.getAttribute('placeholder') || '',
                                tag: el.tagName.toLowerCase()
                            })"""
                        )

                        stable_target = None
                        for candidate_target in [
                            {"role": candidate.get("role"),
                             "name": candidate.get("name")},
                            {"id": candidate.get("id")},
                            {"label": candidate.get("label")},
                            {"placeholder": candidate.get("placeholder")},
                        ]:
                            candidate_target = {
                                k: v for k, v in candidate_target.items() if v
                            }
                            if not candidate_target:
                                continue
                            stable_locator, _ = build_primary_locator(
                                page, candidate_target
                            )
                            if stable_locator is not None:
                                try:
                                    if (stable_locator.count() == 1
                                            and stable_locator.is_visible()):
                                        stable_target = candidate_target
                                        break
                                except Exception:
                                    pass

                        if stable_target is None:
                            raise ValueError("AI candidate has no unique stable locator")

                        # TEST_AI_AUTONOMOUS_HEALING_V1
                        # Autonomous recovery requires a unique stable locator,
                        # sufficient semantic evidence and a safe action target.
                        similarity = float(
                            decision.get("semantic_similarity") or 0
                        )
                        margin = float(
                            decision.get("margin") or 0
                        )

                        safe_role = stable_target.get("role") in {
                            "button", "link"
                        }

                        candidate_name = str(
                            stable_target.get("name") or ""
                        ).strip().lower()

                        dangerous_words = (
                            "delete", "remove account", "purchase",
                            "checkout", "pay now", "transfer",
                            "submit payment", "confirm order",
                        )

                        safe_name = not any(
                            word in candidate_name
                            for word in dangerous_words
                        )

                        if (
                            similarity >= 0.80
                            and margin >= 0.08
                            and safe_role
                            and safe_name
                        ):
                            stable_locator, _ = build_primary_locator(
                                page, stable_target
                            )

                            if (
                                stable_locator is not None
                                and stable_locator.count() == 1
                                and stable_locator.is_visible()
                                and stable_locator.is_enabled()
                            ):
                                return {
                                    "locator": stable_locator,
                                    "healed": True,
                                    "resolution_status": "AUTO_HEALED",
                                    "original_locator": primary_description,
                                    "replacement_locator": locator_to_string(
                                        stable_target
                                    ),
                                    "replacement_target": stable_target,
                                    "confidence": similarity,
                                    "healing_decision": "AUTO_HEALED",
                                    "healing_decision_reason": (
                                        "Unique semantic replacement passed "
                                        "automatic recovery checks."
                                    ),
                                    "reason": (
                                        "AI automatically resolved the changed "
                                        "website element."
                                    ),
                                    "ai_model": decision["model"],
                                    "ai_similarity": similarity,
                                    "ai_margin": margin,
                                }

                        return {
                            "locator": None,
                            "healed": False,
                            "resolution_status": "REVIEW_REQUIRED",
                            "original_locator": primary_description,
                            "replacement_locator": locator_to_string(stable_target),
                            "replacement_target": stable_target,
                            "confidence": decision[
                                "semantic_similarity"
                            ],
                            "healing_decision": "REVIEW_REQUIRED",
                            "healing_decision_reason": (
                                "AI semantic match found. "
                                "Human approval and stable locator "
                                "validation are required."
                            ),
                            "reason": (
                                "AI identified a possible replacement "
                                "element after recorded locators failed."
                            ),
                            "ai_model": decision["model"],
                            "ai_similarity": decision[
                                "semantic_similarity"
                            ],
                            "ai_margin": decision["margin"],
                        }

    except Exception as ai_error:
        # AI failure must not authorize an unsafe action.
        # Preserve normal locator failure behavior.
        import logging

        logging.getLogger(__name__).exception(
            "AI semantic recovery failed: %s",
            ai_error,
        )

    # --------------------------------------------------------
    # NO MATCH FOUND
    # --------------------------------------------------------

    return {
        "locator": None,
        "healed": False,
        "original_locator": primary_description,
        "replacement_locator": None,
        "confidence": 0.0,
        "reason": (
            "Recorded element could not be located "
            "using the original or alternative selectors."
        ),
    }