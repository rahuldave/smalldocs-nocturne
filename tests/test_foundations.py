"""Numerical roles, reproducibility and fresh working-file consumer coverage."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
import pytest
from smalldocs.site import build

ROOT = Path(__file__).resolve().parents[1]
FOUNDATIONS = json.loads((ROOT / "src/foundations.json").read_text())
NAME = FOUNDATIONS["theme"]
EXT = ROOT / "_extensions" / NAME


def contrast(a, b):
    def lum(c):
        channels = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        return sum(
            w * (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
            for v, w in zip(channels, [0.2126, 0.7152, 0.0722])
        )

    x, y = sorted([lum(a), lum(b)])
    return (y + 0.05) / (x + 0.05)


def test_named_pairs_and_source_manifest():
    assert (ROOT / "src/foundations.json").read_bytes() == (
        EXT / "foundations.json"
    ).read_bytes()
    for data in FOUNDATIONS["modes"].values():
        role = lambda key: data["swatches"][data["roles"][key]]
        for text in [
            "ink",
            "muted",
            "accent-text",
            "link-hover",
            "secondary-text",
            "code-ink",
            "secondary-action",
        ]:
            for bg in ["paper", "panel", "code"]:
                assert contrast(role(text), role(bg)) >= 5
        for fg, bg in [
            ("button-ink", "primary-fill"),
            ("primary-hover-ink", "primary-hover-fill"),
            ("selected-ink", "selected-fill"),
            ("disabled-ink", "disabled-fill"),
        ]:
            assert contrast(role(fg), role(bg)) >= 4.5
        for edge in ["focus", "control-boundary"]:
            for bg in ["paper", "panel", "code"]:
                assert contrast(role(edge), role(bg)) >= 3
        for state in data["states"].values():
            assert contrast(state["ink"], state["fill"]) >= 5
            assert contrast(state["boundary"], state["fill"]) >= 3
        assert contrast(data["states"]["danger"]["boundary"], role("paper")) >= 3
        assert role("primary-hover-fill") != role("secondary-text")


def test_build_reproducible_and_quarto_overlay_only():
    before = {p.relative_to(EXT): p.read_bytes() for p in EXT.rglob("*") if p.is_file()}
    subprocess.run([sys.executable, str(ROOT / "scripts/build.py")], check=True)
    assert before == {
        p.relative_to(EXT): p.read_bytes() for p in EXT.rglob("*") if p.is_file()
    }
    for path in EXT.glob("*.scss"):
        text = path.read_text()
        assert "Bootstrap v" not in text
        assert "main.content" not in text
        assert ".btn-primary{" not in text
    css = (EXT / f"{NAME}.css").read_text()
    assert "--bs-btn-hover-bg:var(--f-primary-hover-fill)" in css
    assert "html main.content .callout :is(p,li)" in css
    assert "opacity:1" in css
    assert "font-synthesis:none" in css
    assert (
        "html body #quarto-content .callout.callout-caution .callout-body { color:var(--f-ink); background:var(--f-paper); }"
        in css
    )
    assert (
        "html body #quarto-content .callout.callout-style-default.callout-caution .callout-header { color:var(--f-danger-ink)"
        in css
    )


def consumer(tmp_path):
    shutil.copytree(EXT, tmp_path / "_extensions" / NAME)
    shutil.copy2(ROOT / "example/pages/foundations.qmd", tmp_path / "index.qmd")
    return tmp_path


def test_working_files_smalldocs_consumer(tmp_path):
    root = consumer(tmp_path)
    (root / "_smalldocs.yml").write_text(
        f"website:\n  title: Foundation consumer\n  navbar: true\ntheme: {NAME}\ntoc: true\n"
    )
    result = build(root)
    assert not result.warnings
    assert (root / "_extensions" / NAME / "foundations.json").read_bytes() == (
        EXT / "foundations.json"
    ).read_bytes()
    assert (root / "_site/site_libs/themes" / NAME / f"{NAME}.css").read_bytes() == (
        EXT / f"{NAME}.css"
    ).read_bytes()
    html = (root / "_site/index.html").read_text()
    for token in [
        "reading-primary",
        'aria-invalid="true"',
        "reading-disabled-button",
        "callout-warning",
        "Current page",
    ]:
        assert token in html


def test_working_files_quarto_consumer(tmp_path):
    if not shutil.which("quarto"):
        pytest.skip("Quarto executable unavailable")
    root = consumer(tmp_path)
    (root / "_quarto.yml").write_text(
        f"project:\n  type: website\nwebsite:\n  title: Foundation consumer\n  navbar:\n    left:\n      - href: index.qmd\n        text: Foundations\nformat:\n  {NAME}-html:\n    toc: true\n"
    )
    result = subprocess.run(
        ["quarto", "render", str(root), "--quiet"],
        cwd=root,
        timeout=180,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "SCSSParsingError" not in result.stderr, result.stderr
    html = (root / "_site/index.html").read_text()
    assert "reading-primary" in html and "quarto-bootstrap" in html
    assert "foundations.css" in html
    assets = list((root / "_site").rglob("*.css"))
    assert any("--f-primary-fill" in p.read_text() for p in assets)


def test_profile_jobs_drive_css_and_single_card_padding():
    import copy

    module_path = ROOT / "scripts/foundations.py"
    spec = importlib.util.spec_from_file_location("foundation_support", module_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    changed = copy.deepcopy(FOUNDATIONS)
    changed["typography"]["profiles"]["reading"]["title"] = 48
    changed["typography"]["profiles"]["reading"]["metadata"] = 16
    changed["spacing"]["profiles"]["reading"]["panel"] = 32
    changed["spacing"]["profiles"]["reading"]["columns"] = 48
    changed["typography"]["lineHeights"]["reading"] = 1.75
    css = helper.rules(changed)
    assert "--f-reading-title: 3rem;" in css
    assert "--f-reading-metadata: 1rem;" in css
    assert "--f-reading-space-panel: 2rem;" in css
    assert "--f-reading-space-columns: 3rem;" in css
    assert (
        "--sd-gap: var(--f-reading-space-columns)"
        in (ROOT / "src/common.css").read_text()
    )
    assert "--f-reading-space-outer" in (ROOT / "src/common.css").read_text()
    assert "--f-line-reading: 1.75;" in css
    assert "font-size:var(--f-reading-title)" in css
    assert "html div.sourceCode > pre.sourceCode { padding:0; margin:0; }" in css
    assert (
        "html body #quarto-content div.sourceCode :is(pre,code) { padding:0; margin:0; }"
        in css
    )
    assert (
        "html body #quarto-content div.sourceCode :is(pre,code,span) { font-family:var(--f-font-code); font-size:var(--f-reading-code); line-height:var(--f-line-code); }"
        in css
    )
    assert "html .card { padding:0; }" in css
    assert "html .card-body { padding:var(--f-reading-space-panel); }" in css


def test_selected_icon_ink_is_independent_of_paper(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "custom_build", ROOT / "scripts/build.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    css = module.palette(module.THEME["light"], "#123456")
    assert "stroke='%23123456'" in css
    assert "fill='%23123456'" in css


def test_authoritative_source_derives_aliases_and_icon_defaults(tmp_path):
    import copy

    spec = importlib.util.spec_from_file_location(
        "foundation_support", ROOT / "scripts/foundations.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    (tmp_path / "src").mkdir()
    changed = copy.deepcopy(FOUNDATIONS)
    ink_ref = changed["modes"]["light"]["roles"]["ink"]
    changed["modes"]["light"]["swatches"][ink_ref] = "#123456"
    (tmp_path / "src/foundations.json").write_text(json.dumps(changed))
    shutil.copy2(ROOT / "src/theme-info.json", tmp_path / "src/theme-info.json")
    _, aliases = helper.load(tmp_path)
    assert aliases["light"]["ink"] == "#123456"
    assert json.loads((tmp_path / "src/theme.json").read_text()) == aliases
    for mode, suffix in [("light", ""), ("dark", "-dark")]:
        text = (EXT / f"{NAME}{suffix}.scss").read_text()
        states = FOUNDATIONS["modes"][mode]["states"]
        for callout, state in [
            ("note", "info"),
            ("tip", "success"),
            ("warning", "warning"),
            ("important", "danger"),
            ("caution", "danger"),
        ]:
            assert f'$callout-color-{callout}: {states[state]["ink"]} !default;' in text
    assert "css: foundations.css" in (EXT / "_extension.yml").read_text()
    assert "Bootstrap v" not in (EXT / "foundations.css").read_text()


def test_semantic_actions_and_outline_neutral_keep_approved_pairs():
    spec = importlib.util.spec_from_file_location(
        "foundation_support", ROOT / "scripts/foundations.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    css = (EXT / "foundations.css").read_text()
    fixture = (ROOT / "example/pages/foundations.qmd").read_text()
    for name in ["success", "warning", "danger", "info"]:
        rule = helper.semantic_button_rules(name)
        assert f"html .btn-{name},html .btn-outline-{name}" in rule
        assert f"color:var(--f-{name}-ink)" in rule
        assert f"background-color:var(--f-{name}-fill)" in rule
        assert "border-color:var(--f-control-boundary)" in rule
        assert ":not(:disabled):not(.disabled):not([aria-disabled=true]):hover" in rule
        assert ":focus-visible" in rule and "outline:2px solid var(--f-focus)" in rule
        for mode in FOUNDATIONS["modes"].values():
            state = mode["states"][name]
            assert contrast(state["ink"], state["fill"]) >= 5
            for surface in ["paper", "panel", "code"]:
                assert (
                    contrast(state["ink"], mode["swatches"][mode["roles"][surface]])
                    >= 5
                )
        for identifier in [
            f"reading-{name}",
            f"reading-outline-{name}",
            f"reading-disabled-{name}",
        ]:
            assert f'id="{identifier}"' in fixture
    assert "html .btn-outline-secondary" in css
    assert "background-color:transparent" in css
    assert css.rfind("html .btn:disabled") > css.rfind(
        "html .btn-outline-info:focus-visible"
    )
    assert "box-shadow:none" in css and "text-decoration:none" in css
