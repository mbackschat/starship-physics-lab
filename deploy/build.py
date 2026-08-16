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

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "deploy" / "site"

STLITE_VERSION = "0.83.1"
"""Pinned. An unpinned CDN import means the app can break without a commit."""

REQUIREMENTS = ["pyyaml", "pydantic", "plotly"]
"""Everything beyond what stlite already bundles. Streamlit itself comes with it.

Keep this list short. Each entry is a wheel the reader downloads before they see
anything.
"""

ENTRYPOINT = "app/Home.py"

TREES = {
    "app": ROOT / "app",
    "rocketry": ROOT / "src" / "rocketry",
    "labbook": ROOT / "src" / "labbook",
    "data": ROOT / "data",
}
"""Source tree to destination. The packages are flattened out of ``src/`` so
they sit at the mount root and import without any path juggling."""

SUFFIXES = {".py", ".yaml", ".yml"}


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
    manifest = {virtual: {"url": f"./{virtual}"} for virtual in files}
    (SITE / "index.html").write_text(_index(manifest))
    (SITE / ".nojekyll").write_text("")


def _index(manifest: dict[str, dict[str, str]]) -> str:
    """Render the bootstrap page.

    Args:
        manifest: Virtual path to fetch instruction, as stlite expects.

    Returns:
        The HTML.
    """
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Starship Physics Lab</title>
    <meta
      name="description"
      content="Why rockets perform the way they do, worked out by moving the numbers yourself."
    />
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE_VERSION}/build/stlite.css"
    />
    <style>
      body {{ margin: 0; font-family: system-ui, sans-serif; }}
      #boot {{
        position: fixed; inset: 0; display: grid; place-content: center;
        text-align: center; gap: 0.75rem; padding: 2rem;
        background: #fcfcfb; color: #0b0b0b; z-index: 9;
      }}
      #boot h1 {{ font-size: 1.4rem; margin: 0; }}
      #boot p {{ margin: 0; color: #52514e; max-width: 34rem; line-height: 1.5; }}
      @media (prefers-color-scheme: dark) {{
        #boot {{ background: #1a1a19; color: #fff; }}
        #boot p {{ color: #c3c2b7; }}
      }}
    </style>
  </head>
  <body>
    <div id="boot">
      <h1>Starting the physics engine</h1>
      <p>
        This page runs Python in your browser, so the first visit downloads the
        interpreter. It takes a few seconds, then everything is instant and works
        offline. Nothing is sent to a server.
      </p>
    </div>
    <div id="root"></div>
    <script type="module">
      import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@{STLITE_VERSION}/build/stlite.js";
      mount(
        {{
          requirements: {json.dumps(REQUIREMENTS)},
          entrypoint: {json.dumps(ENTRYPOINT)},
          files: {json.dumps(manifest, indent=10)},
        }},
        document.getElementById("root"),
      );
      const boot = document.getElementById("boot");
      new MutationObserver((_, observer) => {{
        if (document.querySelector('[data-testid="stAppViewContainer"]')) {{
          boot.remove();
          observer.disconnect();
        }}
      }}).observe(document.getElementById("root"), {{ childList: true, subtree: true }});
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
