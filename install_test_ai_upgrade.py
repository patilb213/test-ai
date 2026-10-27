from pathlib import Path
from datetime import datetime
import shutil
import ast
import re

# TEST AI - SELF-HEALING UPGRADE 1

root = Path(__file__).resolve().parent
app = root / "backend" / "app"

healing = app / "healing.py"
runner = app / "runner.py"
recorder = app / "browser_recorder.py"

files = [healing, runner, recorder]

for file in files:
    if not file.is_file():
        raise SystemExit(f"Required file missing: {file}")

source = {
    file: file.read_text(encoding="utf-8")
    for file in files
}

for file, code in source.items():
    ast.parse(code, filename=str(file))

if any(
    "TEST_AI_UPGRADE_1" in code
    for code in source.values()
):
    raise SystemExit(
        "Upgrade already installed or partially installed."
    )

# ----------------------------------------
# 1. IMPROVE HEALING CLASSIFICATION
# ----------------------------------------

code = source[healing]

old = '''                    "healed": True,
                    "original_locator": primary_description,
                    "replacement_locator": description,
                    "confidence": confidence,
                    "reason": reason,'''

new = '''                    "healed": False,
                    "resolution_status": "FALLBACK",
                    "original_locator": primary_description,
                    "replacement_locator": description,
                    "confidence": None,
                    "reason": "Existing recorded locator fallback: " + reason,'''

if old not in code:
    raise SystemExit(
        "Healing fallback structure differs. No changes made."
    )

code = code.replace(old, new)

old = '''            if match is not None:
                # Avoid reporting an identical locator as healed.'''

new = '''            if match is not None:
                # TEST_AI_UPGRADE_1
                # Validate recorded container context.
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

                # Avoid reporting an identical locator as healed.'''

if old not in code:
    raise SystemExit(
        "Healing validation location differs. No changes made."
    )

code = code.replace(old, new)
source[healing] = code

# ----------------------------------------
# 2. IMPROVE ELEMENT RECORDING
# ----------------------------------------

code = source[recorder]

old = '''            css: selector(element),
            tag: tag'''

new = '''            css: selector(element),
            tag: tag,
            // TEST_AI_UPGRADE_1
            // Capture context for repeated controls.
            containerText: (() => {
                const parent = element.closest(
                    '[data-testid*="product"], article, li, [class*="product"], [class*="card"]'
                );
                return parent
                    ? trim(
                        parent.innerText || parent.textContent,
                        240
                    )
                    : "";
            })(),
            testId: attr(element, "data-testid"),
            type: attr(element, "type")'''

if old not in code:
    raise SystemExit(
        "Recorder target structure differs. No changes made."
    )

code = code.replace(old, new)
source[recorder] = code

# ----------------------------------------
# 3. INTEGRATE WITH EXISTING RUNNER
# ----------------------------------------

code = source[runner]

old = '''def healing_details_from(result):
    if not result.get("healed"):
        return None'''

new = '''def healing_details_from(result):
    # TEST_AI_UPGRADE_1
    # Recorded fallback is not genuine self-healing.
    if result.get("resolution_status") == "FALLBACK":
        return {
            "healed": False,
            "resolution_status": "FALLBACK",
            "original_locator": result.get(
                "original_locator"
            ),
            "replacement_locator": result.get(
                "replacement_locator"
            ),
            "confidence": None,
            "reason": result.get("reason"),
        }

    if not result.get("healed"):
        return None'''

if old not in code:
    raise SystemExit(
        "Runner healing adapter differs. No changes made."
    )

code = code.replace(old, new)

code = re.sub(
    r'(?m)^(\s*)result\["status"\] = "HEALED"\n'
    r'\1result\["healing"\] = details$',
    r'\1result["status"] = "HEALED" if details.get("healed") else "PASS"'
    '\n'
    r'\1result["resolution_status"] = details.get("resolution_status", "HEALED")'
    '\n'
    r'\1result["healing"] = details',
    code
)

source[runner] = code

# ----------------------------------------
# 4. VALIDATE BEFORE WRITING
# ----------------------------------------

for file, code in source.items():
    ast.parse(code, filename=str(file))

# ----------------------------------------
# 5. AUTOMATIC BACKUP
# ----------------------------------------

backup = root / "backups" / (
    "upgrade1-" +
    datetime.now().strftime("%Y%m%d-%H%M%S")
)

backup.mkdir(parents=True, exist_ok=True)

for file in files:
    shutil.copy2(file, backup / file.name)

# ----------------------------------------
# 6. INSTALL CHANGES
# ----------------------------------------

for file, code in source.items():
    file.write_text(code, encoding="utf-8")

print("Upgrade 1 installed successfully.")
print("Backup:", backup)
print("Re-record a test to capture new element context.")
print("Next: verify playback and fallback reporting.")
