"""Build the static site that GitHub Pages serves.

GitHub Pages only serves files; the browser only runs JavaScript and
WebAssembly. Python works because Pyodide is CPython itself compiled to
WebAssembly, and stlite is Streamlit packaged to run on it. The reader's browser
downloads the interpreter, then executes the very same .py files that run
locally. Nothing runs on a server.

That imposes one discipline on the rest of the project, and it is why scipy and
ambiance were dropped: every runtime dependency has to be downloaded into the
reader's browser as a wheel.

Run:  uv run python deploy/build.py
Out:  deploy/site/
"""

import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "deploy" / "site"
LOGO = ROOT / "assets" / "logo.svg"

STLITE_VERSION = "1.8.1"
"""Pinned. An unpinned CDN import means the app can break without a commit.

The 1.x line mounts declaratively through a ``<streamlit-app>`` custom element
with ``<app-file>`` and ``<app-requirements>`` children, which is what this
build emits.
"""

REQUIREMENTS = ["pyyaml", "pydantic", "plotly"]
"""Everything beyond what stlite already bundles. Streamlit itself comes with it.

Keep this list short. Each entry is a wheel the reader downloads before they see
anything.
"""

ENTRYPOINT = "app/Home.py"

CHAPTER_PARAM = "chapter"
"""Where the bootstrap page leaves the chapter it found in the path.

Must match ``labbook.sharing.CHAPTER_PARAM``; a test holds the two together.
Kept as a literal rather than imported so the build stays runnable without the
app's own package on the path.
"""

TREES = {
    "app": ROOT / "app",
    "rocketry": ROOT / "src" / "rocketry",
    "labbook": ROOT / "src" / "labbook",
    "data": ROOT / "data",
    "assets": ROOT / "assets",
}
"""Source tree to destination. The packages are flattened out of ``src/`` so
they sit at the mount root and import without any path juggling."""

SUFFIXES = {".py", ".yaml", ".yml", ".svg"}


def collect() -> dict[str, Path]:
    """Find every file the app needs at runtime.

    Returns:
        Mapping of the path inside the virtual filesystem to the file on disk.
    """
    found: dict[str, Path] = {}
    for target, source in TREES.items():
        for path in sorted(source.rglob("*")):
            if path.suffix not in SUFFIXES or "__pycache__" in path.parts:
                continue
            found[f"{target}/{path.relative_to(source).as_posix()}"] = path
    return found


def write_site(files: dict[str, Path]) -> None:
    """Copy the app into the site directory and write its index page.

    The same page is written twice. GitHub Pages serves ``404.html`` for any
    path with no file behind it, and Streamlit puts a chapter's own path in the
    address bar the moment the reader navigates. Without the second copy, every
    URL the app itself produces answers with GitHub's error page: reload a
    chapter, bookmark one, or share one, and it dies.

    Args:
        files: Mapping of virtual path to file on disk.
    """
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    for virtual, real in files.items():
        destination = SITE / virtual
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(real, destination)
    index = _index(sorted(files))
    (SITE / "index.html").write_text(index)
    (SITE / "404.html").write_text(index)
    (SITE / ".nojekyll").write_text("")


def _index(virtual_paths: list[str]) -> str:
    """Render the bootstrap page.

    Args:
        virtual_paths: Every file to mount, in the virtual filesystem's terms.

    Returns:
        The HTML.

    Raises:
        ValueError: If the entrypoint is not among the files being mounted.
    """
    if ENTRYPOINT not in virtual_paths:
        raise ValueError(f"entrypoint {ENTRYPOINT!r} is not in the collected files")
    app_files = "\n      ".join(
        f'<app-file name="{path}" url="./{path}"'
        f'{" entrypoint" if path == ENTRYPOINT else ""}></app-file>'
        for path in virtual_paths
    )
    requirements = "\n        ".join(REQUIREMENTS)
    # Inlined rather than linked. This same page answers unmatched paths such as
    # /repo/The_payload_question, so a relative href would resolve against the
    # wrong directory in exactly the case the 404 copy exists to handle.
    logo = LOGO.read_text().strip()
    favicon = f"data:image/svg+xml,{quote(logo)}"
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Starship Physics Lab</title>
    <meta
      name="description"
      content="Understand Starship. Then build a better one. An interactive rocket physics explorer that runs entirely in your browser."
    />
    <link rel="icon" href="{favicon}" />
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE_VERSION}/build/stlite.css"
    />
    <style>
      body {{ margin: 0; font-family: system-ui, sans-serif; }}
      streamlit-app {{ display: block; min-height: 100vh; }}
      #boot {{
        position: fixed; inset: 0; display: grid; place-content: center;
        justify-items: center; text-align: center; gap: 0.75rem; padding: 2rem;
        background: #fcfcfb; color: #0b0b0b; --ship-gap: #fcfcfb; z-index: 9;
      }}
      /* The mark carries a default colour per scheme so it stands up as a
         plain image. Here it should take this screen's own, so override it;
         an id beats the one-class rules inside the file. */
      #boot svg {{
        height: 132px; width: auto;
        color: inherit; --ship-gap: inherit;
      }}
      #boot h1 {{ font-size: 1.4rem; margin: 0; }}
      #boot p {{ margin: 0; color: #52514e; max-width: 34rem; line-height: 1.5; }}
      @media (prefers-color-scheme: dark) {{
        #boot {{ background: #1a1a19; color: #fff; --ship-gap: #1a1a19; }}
        #boot p {{ color: #c3c2b7; }}
      }}
    </style>
    <script>
      // This same page answers every unmatched path, so a chapter URL such as
      // /repo/The_payload_question arrives here with the chapter in the path.
      // The app never sees that: stlite reports its own mount point as the URL
      // and passes on only the query string. So move the path into the query
      // string now, while this is still an ordinary web page.
      //
      // Deliberately dumb: it forwards whatever segment it finds and lets the
      // app decide whether that names a chapter. The slug rule lives in Python,
      // in labbook.sharing, and is not worth restating in a second language.
      (function () {{
        var here = new URL(window.location.href);
        var root = new URL(".", here).pathname;
        var rest = here.pathname.slice(root.length).replace(/\\/$/, "");
        if (!rest || rest.endsWith(".html")) return;
        here.searchParams.set("{CHAPTER_PARAM}", rest);
        window.history.replaceState(null, "", root + here.search + here.hash);
      }})();
    </script>
    <script
      type="module"
      src="https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE_VERSION}/build/stlite.js"
    ></script>
  </head>
  <body>
    <div id="boot">
      {logo}
      <h1>Starting the physics engine</h1>
      <p>
        This page runs Python in your browser, so the first visit downloads the
        interpreter. It takes a few seconds, then everything is instant and works
        offline. Nothing is sent to a server.
      </p>
    </div>
    <streamlit-app>
      <app-requirements>
        {requirements}
      </app-requirements>
      {app_files}
    </streamlit-app>
    <script type="module">
      const boot = document.getElementById("boot");
      new MutationObserver((_, observer) => {{
        if (document.querySelector('[data-testid="stAppViewContainer"]')) {{
          boot.remove();
          observer.disconnect();
        }}
      }}).observe(document.body, {{ childList: true, subtree: true }});
      setTimeout(() => boot?.remove(), 90000);
    </script>
  </body>
</html>
"""


def main() -> None:
    """Build the site and report what went into it."""
    files = collect()
    write_site(files)
    total_kb = sum(path.stat().st_size for path in files.values()) / 1024
    print(f"built {SITE.relative_to(ROOT)}")
    print(f"  {len(files)} files, {total_kb:,.0f} kB of Python and data")
    print(f"  entrypoint {ENTRYPOINT}")
    print(f"  extra wheels: {', '.join(REQUIREMENTS)}")


if __name__ == "__main__":
    main()
