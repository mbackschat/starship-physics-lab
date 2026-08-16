"""Check the built site the way a reader meets it: in a browser, over HTTP.

The unit tests know what the build writes. They cannot know whether the reader's
browser boots Python, whether a chapter renders, or whether a link somebody was
sent still works. That gap is where the routing bug lived: every test passed
while every chapter URL answered with GitHub's error page.

Run against a local build, which needs no deploy:

    uv run python deploy/acceptance.py --local

Or against the deployed site:

    uv run python deploy/acceptance.py

Requires the dev dependencies and a browser:

    uv sync && uv run playwright install chromium
"""

import argparse
import socket
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "deploy" / "site"
LIVE_URL = "https://mbackschat.github.io/starship-physics-lab/"

PREFIX = "/starship-physics-lab"
"""Pages serves a project site from a sub-path, so the local run does too.

Serving from the root would hide anything that only breaks one level deep.
"""

BOOT_TIMEOUT_MS = 240_000
"""Generous: the first visit downloads a Python interpreter."""

SETTLE_MS = 5_000

CHAPTERS = (
    "Rocket equation",
    "Anatomy",
    "Launch",
    "Stages",
    "Reuse",
    "Weighing Starship",
    "The payload question",
    "Bigger is better",
    "Build your own",
    "Fact check",
    "Glossary",
)

SHARED_LINK = "The_payload_question?dry=165"
"""A chapter deep link carrying a setting, which is the whole point of sharing."""

HOSTILE = (
    "The_payload_question?dry=banana",
    "The_payload_question?dry=1e999",
    "Nonsense_chapter",
)
"""URLs a reader can produce by hand. None may break the page."""


class _PagesHandler(SimpleHTTPRequestHandler):
    """Serves a directory the way GitHub Pages serves a project site.

    Two behaviours matter and a plain file server has neither: everything lives
    under the repository sub-path, and any unmatched path answers with
    ``404.html`` rather than an error page.
    """

    def translate_path(self, path: str) -> str:
        """Map a request path onto a file, honouring the project sub-path.

        Args:
            path: The requested path.

        Returns:
            The file to serve.
        """
        stripped = path.split("?", 1)[0].split("#", 1)[0]
        stripped = stripped[len(PREFIX) :] or "/" if stripped.startswith(PREFIX) else "/__no__"
        return super().translate_path(stripped)

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        """Answer an unmatched path with the fallback page, as Pages does.

        Args:
            code: The status code.
            message: Short error message.
            explain: Long error message.
        """
        fallback = Path(self.directory) / "404.html"
        if code == 404 and fallback.exists():
            body = fallback.read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def log_message(self, *args: object) -> None:
        """Stay quiet; the checks do the talking."""


def serve(directory: Path) -> tuple[str, ThreadingHTTPServer]:
    """Start a Pages-alike server on a free port.

    Args:
        directory: The built site.

    Returns:
        Its base URL and the server, which the caller must shut down.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), partial(_PagesHandler, directory=str(directory))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}{PREFIX}/", server


def settle(page: Page, complaint: str) -> None:
    """Wait until the page has actually painted, not merely mounted.

    The app container appears well before Streamlit has drawn anything, so
    waiting on it alone reads an empty page and calls it a missing chapter.
    Every page here opens with a title, so wait for a heading, or for the
    traceback that explains why there is not one.

    Args:
        page: The browser page.
        complaint: What to say if it never arrives.

    Raises:
        RuntimeError: If nothing was ever drawn.
    """
    try:
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=BOOT_TIMEOUT_MS)
        page.wait_for_selector('h1, [data-testid="stException"]', timeout=BOOT_TIMEOUT_MS)
    except PlaywrightTimeout as error:
        raise RuntimeError(complaint) from error
    page.wait_for_timeout(SETTLE_MS)


def boot(page: Page, url: str) -> None:
    """Open a URL and wait for Python to finish starting in the browser.

    Args:
        page: The browser page.
        url: Where to go.

    Raises:
        RuntimeError: If the app never started.
    """
    page.goto(url, wait_until="domcontentloaded")
    settle(page, f"the app never booted at {url}")


def _heading(page: Page) -> str:
    """The page's title as the reader sees it.

    Args:
        page: The browser page.

    Returns:
        The first heading, or a marker if there is none.
    """
    return page.locator("h1").first.inner_text().strip() if page.locator("h1").count() else "(none)"


def _exception(page: Page) -> str:
    """Any Python traceback the page rendered.

    Args:
        page: The browser page.

    Returns:
        The first line of the traceback, or an empty string.
    """
    found = page.locator('[data-testid="stException"]')
    return found.first.inner_text().splitlines()[0] if found.count() else ""


def _slider(page: Page) -> str:
    """The first slider's rendered text.

    Args:
        page: The browser page.

    Returns:
        Its text, or a marker if the page has no slider.
    """
    sliders = page.locator('[data-testid="stSlider"]')
    return sliders.first.inner_text() if sliders.count() else "(no slider)"


def check_chapters(page: Page, base: str, failures: list[str]) -> None:
    """Every chapter must render without a traceback.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("1. every chapter renders")
    boot(page, base)
    for chapter in CHAPTERS:
        try:
            page.get_by_role("link", name=chapter).first.click(timeout=30_000)
        except PlaywrightTimeout:
            failures.append(f"{chapter}: no navigation link")
            print(f"   MISSING  {chapter}")
            continue
        page.wait_for_timeout(SETTLE_MS)
        if problem := _exception(page):
            failures.append(f"{chapter}: {problem}")
            print(f"   ERROR    {chapter}: {problem}")
            continue
        print(f"   ok       {_heading(page)}")


def check_shared_link(page: Page, base: str, failures: list[str]) -> None:
    """A link somebody was sent must open the chapter, on the shared setting.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("2. a shared link opens its chapter, on its setting")
    boot(page, base + SHARED_LINK)
    heading, slider = _heading(page), _slider(page)
    print(f"   {heading} · slider reads {' '.join(slider.split())}")
    if "payload question" not in heading:
        failures.append(f"a shared link landed on {heading!r}")
    if "165" not in slider:
        failures.append(f"a shared link lost its setting: {slider!r}")
    if "The_payload_question" not in page.url:
        failures.append(f"the address bar drifted off the chapter: {page.url}")


def check_reload(page: Page, base: str, failures: list[str]) -> None:
    """Reloading a chapter must not throw the reader out of it.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("3. reloading a chapter stays on it")
    boot(page, base + SHARED_LINK)
    page.reload(wait_until="domcontentloaded")
    settle(page, "the app never came back after a reload")
    heading = _heading(page)
    print(f"   {heading}")
    if "payload question" not in heading:
        failures.append(f"reloading a chapter landed on {heading!r}")


def check_hostile_urls(page: Page, base: str, failures: list[str]) -> None:
    """A hand-edited URL must fall back, never break.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("4. a hand-edited URL falls back rather than breaking")
    for hostile in HOSTILE:
        boot(page, base + hostile)
        if problem := _exception(page):
            failures.append(f"{hostile}: threw {problem}")
            print(f"   ERROR    {hostile}: {problem}")
        else:
            print(f"   ok       {hostile} -> {_heading(page)}")


def check_drawings(page: Page, base: str, failures: list[str]) -> None:
    """The drawn parts must arrive as drawings, not as their own source code.

    Streamlit parses markdown before it honours ``unsafe_allow_html``, and takes
    an indented line for a code block, so multi-line SVG reaches the page as
    literal text. Every unit test still passes when that happens, because the
    string handed over was perfectly good SVG. Only a browser can tell the
    difference, and this is the browser.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("5. the drawn parts actually draw")
    boot(page, base + "Rocket_equation")
    drawings = {
        "the mark": "svg.ship-mark",
        "the cutaway": "svg.ch1-svg",
        "the burn animation": ".js-plotly-plot",
    }
    for name, selector in drawings.items():
        if page.locator(selector).count():
            print(f"   ok       {name}")
        else:
            failures.append(f"{name} did not render ({selector} not found)")
            print(f"   MISSING  {name}")

    # The giveaway when markdown wins: the SVG source shown as words.
    if page.get_by_text("viewBox", exact=False).count():
        failures.append("SVG source is being displayed as text")
        print("   ERROR    SVG source is on the page as text")

    play = page.get_by_text("Burn it")
    if not play.count():
        failures.append("the burn animation has no play button")
        print("   MISSING  the play button")
        return
    before = page.locator(".js-plotly-plot .scatterlayer").first.inner_html()
    play.first.click()
    page.wait_for_timeout(2_500)
    if page.locator(".js-plotly-plot .scatterlayer").first.inner_html() == before:
        failures.append("pressing play did not move the burn animation")
        print("   ERROR    play did nothing")
    else:
        print("   ok       play runs the burn")


def main() -> int:
    """Run every check against a local build or the deployed site.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local", action="store_true", help="build and serve the site here instead of using Pages"
    )
    arguments = parser.parse_args()

    server = None
    if arguments.local:
        subprocess.run([sys.executable, str(ROOT / "deploy" / "build.py")], check=True)
        base, server = serve(SITE)
    else:
        base = LIVE_URL
    print(f"checking {base}\n")

    failures: list[str] = []
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch()
            page = browser.new_page(viewport={"width": 1600, "height": 1100})
            for check in (
                check_chapters,
                check_shared_link,
                check_reload,
                check_hostile_urls,
                check_drawings,
            ):
                check(page, base, failures)
                print()
            browser.close()
    finally:
        if server is not None:
            server.shutdown()

    if failures:
        print(f"{len(failures)} failure(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
