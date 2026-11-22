"""Generate the code reference pages under docs/reference/.

Zensical does not support the mkdocs-gen-files and mkdocs-literate-nav
plugins, so this script writes real Markdown files instead of virtual
ones. Run it after adding, removing or renaming modules under src/:

    uv run scripts/gen_ref_pages.py

Then build or serve the docs with `zensical build` / `zensical serve`.
"""

import shutil
from pathlib import Path

root = Path(__file__).parent.parent
src = root / "src"
out = root / "docs" / "reference"

# Start from a clean slate so removed modules don't leave stale pages.
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

entries: list[tuple[str, Path]] = []

for path in sorted(src.rglob("*.py")):
    parts = path.relative_to(src).with_suffix("").parts

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = Path(*parts, "index.md")
    elif parts[-1] == "__main__":
        continue
    else:
        doc_path = Path(*parts).with_suffix(".md")

    identifier = ".".join(parts)
    full_doc_path = out / doc_path
    full_doc_path.parent.mkdir(parents=True, exist_ok=True)
    full_doc_path.write_text(f"::: {identifier}\n")
    entries.append((identifier, doc_path))

# Section index page linking to every generated page, since the
# literate-nav SUMMARY.md is no longer used to build the navigation.
lines = ["# Reference", ""]
for identifier, doc_path in sorted(entries):
    lines.append(f"- [{identifier}]({doc_path.as_posix()})")
(out / "index.md").write_text("\n".join(lines) + "\n")
