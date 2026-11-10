# Copyright 2026 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Browser UI end-to-end tests using Playwright."""

from collections.abc import Iterator
import contextlib
import logging
import os
import re
from typing import Any
from typing import Optional
import urllib.parse
import uuid

try:
    # pylint: disable=import-error
    from playwright.sync_api import expect  # type: ignore[import-not-found]
    from playwright.sync_api import Page  # type: ignore[import-not-found]
    from playwright.sync_api import Response  # type: ignore[import-not-found]
    from playwright.sync_api import (  # type: ignore[import-not-found]
        sync_playwright,
    )
except ImportError:
    expect: Any = None  # type: ignore[no-redef]
    Page = Any  # type: ignore[assignment,misc]
    Response = Any  # type: ignore[assignment,misc]
    sync_playwright: Any = None  # type: ignore[no-redef]

from . import interface
from . import manager

logger = logging.getLogger("timesketch.e2e.ui_test")

DEFAULT_ARTIFACT_DIR = "/tmp/timesketch-ui-artifacts"
CSV_FIXTURE_FILENAME = "sigma_events.csv"
EXPECTED_CSV_EVENTS = 4
CSV_INDEX_TIMEOUT_SECONDS = 60
EXPECTED_PLASO_EVENTS = 3205
PLASO_INDEX_TIMEOUT_SECONDS = 300


class UiEndToEndTest(interface.BaseEndToEndTest):
    """End-to-end tests exercising the compiled web UI in headless Chromium.

    Tests are ordered for rapid fail-fast feedback while overlapping slow Plaso
    ingestion in the background:
      1. test_01: UI reachability, login redirect guard, static /dist/ assets.
      2. test_02: Auth check, blank sketch dialog, session cookie capture.
      3. test_03: Kick off Plaso upload in UI (HTTP 201) and return immediately
         so a Celery worker runs psort.py in the background.
      4. test_04: Upload 702-byte sigma_events.csv via UI, await live 5s SPA
         auto-poll, and query 4 events in Explore while Plaso is still running.
      5. test_05: Await the remaining tail of the parallel Plaso timeline and
         query all 3,205 events in Explore.
    """

    NAME = "ui_test"

    def __init__(self) -> None:
        super().__init__()
        self._step_screenshots: dict[str, str] = {}
        self._auth_storage_state: Any = None
        self._pending_plaso_sketch_id: Optional[int] = None

    def setup(self) -> None:
        """Resets per-suite UI state; tests drive imports through the browser."""
        self._step_screenshots.clear()
        self._auth_storage_state = None
        self._pending_plaso_sketch_id = None

    @staticmethod
    def _artifact_dir() -> str:
        """Returns the configured UI E2E artifact output directory."""
        return os.environ.get("UI_E2E_ARTIFACT_DIR", DEFAULT_ARTIFACT_DIR)

    def _capture_step_screenshot(
        self, page: Page, step_slug: str, title: str, description: str
    ) -> str:
        """Captures a milestone PNG screenshot and updates steps/summary.md.

        Args:
            page (playwright.sync_api.Page): Active Playwright page.
            step_slug (str): Deterministic filename stem (e.g. '01_login_page').
            title (str): Short human-readable milestone title.
            description (str): One-sentence explanation of what the view shows.

        Returns:
            str: Absolute path to the written PNG file.
        """
        steps_dir = os.path.join(self._artifact_dir(), "steps")
        os.makedirs(steps_dir, exist_ok=True)
        filename = f"{step_slug}.png"
        png_path = os.path.join(steps_dir, filename)
        page.screenshot(path=png_path, full_page=True)

        parsed_path = urllib.parse.urlsplit(page.url).path or "/"
        self._step_screenshots[step_slug] = (
            f"| **{title}** | `{parsed_path}` | `steps/{filename}` | {description} |"
        )
        summary_lines = [
            "### Playwright UI E2E Milestone Storyboard",
            "",
            "| Step | Route | Screenshot | Description |",
            "| :--- | :--- | :--- | :--- |",
            *self._step_screenshots.values(),
            "",
        ]
        summary_path = os.path.join(steps_dir, "summary.md")
        with open(summary_path, "w", encoding="utf-8") as md_fh:
            md_fh.write("\n".join(summary_lines))
        return png_path

    @contextlib.contextmanager
    def _browser_page(self, test_label: str) -> Iterator[Page]:
        """Yields an isolated Playwright Page with network, JS, and trace guards.

        Args:
            test_label (str): Identifier used for failure screenshot/trace files.

        Yields:
            playwright.sync_api.Page: Fresh browser page with 1440x900 viewport.

        Raises:
            RuntimeError: If Playwright is not installed in the active container.
        """
        if sync_playwright is None or expect is None:
            raise RuntimeError(
                "playwright is not installed in this container. Run ui_test via "
                "the '--profile ui' Docker Compose sidecar (ui-e2e)."
            )

        artifact_dir = self._artifact_dir()
        os.makedirs(artifact_dir, exist_ok=True)
        errors: list[str] = []

        def _on_response(response: Response) -> None:
            path = urllib.parse.urlsplit(response.url).path
            if path.startswith("/api/v1/") and response.status >= 500:
                errors.append(
                    f"API 5xx: {response.request.method} {path} -> "
                    f"HTTP {response.status}"
                )
            elif path.startswith("/dist/") and response.status >= 400:
                errors.append(
                    f"Asset error: {response.request.method} {path} -> "
                    f"HTTP {response.status}"
                )

        context_kwargs: dict[str, Any] = {"viewport": {"width": 1440, "height": 900}}
        if self._auth_storage_state is not None:
            context_kwargs["storage_state"] = self._auth_storage_state

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(**context_kwargs)
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()
            page.on("pageerror", lambda exc: errors.append(f"JS error: {exc}"))
            page.on("response", _on_response)
            try:
                yield page
                self.assertions.assertEqual(
                    errors,
                    [],
                    f"Browser errors during {test_label}: {errors}",
                )
                context.tracing.stop()
            except Exception:
                screenshot_path = os.path.join(
                    artifact_dir, f"{test_label}_failure.png"
                )
                trace_path = os.path.join(artifact_dir, f"{test_label}_trace.zip")
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    context.tracing.stop(path=trace_path)
                    logger.error(
                        "Saved UI failure artifacts for %s: %s and %s",
                        test_label,
                        screenshot_path,
                        trace_path,
                    )
                except Exception as e:  # pylint: disable=broad-except
                    logger.warning(
                        "Could not write failure artifacts for %s: %s",
                        test_label,
                        e,
                    )
                raise
            finally:
                context.close()
                browser.close()

    def _login_via_ui(
        self,
        page: Page,
        username: str = interface.USERNAME,
        password: str = interface.PASSWORD,
    ) -> None:
        """Submits the local login form in the browser and caches storage_state.

        Args:
            page (playwright.sync_api.Page): Active Playwright page.
            username (str): Account username to submit.
            password (str): Account password to submit.
        """
        page.goto(f"{interface.HOST_URI}/login/", wait_until="domcontentloaded")
        page.locator('input[name="username"]').fill(username)
        page.locator('input[name="password"]').fill(password)
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url(re.compile(r"^https?://[^/]+/?$"), timeout=30000)
        expect(
            page.get_by_role("heading", name="Start new investigation")
        ).to_be_visible(timeout=30000)
        self._auth_storage_state = page.context.storage_state()

    def _create_blank_sketch_via_ui(self, page: Page, sketch_name: str) -> int:
        """Creates a blank sketch from the Home dialog and returns its sketch ID.

        Args:
            page (playwright.sync_api.Page): Authenticated Playwright page on '/'.
            sketch_name (str): Name for the new sketch.

        Returns:
            int: Newly created Timesketch sketch ID parsed from the SPA route.
        """
        page.get_by_role("button", name="Blank sketch").click()
        name_input = page.get_by_placeholder("Name your sketch")
        expect(name_input).to_be_visible(timeout=15000)
        name_input.fill(sketch_name)
        page.get_by_role("button", name="Create").click()

        # router.js redirects Overview ('/sketch/:sketchId') to Explore.
        page.wait_for_url(re.compile(r".*/sketch/\d+/explore"), timeout=30000)
        expect(page.get_by_text("It's empty around here")).to_be_visible(timeout=30000)
        expect(page.get_by_role("button", name="Add Timeline")).to_be_visible(
            timeout=15000
        )

        match = re.search(r"/sketch/(\d+)/explore", page.url)
        self.assertions.assertIsNotNone(
            match, f"Could not extract sketch ID from URL: {page.url}"
        )
        assert match is not None
        return int(match.group(1))

    def _open_new_empty_sketch_in_ui(self, page: Page, sketch_prefix: str) -> int:
        """Creates a fresh sketch via API and opens its empty Explore view in UI.

        Args:
            page (playwright.sync_api.Page): Authenticated Playwright page.
            sketch_prefix (str): Prefix for the unique sketch name.

        Returns:
            int: Newly created sketch ID.
        """
        sketch_name = f"{sketch_prefix}_{uuid.uuid4().hex[:8]}"
        sketch_id = self.api.create_sketch(name=sketch_name).id
        page.goto(
            f"{interface.HOST_URI}/sketch/{sketch_id}/explore",
            wait_until="domcontentloaded",
        )
        expect(page.get_by_text("It's empty around here")).to_be_visible(timeout=30000)
        expect(page.get_by_role("button", name="Add Timeline")).to_be_visible(
            timeout=15000
        )
        return sketch_id

    def _submit_timeline_upload_via_ui(
        self,
        page: Page,
        file_path: str,
        step_screenshot: Optional[tuple[str, str, str]] = None,
    ) -> str:
        """Uploads a timeline file through UploadForm.vue and awaits HTTP 201.

        Args:
            page (playwright.sync_api.Page): Page on empty '/sketch/<id>/explore'.
            file_path (str): Path to .csv, .jsonl, or .plaso fixture on disk.
            step_screenshot (Optional[tuple[str, str, str]]): Optional
                (slug, title, description) to capture before clicking Submit.

        Returns:
            str: Auto-populated timeline name stem.
        """
        self.assertions.assertTrue(
            os.path.isfile(file_path), f"Upload fixture missing at {file_path}"
        )
        filename = os.path.basename(file_path)
        expected_tl_name = os.path.splitext(filename)[0]

        page.get_by_role("button", name="Add Timeline").click()
        expect(page.get_by_text("Upload Plaso/JSONL/CSV file")).to_be_visible(
            timeout=15000
        )

        page.locator("input#datafile").set_input_files(file_path)
        expect(page.get_by_role("textbox", name="Timeline Name")).to_have_value(
            expected_tl_name, timeout=15000
        )
        expect(page.get_by_text(filename)).to_be_visible(timeout=15000)

        if step_screenshot is not None:
            slug, title, description = step_screenshot
            self._capture_step_screenshot(page, slug, title, description)

        with page.expect_response(
            lambda resp: "/api/v1/upload/" in resp.url
            and resp.request.method == "POST",
            timeout=60000,
        ) as upload_info:
            page.get_by_role("button", name="Submit").click()

        self.assertions.assertEqual(upload_info.value.status, 201)

        # UploadForm.vue dispatches updateSketch on 201, transitioning Sketch.vue
        # out of its empty state and mounting Explore (#tsSearchInput).
        expect(page.get_by_text("It's empty around here")).to_be_hidden(timeout=30000)
        expect(page.locator("#tsSearchInput")).to_be_visible(timeout=30000)
        return expected_tl_name

    def _await_chip_and_run_wildcard_search(
        self,
        page: Page,
        sketch_id: int,
        expected_tl_name: str,
        expected_events: int,
        timeout_seconds: int,
    ) -> None:
        """Awaits live SPA timeline enablement and runs '*' in #tsSearchInput.

        Args:
            page (playwright.sync_api.Page): Active page on '/sketch/<id>/explore'.
            sketch_id (int): Target sketch identifier.
            expected_tl_name (str): Expected timeline chip label.
            expected_events (int): Expected total event count in UI and API.
            timeout_seconds (int): Max seconds to wait for timeline indexing.
        """
        search_input = page.locator("#tsSearchInput")
        expect(search_input).to_be_visible(timeout=30000)

        processed_chip = page.locator(".v-chip.timeline-chip").filter(
            has_text=expected_tl_name
        )
        expect(processed_chip).to_be_visible(timeout=timeout_seconds * 1000)
        expect(processed_chip).not_to_have_class(re.compile(r"\bfailed\b"))
        expect(
            processed_chip.locator(".timeline-name-ellipsis:not(.disabled)")
        ).to_be_visible(timeout=timeout_seconds * 1000)

        with page.expect_response(
            lambda resp: f"/api/v1/sketches/{sketch_id}/explore/" in resp.url
            and resp.request.method == "POST",
            timeout=60000,
        ) as explore_info:
            search_input.fill("*")
            search_input.press("Enter")

        self.assertions.assertEqual(explore_info.value.status, 200)
        expect(page.get_by_text(f"of {expected_events} events")).to_be_visible(
            timeout=30000
        )
        event_rows = page.locator(".v-data-table tbody tr")
        expect(event_rows.first).to_be_visible(timeout=15000)
        self.assertions.assertGreater(
            event_rows.count(),
            0,
            "Expected rendered event rows in Explore data table.",
        )
        events = self.api.get_sketch(sketch_id).explore("*", as_pandas=True)
        self.assertions.assertEqual(len(events), expected_events)

    def test_01_ui_reachable_and_login_guard(self) -> None:
        """Unauthenticated root redirects to /login/ and serves static UI assets."""
        with self._browser_page("test_01_ui_reachable") as page:
            response = page.goto(
                f"{interface.HOST_URI}/", wait_until="domcontentloaded"
            )
            self.assertions.assertIsNotNone(response)
            assert response is not None
            self.assertions.assertEqual(response.status, 200)
            self.assertions.assertIn("/login/", page.url)

            expect(page).to_have_title(re.compile(r"Timesketch", re.IGNORECASE))
            expect(page.locator("img.logo-image")).to_be_visible()
            expect(page.locator('input[name="username"]')).to_be_visible()
            expect(page.locator('input[name="password"]')).to_be_visible()
            expect(page.get_by_role("button", name="Sign in")).to_be_visible()

            csrf_token = page.locator("input#csrf_token").get_attribute("value")
            self.assertions.assertTrue(
                bool(csrf_token), "CSRF token hidden input must be populated."
            )

            logo_resp = page.request.get(
                f"{interface.HOST_URI}/dist/timesketch-color.png"
            )
            self.assertions.assertEqual(logo_resp.status, 200)

            self._capture_step_screenshot(
                page,
                "01_login_page",
                "Step 1 - Login Guard & Static Assets",
                "Unauthenticated root redirects to /login/ with Timesketch "
                "branding, CSRF token, and sign-in form.",
            )

    def test_02_login_and_create_blank_sketch(self) -> None:
        """Rejects invalid credentials, logs in, and creates a blank sketch."""
        with self._browser_page("test_02_login_and_sketch") as page:
            page.goto(f"{interface.HOST_URI}/login/", wait_until="domcontentloaded")
            page.locator('input[name="username"]').fill(interface.USERNAME)
            page.locator('input[name="password"]').fill(
                f"invalid_pw_{uuid.uuid4().hex}"
            )
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_load_state("domcontentloaded")
            self.assertions.assertIn("/login/", page.url)
            expect(page.get_by_role("button", name="Sign in")).to_be_visible()

            self._login_via_ui(page)
            self._capture_step_screenshot(
                page,
                "02_home_dashboard",
                "Step 2 - Authenticated Home Dashboard",
                "Authenticated session routed to the Home SPA displaying "
                "investigation actions and sketch list.",
            )

            sketch_name = f"ui_e2e_blank_{uuid.uuid4().hex[:8]}"
            sketch_id = self._create_blank_sketch_via_ui(page, sketch_name)
            self._capture_step_screenshot(
                page,
                "03_empty_sketch_explore",
                "Step 3 - Newly Created Blank Sketch",
                "Blank sketch routed to Explore empty state with Add Timeline "
                "call-to-action.",
            )

            api_sketch = self.api.get_sketch(sketch_id)
            self.assertions.assertEqual(api_sketch.name, sketch_name)

    def test_03_kickoff_plaso_upload_via_ui(self) -> None:
        """Starts browser Plaso upload immediately so Celery runs in parallel."""
        plaso_filename = interface.get_plaso_filename()
        plaso_path = os.path.join(interface.TEST_DATA_DIR, plaso_filename)

        with self._browser_page("test_03_kickoff_plaso") as page:
            sketch_id = self._open_new_empty_sketch_in_ui(page, "ui_e2e_plaso")
            self._submit_timeline_upload_via_ui(
                page,
                plaso_path,
                step_screenshot=(
                    "04_upload_plaso_modal",
                    "Step 4 - Plaso Upload Form Populated",
                    f"UploadForm.vue modal populated with {plaso_filename} "
                    "metadata and auto-derived timeline name before background "
                    "psort.py ingestion.",
                ),
            )
            self._pending_plaso_sketch_id = sketch_id

    def test_04_fast_csv_upload_and_explore_via_ui(self) -> None:
        """Uploads a 4-row CSV for rapid UI/auto-poll/Explore feedback."""
        csv_path = os.path.join(interface.TEST_DATA_DIR, CSV_FIXTURE_FILENAME)

        with self._browser_page("test_04_fast_csv_explore") as page:
            sketch_id = self._open_new_empty_sketch_in_ui(page, "ui_e2e_csv")
            expected_tl_name = self._submit_timeline_upload_via_ui(page, csv_path)

            # Without reloading the page, TimelineComponent.vue polls every 5s
            # and enables sigma_events on a separate Celery worker while Plaso
            # continues processing in the background.
            self._await_chip_and_run_wildcard_search(
                page,
                sketch_id=sketch_id,
                expected_tl_name=expected_tl_name,
                expected_events=EXPECTED_CSV_EVENTS,
                timeout_seconds=CSV_INDEX_TIMEOUT_SECONDS,
            )
            expect(page.get_by_text("apt-get install zmap")).to_be_visible(
                timeout=15000
            )
            self._capture_step_screenshot(
                page,
                "05_explore_csv_events",
                "Step 5 - Fast CSV Events in Explore",
                "702-byte sigma_events.csv indexed on a parallel Celery worker, "
                "auto-enabled by the live SPA poll, and queried in Explore.",
            )

    def test_05_await_parallel_plaso_and_search_events(self) -> None:
        """Awaits the background Plaso timeline and queries all 3,205 events."""
        plaso_filename = interface.get_plaso_filename()
        expected_tl_name = os.path.splitext(plaso_filename)[0]
        self.assertions.assertIsNotNone(self._pending_plaso_sketch_id)
        assert self._pending_plaso_sketch_id is not None
        sketch_id = self._pending_plaso_sketch_id

        with self._browser_page("test_05_await_plaso") as page:
            page.goto(
                f"{interface.HOST_URI}/sketch/{sketch_id}/explore",
                wait_until="domcontentloaded",
            )
            self._await_chip_and_run_wildcard_search(
                page,
                sketch_id=sketch_id,
                expected_tl_name=expected_tl_name,
                expected_events=EXPECTED_PLASO_EVENTS,
                timeout_seconds=PLASO_INDEX_TIMEOUT_SECONDS,
            )
            self._capture_step_screenshot(
                page,
                "06_explore_plaso_events",
                "Step 6 - Parallel Plaso Events in Explore",
                "Background Plaso timeline (evtx_20260720.plaso) finished "
                "indexing and rendered 3,205 searchable EVTX events in Explore.",
            )


if sync_playwright is not None:
    manager.EndToEndTestManager.register_test(UiEndToEndTest)
