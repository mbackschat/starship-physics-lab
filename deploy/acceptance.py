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
import re
import socket
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from labbook.navigation import CHAPTERS as REGISTRY

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

CHAPTERS = tuple(entry.label for entry in REGISTRY)
"""Derived, never listed.

A hand-kept copy here silently stopped checking chapter 12 the day it was added,
which is the exact failure this whole script exists to catch. The sidebar is drawn by hand in
`components.shell`, so `label` is exactly the text the browser will see."""

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


def _thumb(page: Page) -> str:
    """What the first slider's handle currently reads.

    Args:
        page: The browser page.

    Returns:
        The value shown above the handle.
    """
    return page.get_by_test_id("stSliderThumbValue").first.inner_text()


def _nudge(page: Page, which: int, times: int = 1) -> None:
    """Move a slider the way a reader would, from the keyboard.

    The handle is BaseWeb's ``role="slider"`` element rather than a range
    input. The two are not interchangeable: the development server and the
    interpreter the built site downloads ship different Streamlit frontends,
    and only the built one is what a reader meets.

    Args:
        page: The browser page.
        which: Which slider on the page, in draw order.
        times: How many steps to move it.
    """
    handle = page.get_by_test_id("stSlider").nth(which).locator('[role="slider"]')
    handle.focus()
    for _ in range(times):
        handle.press("ArrowRight")
    page.wait_for_timeout(SETTLE_MS)


def check_reset(page: Page, base: str, failures: list[str]) -> None:
    """Reset must move the control the reader is looking at, not only the value.

    Streamlit pushes a value down to the browser when session state is
    *assigned* to, and not when a key is deleted. A reset written the obvious
    way therefore leaves the slider sitting exactly where it was dragged while
    the numbers beside it jump back to their defaults, and the next rerun sends
    the stale value back up and undoes the reset completely.

    Every unit test passes throughout, because on the Python side the value
    really did return to its default. Only a browser can see the handle, which
    is why this check is here and not in `tests/test_app.py`.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("6. reset moves the controls, not only the numbers beside them")
    boot(page, base + "Rocket_equation")
    if not page.get_by_test_id("stSliderThumbValue").count():
        failures.append("chapter 1 drew no slider, so reset could not be checked")
        print("   MISSING  the sliders")
        return

    started = _thumb(page)
    _nudge(page, 0, times=20)
    moved = _thumb(page)
    if moved == started:
        failures.append(f"the slider would not move off {started}, leaving reset unchecked")
        print("   ERROR    the slider did not move")
        return
    print(f"   moved    {started} -> {moved}")

    page.get_by_role("button", name="Reset the controls").click()
    page.wait_for_timeout(SETTLE_MS)
    if (back := _thumb(page)) != started:
        failures.append(f"reset left the slider reading {back}, not {started}")
        print(f"   ERROR    reset left it at {back}")
        return
    print(f"   ok       back to {started}")

    # A browser that was never told still holds the old value and hands it back
    # on the next rerun, so touching another control is part of the check.
    _nudge(page, 2)
    if (after := _thumb(page)) != started:
        failures.append(f"the reset slider sprang back to {after} at the next touch")
        print(f"   ERROR    it sprang back to {after}")
    else:
        print(f"   ok       still {started} after another control moves")


DARK_PROBE = """
() => {
  const paint = (el, prop) => el ? getComputedStyle(el)[prop] : null;
  const surface = document.querySelector('.js-plotly-plot .main-svg');
  // A unified tooltip is drawn as a legend inside the hover layer, not as the
  // `.hovertext` a single-trace hover produces.
  const panel = document.querySelector('.hoverlayer .legend .bg');
  const words = document.querySelector('.hoverlayer .legend text');
  return {
    page: paint(document.querySelector('.stApp'), 'backgroundColor'),
    chart: surface ? surface.style.background : null,
    heading: paint(document.querySelector('h1'), 'color'),
    panel: paint(panel, 'fill'),
    words: paint(words, 'fill'),
  };
}
"""
"""What the reader's own browser says it painted, rather than what we asked for."""

DARK_ENOUGH = 0.35
"""Below this, on a 0 to 1 scale, a surface reads as dark."""

READABLE = 0.35
"""How far apart ink and its background must be to be legible."""


def _brightness(colour: str | None) -> float | None:
    """How light a rendered colour is, from 0 to 1.

    Args:
        colour: A CSS colour as the browser reports it, or None.

    Returns:
        Its perceived brightness, or None if there was no colour.
    """
    if not colour:
        return None
    parts = [int(number) for number in re.findall(r"\d+", colour)[:3]]
    if len(parts) < 3:
        return None
    red, green, blue = parts
    return (0.299 * red + 0.587 * green + 0.114 * blue) / 255


def check_dark_mode(page: Page, base: str, failures: list[str]) -> None:
    """A reader whose browser is dark must not be handed light charts.

    Streamlit's own chrome follows the browser's `prefers-color-scheme` without
    the server ever being told, so `theme.base` stays "light" and said so to
    anything that asked. Every chart was therefore drawn on a white surface and
    pasted onto a dark page. Nothing in the unit tests could see it: they ask a
    chart what it would look like in a mode they hand it, and it answers
    correctly in both.

    The same blind spot produced two smaller versions of itself, a near-white
    legend panel and white hover text on a white tooltip, which is why this
    check reads the colours the browser actually painted rather than the ones
    the code intended.

    Args:
        page: The browser page.
        base: Site root.
        failures: Collects what went wrong.
    """
    print("7. a dark browser gets a dark app, charts included")
    page.emulate_media(color_scheme="dark")
    try:
        boot(page, base + "The_payload_question")
        page.wait_for_selector(".js-plotly-plot", timeout=BOOT_TIMEOUT_MS)
        page.wait_for_timeout(SETTLE_MS)

        # Plotly's own drag layer, which is exactly the plot area. Aiming at
        # the middle of the container instead lands in the margin below the
        # axis, where there is nothing to hover and no tooltip to check.
        plot = page.locator(".js-plotly-plot .nsewdrag").first
        box = plot.bounding_box()
        if box:
            middle = (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.move(*middle)
            page.mouse.move(middle[0] + 6, middle[1])
            page.wait_for_timeout(2_000)
        seen = page.evaluate(DARK_PROBE)

        for name in ("page", "chart"):
            level = _brightness(seen[name])
            if level is None:
                failures.append(f"the {name} reported no colour in dark mode")
                print(f"   MISSING  the {name} has no colour")
            elif level > DARK_ENOUGH:
                failures.append(f"the {name} stayed light in a dark browser: {seen[name]}")
                print(f"   ERROR    the {name} is light: {seen[name]}")
            else:
                print(f"   ok       the {name} is dark: {seen[name]}")

        ink, behind = _brightness(seen["words"]), _brightness(seen["panel"])
        if ink is None or behind is None:
            # Reported rather than skipped: the tooltip is the thing that was
            # unreadable, so not reaching it leaves the defect unchecked.
            failures.append("no tooltip appeared to check, so its contrast is unverified")
            print("   ERROR    no tooltip appeared")
        elif abs(ink - behind) < READABLE:
            failures.append(f"tooltip text {seen['words']} is unreadable on {seen['panel']}")
            print(f"   ERROR    tooltip {seen['words']} on {seen['panel']}")
        else:
            print(f"   ok       tooltip text reads against its panel ({abs(ink - behind):.2f})")
    finally:
        page.emulate_media(color_scheme="light")


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
                check_reset,
                check_dark_mode,
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
