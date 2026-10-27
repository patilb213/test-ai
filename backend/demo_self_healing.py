from playwright.sync_api import sync_playwright
from app.healing import find_element

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    try:
        page = browser.new_page()

        page.set_content("""
        <button onclick="document.getElementById('status').textContent='SUCCESS'">
            Sign in
        </button>
        <p id="status">Waiting</p>
        """)

        result = find_element(page, {
            "role": "button",
            "name": "Log in",
            "text": "Log in"
        })

        print("\n========== TEST AI SELF-HEALING ==========")
        print("Original element :", "Log in")
        print("AI similarity    :", result.get("ai_similarity"))
        print("AI suggested     :", result.get("replacement_target"))
        print("Healing decision :", result.get("resolution_status"))

        assert result["resolution_status"] == "REVIEW_REQUIRED"
        assert result["locator"] is None

        replacement = result["replacement_target"]
        assert replacement == {"role": "button", "name": "Sign in"}

        approved = input("\nApprove suggested selector? (yes/no): ")

        if approved.strip().lower() != "yes":
            print("PASS: Execution blocked without approval.")
        else:
            locator = page.get_by_role(
                replacement["role"],
                name=replacement["name"],
                exact=True
            )

            assert locator.count() == 1
            assert locator.is_visible()
            assert locator.is_enabled()

            locator.click()

            assert page.locator("#status").inner_text() == "SUCCESS"

            print("\nPASS: AI semantic similarity detected")
            print("PASS: Human approval received")
            print("PASS: Approved selector executed")
            print("PASS: Expected result verified")
            print("\nSELF-HEALING DEMONSTRATION PASSED")

    finally:
        browser.close()
