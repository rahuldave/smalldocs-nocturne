"""Install the shipped extension and render a fresh consumer site."""

import json
import shutil
from pathlib import Path

from smalldocs.extensions import add, installed
from smalldocs.site import build

ROOT = Path(__file__).resolve().parents[1]
NAME = json.loads((ROOT / "src/theme.json").read_text())["name"]


def test_install_and_render(tmp_path):
    (tmp_path / "_smalldocs.yml").write_text(
        f"website:\n  title: Consumer site\n  navbar: true\ntheme: {NAME}\ncode-copy: true\n"
    )
    (tmp_path / "index.qmd").write_text(
        '---\ntitle: A fresh consumer site\n---\n\n## Code\n\n```python\nprint("hello")\n```\n'
    )
    # Test generated working files, not the last Git commit.
    shutil.copytree(ROOT / "_extensions" / NAME, tmp_path / "_extensions" / NAME)
    assert (tmp_path / "_extensions" / NAME / "foundations.json").is_file()
    site = build(tmp_path)
    assert not site.warnings
    output = tmp_path / "_site"
    html = (output / "index.html").read_text()
    assert f"site_libs/themes/{NAME}/{NAME}.css" in html
    assert f"site_libs/themes/{NAME}/{NAME}-dark.css" in html
    fonts = output / "site_libs/themes" / NAME / "fonts"
    assert (fonts / "ibm-plex-mono-400-normal.ttf").is_file()
    assert "smalldocsToggleScheme" in html
