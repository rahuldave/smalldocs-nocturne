"""Build fresh Quarto QA plus real narrow iframe wrappers after the SmallDocs demo."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = json.loads((ROOT / "src/foundations.json").read_text())["theme"]


def main() -> None:
    """Use generated working files directly, never Git's last committed extension."""
    # Quarto deliberately excludes ignored/hidden project roots, even explicit files.
    # A fresh external directory exercises the same install shape as consumer tests.
    consumer = Path(tempfile.mkdtemp(prefix="theme-foundation-consumer-"))
    shutil.copytree(ROOT / "_extensions" / NAME, consumer / "_extensions" / NAME)
    shutil.copy2(ROOT / "example/pages/foundations.qmd", consumer / "index.qmd")
    (consumer / "_quarto.yml").write_text(
        f"project:\n  type: website\nwebsite:\n  title: Foundation consumer\n  navbar:\n    left:\n      - href: index.qmd\n        text: Foundations\nformat:\n  {NAME}-html:\n    toc: true\n"
    )
    subprocess.run(
        ["quarto", "render", "index.qmd", "--quiet"], cwd=consumer, check=True
    )
    if not (consumer / "_site/index.html").is_file():
        raise RuntimeError("Quarto did not produce the fixture index")
    site = ROOT / "example/_site"
    destination = site / "quarto-foundations"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(consumer / "_site", destination)
    shutil.rmtree(consumer)
    for filename, target in [
        ("qa-390.html", "pages/foundations.html"),
        ("qa-quarto-390.html", "quarto-foundations/index.html"),
    ]:
        (site / filename).write_text(
            f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{NAME} 390px viewport QA</title><body style="margin:0;font:16px system-ui"><p>Real 390px document viewport · {NAME} · use the embedded mode control.</p><iframe title="{NAME} 390px fixture" src="{target}" style="display:block;width:390px;height:1000px;border:1px solid #888"></iframe></body></html>"""
        )
    print(
        f'Fresh Quarto: {destination / "index.html"}; narrow wrappers: qa-390.html, qa-quarto-390.html'
    )


if __name__ == "__main__":
    main()
