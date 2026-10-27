from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Callable

from playwright.sync_api import sync_playwright


# ============================================================
# ACTIVE BROWSER RECORDERS
# ============================================================

_active_recorders: dict[str, "BrowserRecorder"] = {}
_registry_lock = threading.Lock()


# ============================================================
# JAVASCRIPT RECORDER
# ============================================================

RECORDER_SCRIPT = r"""
(() => {

    if (window.__TEST_AI_RECORDER_INSTALLED__) {
        return;
    }

    window.__TEST_AI_RECORDER_INSTALLED__ = true;

    // ========================================================
    // HELPERS
    // ========================================================

    const trim = (value, length = 140) => {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/\s+/g, " ")
            .trim()
            .slice(0, length);
    };

    const attr = (element, name) => {
        return trim(element.getAttribute(name));
    };

    const quote = value => {
        return String(value)
            .replace(/\\/g, "\\\\")
            .replace(/"/g, '\\"');
    };

    const unique = selector => {
        try {
            return document.querySelectorAll(selector).length === 1;
        } catch (_) {
            return false;
        }
    };


    // ========================================================
    // BUILD CSS SELECTOR
    // ========================================================

    function selector(element) {

        if (element.id && window.CSS && CSS.escape) {
            const result = "#" + CSS.escape(element.id);

            if (unique(result)) {
                return result;
            }
        }

        for (const key of [
            "data-testid",
            "data-test",
            "data-cy",
            "name"
        ]) {

            const value = attr(element, key);

            if (!value) {
                continue;
            }

            const result =
                `${element.tagName.toLowerCase()}[${key}="${quote(value)}"]`;

            if (unique(result)) {
                return result;
            }
        }

        const parts = [];

        for (
            let current = element;
            current && current.nodeType === 1;
            current = current.parentElement
        ) {

            let part = current.tagName.toLowerCase();

            const parent = current.parentElement;

            if (parent) {

                const siblings = Array.from(parent.children)
                    .filter(
                        child => child.tagName === current.tagName
                    );

                if (siblings.length > 1) {
                    const index = siblings.indexOf(current) + 1;
                    part += `:nth-of-type(${index})`;
                }
            }

            parts.unshift(part);

            const result = parts.join(" > ");

            if (unique(result)) {
                return result;
            }

            if (parts.length >= 9) {
                break;
            }
        }

        return parts.join(" > ");
    }


    // ========================================================
    // GET ELEMENT LABEL
    // ========================================================

    function label(element) {

        if (element.labels && element.labels.length) {
            return trim(
                Array.from(element.labels)
                    .map(item => item.innerText)
                    .join(" ")
            );
        }

        const labelledBy = attr(
            element,
            "aria-labelledby"
        );

        if (labelledBy) {

            const result = labelledBy
                .split(/\s+/)
                .map(id => {
                    const node = document.getElementById(id);
                    return node ? node.innerText : "";
                })
                .join(" ");

            if (trim(result)) {
                return trim(result);
            }
        }

        return (
            attr(element, "aria-label") ||
            trim(element.closest("label")?.innerText) ||
            ""
        );
    }


    // ========================================================
    // GET ELEMENT ROLE
    // ========================================================

    function role(element) {

        const explicitRole = attr(element, "role");

        if (explicitRole) {
            return explicitRole;
        }

        const tag = element.tagName.toLowerCase();

        if (tag === "button") {
            return "button";
        }

        if (tag === "a") {
            return "link";
        }

        if (tag === "select") {
            return "combobox";
        }

        if (tag === "textarea") {
            return "textbox";
        }

        if (tag === "input") {

            const type = (
                attr(element, "type") || "text"
            ).toLowerCase();

            if (type === "checkbox" || type === "radio") {
                return type;
            }

            if (["button", "submit", "reset"].includes(type)) {
                return "button";
            }

            return "textbox";
        }

        return "";
    }


    // ========================================================
    // BUILD ELEMENT TARGET
    // ========================================================

    function target(element) {

        const tag = element.tagName.toLowerCase();

        const text = [
            "input",
            "select",
            "textarea"
        ].includes(tag)
            ? ""
            : trim(element.innerText || element.textContent);

        const elementLabel = label(element);

        const name =
            attr(element, "aria-label") ||
            elementLabel ||
            attr(element, "alt") ||
            attr(element, "title") ||
            text ||
            (
                tag === "input" &&
                ["button", "submit"].includes(
                    attr(element, "type")
                )
                    ? attr(element, "value")
                    : ""
            );

        const result = {
            role: role(element),
            name: name,
            label: elementLabel,
            placeholder: attr(element, "placeholder"),
            id: trim(element.id),
            nameAttr: attr(element, "name"),
            text: text,
            css: selector(element),
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
            type: attr(element, "type")
        };

        return Object.fromEntries(
            Object.entries(result).filter(
                ([key, value]) => value !== "" && value != null
            )
        );
    }


    // ========================================================
    // SENSITIVE INPUT DETECTION
    // ========================================================

    function sensitive(element) {

        const information = [
            attr(element, "type"),
            attr(element, "id"),
            attr(element, "name"),
            attr(element, "placeholder"),
            attr(element, "aria-label"),
            attr(element, "autocomplete")
        ].join(" ").toLowerCase();

        return /password|passwd|passcode|secret|token|otp|one.time|credit.card|card.number|cvv|cvc|security.code|ssn/
            .test(information);
    }


    // ========================================================
    // SEND EVENT TO PYTHON
    // ========================================================

    function send(data) {

        if (
            typeof window.__testAiRecordEvent !== "function"
        ) {
            return;
        }

        try {

            const promise = window.__testAiRecordEvent({
                ...data,
                timestamp: new Date().toISOString()
            });

            if (
                promise &&
                typeof promise.catch === "function"
            ) {
                promise.catch(() => {});
            }

        } catch (_) {}
    }


    // ========================================================
    // RECORD CLICK ACTIONS
    // ========================================================

    const clickable = [
        "button",
        "a",
        "input[type=button]",
        "input[type=submit]",
        "input[type=reset]",
        "input[type=checkbox]",
        "input[type=radio]",
        "[role=button]",
        "[role=link]",
        "[role=checkbox]",
        "[role=radio]"
    ].join(",");

    document.addEventListener(
        "click",
        event => {

            const element =
                event.target instanceof Element
                    ? event.target.closest(clickable)
                    : null;

            if (!element) {
                return;
            }

            // Record pending text before the button click.
            for (const field of Array.from(pending.keys())) {
                flush(field);
            }

            send({
                action: "click",
                target: target(element)
            });
        },
        true
    );


    // ========================================================
    // RECORD INPUT ACTIONS
    // ========================================================

    const pending = new Map();
    const lastSentValues = new WeakMap();

    function flush(element) {

        if (!pending.has(element)) {
            return;
        }

        clearTimeout(pending.get(element));
        pending.delete(element);

        if (!element || !element.isConnected) {
            return;
        }

        const isSensitive = sensitive(element);

        const value = isSensitive
            ? ""
            : String(element.value ?? "");

        const previous = lastSentValues.get(element);

        // Suppress repeated events for unchanged values.
        // Sensitive values remain redacted and are never
        // sent through the recorder bridge.
        if (previous === value) {
            return;
        }

        lastSentValues.set(element, value);

        send({
            action: "input",
            target: target(element),
            value: value
        });
    }


    document.addEventListener(
        "input",
        event => {

            const element = event.target;

            if (!(element instanceof Element)) {
                return;
            }

            if (!element.matches(
                "input:not([type=checkbox]):not([type=radio]):not([type=file]),textarea"
            )) {
                return;
            }

            if (pending.has(element)) {
                clearTimeout(pending.get(element));
            }

            pending.set(
                element,
                setTimeout(() => flush(element), 450)
            );
        },
        true
    );


    // ========================================================
    // RECORD CHANGE AND SELECT ACTIONS
    // ========================================================

    document.addEventListener(
        "change",
        event => {

            const element = event.target;

            if (!(element instanceof Element)) {
                return;
            }

            if (element.matches("select")) {

                send({
                    action: "select",
                    target: target(element),
                    value: String(element.value ?? "")
                });

            } else if (element.matches(
                "input:not([type=checkbox]):not([type=radio]):not([type=file]),textarea"
            )) {

                flush(element);
            }
        },
        true
    );


    // ========================================================
    // SAVE FINAL INPUT ON FOCUS CHANGE
    // ========================================================

    document.addEventListener(
        "focusout",
        event => {

            const element = event.target;

            if (
                element instanceof Element &&
                pending.has(element)
            ) {
                flush(element);
            }
        },
        true
    );

})();
"""


# ============================================================
# BROWSER RECORDER CLASS
# ============================================================

class BrowserRecorder:

    def __init__(
        self,
        session_id: str,
        target_url: str,
        event_callback: Callable[[dict[str, Any]], None]
    ):

        self.session_id = session_id
        self.target_url = target_url
        self.event_callback = event_callback

        self.stop_event = threading.Event()
        self.ready_event = threading.Event()

        self.thread: threading.Thread | None = None
        self.error: str | None = None

        self.pages: list[Any] = []
        self.last_urls: dict[int, str] = {}


    # ========================================================
    # SAVE RECORDED EVENT
    # ========================================================

    def _emit(self, event: dict[str, Any]):

        action = event.get("action")

        if action not in {
            "navigate",
            "click",
            "input",
            "select",
            "wait"
        }:
            return

        if action == "navigate":

            url = str(event.get("url") or "")

            if not url.startswith(
                ("http://", "https://")
            ):
                return

        if action in {
            "click",
            "input",
            "select"
        }:

            if not isinstance(event.get("target"), dict):
                return

        try:

            self.event_callback(event)

            target_data = event.get("target") or {}

            detail = (
                event.get("url")
                or target_data.get("name")
                or target_data.get("css")
                or "(unnamed element)"
            )

            print(
                f"[RECORDER] {action.upper()} -> {detail}",
                flush=True
            )

        except Exception as error:

            print(
                f"[RECORDER ERROR] {error}",
                flush=True
            )


    # ========================================================
    # RECEIVE JAVASCRIPT EVENT
    # ========================================================

    def _on_js_event(self, event: Any):

        if not isinstance(event, dict):
            return

        self._emit(event)


    # ========================================================
    # RECORD NAVIGATION
    # ========================================================

    def _navigation(self, page: Any, url: str):

        if not url:
            return

        if not url.startswith(
            ("http://", "https://")
        ):
            return

        key = id(page)

        if self.last_urls.get(key) == url:
            return

        self.last_urls[key] = url

        self._emit({
            "action": "navigate",
            "url": url,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat()
        })


    # ========================================================
    # REGISTER NEW BROWSER PAGE
    # ========================================================

    def _register_page(self, page: Any):

        if page in self.pages:
            return

        self.pages.append(page)

        page.on(
            "framenavigated",
            lambda frame: self._navigation(
                page,
                frame.url
            ) if frame == page.main_frame else None
        )

        page.on(
            "close",
            lambda: self.pages.remove(page)
            if page in self.pages
            else None
        )


    # ========================================================
    # START PLAYWRIGHT BROWSER
    # ========================================================

    def _run(self):

        try:

            with sync_playwright() as playwright:

                browser = playwright.chromium.launch(
                    headless=False
                )

                try:

                    context = browser.new_context(
                        viewport={
                            "width": 1440,
                            "height": 900
                        }
                    )

                    try:

                        # Register browser-to-Python event bridge.
                        context.expose_function(
                            "__testAiRecordEvent",
                            self._on_js_event
                        )

                        # Install recorder before page scripts.
                        context.add_init_script(
                            script=RECORDER_SCRIPT
                        )

                        context.on(
                            "page",
                            self._register_page
                        )

                        page = context.new_page()

                        self._register_page(page)

                        page.goto(
                            self.target_url,
                            wait_until="domcontentloaded",
                            timeout=30000
                        )

                        self.ready_event.set()

                        # IMPORTANT:
                        # Keep Playwright's event loop active.
                        # This allows click/input/select callbacks
                        # to be received after navigation.
                        while not self.stop_event.is_set():

                            page.wait_for_timeout(100)

                    finally:

                        context.close()

                finally:

                    browser.close()

        except Exception as error:

            self.error = str(error)

            print(
                f"[RECORDER ERROR] {error}",
                flush=True
            )

        finally:

            self.ready_event.set()


    # ========================================================
    # START RECORDER THREAD
    # ========================================================

    def start(self):

        self.thread = threading.Thread(
            target=self._run,
            name=f"test-ai-recorder-{self.session_id[:8]}",
            daemon=True
        )

        self.thread.start()

        if not self.ready_event.wait(timeout=40):

            self.stop_event.set()

            raise RuntimeError(
                "Recorder browser did not start within 40 seconds."
            )

        if self.error:

            raise RuntimeError(self.error)


    # ========================================================
    # STOP RECORDER THREAD
    # ========================================================

    def stop(self):

        self.stop_event.set()

        if self.thread:

            self.thread.join(timeout=10)

            if self.thread.is_alive():

                raise RuntimeError(
                    "Recorder browser did not shut down in time; "
                    "recording was not finalized."
                )


# ============================================================
# PUBLIC FUNCTIONS USED BY recorder.py
# ============================================================

def start_browser_recorder(
    session_id: str,
    target_url: str,
    event_callback
):

    with _registry_lock:

        if session_id in _active_recorders:

            raise RuntimeError(
                "Recorder session is already active."
            )

        recorder = BrowserRecorder(
            session_id=session_id,
            target_url=target_url,
            event_callback=event_callback
        )

        _active_recorders[session_id] = recorder

    try:

        recorder.start()

        return recorder

    except Exception:

        recorder.stop_event.set()

        with _registry_lock:

            _active_recorders.pop(
                session_id,
                None
            )

        raise


def stop_browser_recorder(session_id: str):

    with _registry_lock:

        recorder = _active_recorders.get(
            session_id
        )

    if recorder is None:
        return False

    recorder.stop()

    with _registry_lock:

        if _active_recorders.get(session_id) is recorder:

            del _active_recorders[session_id]

    return True


def browser_recorder_active(session_id: str):

    with _registry_lock:

        recorder = _active_recorders.get(
            session_id
        )

    return bool(
        recorder
        and recorder.thread
        and recorder.thread.is_alive()
        and not recorder.stop_event.is_set()
    )