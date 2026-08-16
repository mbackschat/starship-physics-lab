"""Capture screenshots of the live app for the README.

Drives a real browser against the deployed page, which means it doubles as an
end-to-end test: if Pyodide fails to boot, or a chapter throws, this script
fails rather than quietly saving a picture of an error message.

Re-run it whenever the app changes:

    uv run python deploy/screenshot.py                  # the live site
    uv run python deploy/screenshot.py --local          # a local streamlit run
    uv run python deploy/screenshot.py --shot launch    # just one

Requires the dev dependencies and a browser:

    uv sync && uv run playwright install chromium
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"
LIVE_URL = "https://mbackschat.github.io/starship-physics-lab/"
LOCAL_URL = "http://localhost:8501/"

BOOT_TIMEOUT_MS = 180_000
"""Generous: the first visit downloads a Python interpreter."""

SETTLE_MS = 4_000
"""Time for charts to finish drawing once the page has rendered."""


@dataclass(frozen=True, slots=True)
class Shot:
    """One screenshot to capture.

    Attributes:
        name: Output filename stem.
        page_label: Sidebar navigation link to click. Empty means the home page.
        description: What this shot is meant to show, printed while running.
        width: Viewport width, pixels.
        height: Viewport height, pixels.
    """

    name: str
    page_label: str
    description: str
    width: int = 1600
    height: int = 1000
    scroll_to: str = ""
    """Optional selector to scroll into view before shooting."""


SHOTS = (
    Shot(
        name="launch",
        page_label="Launch",
        description="the launch simulator, showing where a rocket's velocity actually goes",
        height=1450,
    ),
    Shot(
        name="stages",
        page_label="Stages",
        description="the staging split, worth a factor of two in payload",
        height=1150,
    ),
    Shot(
        name="anatomy",
        page_label="Anatomy",
        description="what a rocket is made of, and how little of it is cargo",
    ),
    Shot(
        name="rocket-equation",
        page_label="Rocket equation",
        description="the rocket equation with the reader's own numbers substituted in",
    ),
)


def capture(page: Page, shot: Shot, base_url: str) -> Path:
    """Navigate to one chapter and photograph it.

    Args:
        page: The browser page.
        shot: What to capture.
        base_url: Where the app is served from.

    Returns:
        The file written.

    Raises:
        RuntimeError: If the app never finished booting, or the chapter is
            missing, or it rendered an exception.
    """
    page.goto(base_url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=BOOT_TIMEOUT_MS)
    except PlaywrightTimeout as error:
        raise RuntimeError(
            f"the app never booted at {base_url}. If this is the live site, the "
            "Python-in-the-browser runtime failed to start."
        ) from error

    if shot.page_label:
        link = page.get_by_role("link", name=shot.page_label)
        try:
            link.first.click(timeout=30_000)
        except PlaywrightTimeout as error:
            raise RuntimeError(f"no navigation link named {shot.page_label!r}") from error

    page.wait_for_timeout(SETTLE_MS)
    page.wait_for_selector(".stPlotlyChart, .stMetric", timeout=60_000)
    page.wait_for_timeout(SETTLE_MS)

    if shot.scroll_to:
        page.locator(shot.scroll_to).first.scroll_into_view_if_needed(timeout=15_000)
        page.wait_for_timeout(SETTLE_MS)

    if page.locator('[data-testid="stException"]').count():
        text = page.locator('[data-testid="stException"]').first.inner_text()
        raise RuntimeError(f"{shot.name} rendered an exception:\n{text}")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{shot.name}.png"
    page.screenshot(path=path, full_page=False)
    return path


def _capture_with_retries(page: Page, shot: Shot, base_url: str, retries: int) -> Path:
    """Capture a shot, retrying transient failures.

    A freshly deployed page can serve a stale cache for a minute or two, and a
    cold Pyodide boot occasionally overruns. Neither is worth failing a run for.

    Args:
        page: The browser page.
        shot: What to capture.
        base_url: Where the app is served from.
        retries: Extra attempts after the first.

    Returns:
        The file written.

    Raises:
        RuntimeError: If every attempt failed, carrying the last error.
    """
    last: RuntimeError | None = None
    for attempt in range(retries + 1):
        try:
            return capture(page, shot, base_url)
        except RuntimeError as error:
            last = error
            if attempt < retries:
                print(f"  retry {shot.name} ({attempt + 1}/{retries})", file=sys.stderr)
                page.wait_for_timeout(10_000)
    raise last if last else RuntimeError(f"{shot.name} failed for no recorded reason")


def main() -> int:
    """Capture every requested screenshot.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true", help="shoot a local streamlit run")
    parser.add_argument("--url", default="", help="override the URL entirely")
    parser.add_argument("--shot", default="", help="capture only this one, by name")
    parser.add_argument("--headed", action="store_true", help="watch it happen")
    parser.add_argument(
        "--retries", type=int, default=2, help="attempts per shot before giving up"
    )
    arguments = parser.parse_args()

    base_url = arguments.url or (LOCAL_URL if arguments.local else LIVE_URL)
    wanted = [shot for shot in SHOTS if not arguments.shot or shot.name == arguments.shot]
    if not wanted:
        names = ", ".join(shot.name for shot in SHOTS)
        print(f"no shot named {arguments.shot!r}. Available: {names}", file=sys.stderr)
        return 2

    print(f"shooting {base_url}")
    failures = 0
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not arguments.headed)
        try:
            for shot in wanted:
                context = browser.new_context(
                    viewport={"width": shot.width, "height": shot.height},
                    device_scale_factor=2,
                    color_scheme="light",
                )
                page = context.new_page()
                try:
                    path = _capture_with_retries(page, shot, base_url, arguments.retries)
                    size_kb = path.stat().st_size / 1024
                    print(
                        f"  ok   {path.relative_to(ROOT)}  ({size_kb:,.0f} kB) "
                        f"- {shot.description}"
                    )
                except RuntimeError as error:
                    failures += 1
                    print(f"  FAIL {shot.name}: {error}", file=sys.stderr)
                finally:
                    context.close()
        finally:
            browser.close()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
