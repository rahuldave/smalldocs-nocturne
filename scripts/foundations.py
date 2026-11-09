"""Generate explicit foundation CSS from this repository's authoritative manifest."""

import json
from pathlib import Path


def load(root: Path) -> tuple[dict, dict]:
    """Derive legacy flat aliases; independently authored colors live only in foundations."""
    foundation = json.loads((root / "src/foundations.json").read_text())
    theme = json.loads((root / "src/theme-info.json").read_text())
    theme.update(
        body=foundation["typography"]["fonts"]["body"],
        heading=foundation["typography"]["fonts"]["heading"],
    )
    aliases = {
        "paper": "paper",
        "ink": "ink",
        "muted": "muted",
        "panel": "panel",
        "line": "decorative-line",
        "accent": "accent-text",
        "secondary": "secondary-text",
        "code": "code",
    }
    for mode, data in foundation["modes"].items():
        theme[mode] = {
            key: data["swatches"][data["roles"][role]] for key, role in aliases.items()
        }
    (root / "src/theme.json").write_text(json.dumps(theme, indent=2) + "\n")
    return foundation, theme


def rgb(color: str) -> str:
    return ", ".join(str(int(color[i : i + 2], 16)) for i in (1, 3, 5))


def palette(foundation: dict, mode: str) -> str:
    """Emit opaque role values and Bootstrap state aliases, without Bootstrap CSS."""
    data = foundation["modes"][mode]
    colors = {key: data["swatches"][ref] for key, ref in data["roles"].items()}
    lines = [f"--f-{key}: {value};" for key, value in colors.items()]
    mappings = {
        "body-bg": "paper",
        "body-color": "ink",
        "emphasis-color": "ink",
        "heading-color": "ink",
        "secondary-color": "muted",
        "secondary-bg": "panel",
        "tertiary-bg": "panel",
        "link-color": "accent-text",
        "link-hover-color": "link-hover",
        "primary": "primary-fill",
        "border-color": "decorative-line",
        "code-color": "code-ink",
        "primary-text-emphasis": "accent-text",
        "primary-bg-subtle": "panel",
        "primary-border-subtle": "control-boundary",
    }
    for key, role in mappings.items():
        lines += [
            f"--bs-{key}: {colors[role]};",
            f"--bs-{key}-rgb: {rgb(colors[role])};",
        ]
    lines += [
        "--bs-border-color-translucent: var(--f-decorative-line);",
        "--bs-focus-ring-color: var(--f-focus);",
    ]
    for name, state in data["states"].items():
        for role in ["fill", "ink", "boundary"]:
            lines.append(f"--f-{name}-{role}: {state[role]};")
        lines += [
            f'--bs-{name}: {state["boundary"]};',
            f'--bs-{name}-rgb: {rgb(state["boundary"])};',
            f'--bs-{name}-text-emphasis: {state["ink"]};',
            f'--bs-{name}-bg-subtle: {state["fill"]};',
            f'--bs-{name}-border-subtle: {state["boundary"]};',
        ]
    menu = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 30 30'><path stroke='%23{colors['ink'][1:]}' stroke-width='2' stroke-linecap='round' d='M4 7h22M4 15h22M4 23h22'/></svg>"
    lines.append(f'--f-menu-image: url("data:image/svg+xml,{menu}");')
    return ":root, [data-bs-theme] {\n  " + "\n  ".join(lines) + "\n}\n"


def rules(foundation: dict) -> str:
    """Apply reading hierarchy and semantic controls equally to both renderers."""
    fonts = foundation["typography"]["fonts"]
    radius = foundation["shape"]["radius"] / 16
    variables = [f"--f-font-{key}: {value};" for key, value in fonts.items()]
    variables += [
        f"--f-size-{n}: {n/16:g}rem;" for n in foundation["typography"]["scale"]
    ]
    variables += [
        f"--f-space-{n}: {n/16:g}rem;" for n in foundation["spacing"]["scale"]
    ]
    reading = foundation["typography"]["profiles"]["reading"]
    variables += [
        f"--f-reading-{key}: {value/16:g}rem;" for key, value in reading.items()
    ]
    variables += [
        f"--f-line-{key}: {value:g};"
        for key, value in foundation["typography"]["lineHeights"].items()
    ]
    variables += [
        f"--f-reading-space-{key}: {value/16:g}rem;"
        for key, value in foundation["spacing"]["profiles"]["reading"].items()
    ]
    return (
        ":root, [data-bs-theme] {\n  "
        + "\n  ".join(variables)
        + f" --bs-border-radius:{radius:g}rem; --bs-border-radius-sm:{radius:g}rem; --bs-border-radius-lg:{radius:g}rem; --bs-font-sans-serif:var(--f-font-ui); --bs-body-font-family:var(--f-font-body); --bs-body-font-size:var(--f-reading-body); --bs-body-line-height:var(--f-line-reading);"
        + "\n}\n"
        + r"""
html:root, html.quarto-dark:root { font-size:100%; --sd-root-font-size:16px; --sd-body-width:640px; --sd-inline-code:var(--f-code-ink); --sd-code-bg:var(--f-code); }
html body { font-family:var(--f-font-body); font-size:var(--bs-body-font-size); line-height:var(--f-line-reading); color:var(--f-ink); background:var(--f-paper); font-synthesis:none; }
html main.content { padding-top:var(--f-reading-space-group); padding-bottom:var(--f-reading-space-group); }
html main.content :is(p,li) { line-height:var(--f-line-reading); }
html main.content p { margin-bottom:var(--f-reading-space-paragraph); }
html main.content :is(h1,h2,h3,h4,h5,h6) { font-family:var(--f-font-heading); color:var(--f-ink); font-weight:400; line-height:var(--f-line-heading); letter-spacing:normal; }
html main.content h1,html .quarto-title h1.title { font-weight:400; font-family:var(--f-font-heading); font-size:var(--f-reading-title); line-height:var(--f-line-heading); color:var(--f-ink); margin-bottom:var(--f-reading-space-paragraph); }
html main.content h2 { font-size:var(--f-reading-heading); margin:var(--f-space-48) 0 var(--f-space-16); }
html main.content h3 { font-size:var(--f-size-24); margin:var(--f-space-32) 0 var(--f-space-12); }
html main.content :is(h4,h5,h6) { font-size:var(--f-size-20); margin:var(--f-space-32) 0 var(--f-space-12); }
html .editorial-display,html main.content .editorial-display { font-family:var(--f-font-display); font-size:var(--f-reading-display); line-height:var(--f-line-display); font-weight:400; }
html :is(.navbar,.sidebar-navigation,.btn,.form-label,.form-control,.form-select,.form-check-label,.nav-link,.breadcrumb,.pagination-link,.footer) { font-family:var(--f-font-ui); font-size:var(--f-reading-ui); line-height:var(--f-line-ui); }
html .navbar-title { font-family:var(--f-font-ui); font-size:var(--f-size-20); }
html :is(.quarto-title-meta,.quarto-title-meta-heading,.quarto-category,.listing-category,figcaption,.quarto-figure figcaption,.footnotes,.column-margin,.margin-aside,.metadata,.code-with-filename-file pre,.sidebar-item-section > .sidebar-item-container .sidebar-link) { font-family:var(--f-font-ui); font-size:var(--f-reading-metadata); line-height:var(--f-line-ui); color:var(--f-muted); }
html .quarto-navbar-tools .smalldocs-search input { font-size:var(--f-reading-ui); padding-left:var(--f-space-32); }
html .quarto-title .subtitle { font-family:var(--f-font-body); font-size:var(--bs-body-font-size); line-height:var(--f-line-reading); color:var(--f-muted); }
html :is(pre,code,kbd,samp) { font-family:var(--f-font-code); }
html pre,html pre code,html :not(pre)>code { font-size:var(--f-reading-code); line-height:var(--f-line-code); color:var(--f-code-ink); }
html :is(div.sourceCode,pre) { background:var(--f-code); border-radius:var(--bs-border-radius); box-shadow:none; }
html div.sourceCode { padding:var(--f-reading-space-panel); margin:var(--f-space-24) 0; }
html div.sourceCode > pre.sourceCode { padding:0; margin:0; }
html .code-with-filename-file pre { padding:var(--f-space-8) var(--f-space-16); font-family:var(--f-font-code); font-size:var(--f-reading-metadata); line-height:var(--f-line-ui); }
html hr { margin:var(--f-reading-space-group) 0; }
html main.content blockquote { margin:var(--f-space-32) 0; padding:0 0 0 var(--f-space-24); }
html #TOC #toc-title { font-family:var(--f-font-ui); font-size:var(--f-reading-ui); line-height:var(--f-line-ui); letter-spacing:normal; text-transform:none; margin-bottom:var(--f-space-16); }
html .sidebar nav[role=doc-toc] > h2,html .nav-footer { font-family:var(--f-font-ui); font-size:var(--f-reading-metadata); }
html a { color:var(--f-accent-text); }
html a:hover { color:var(--f-link-hover); }
html :is(a,button,input,select,textarea,summary,[tabindex]):focus-visible { outline:2px solid var(--f-focus); outline-offset:4px; box-shadow:none; }
html :is(.form-control,.form-select,.form-check-input) { color:var(--f-ink); background-color:var(--f-paper); border:1px solid var(--f-control-boundary); border-radius:var(--bs-border-radius); }
html :is(.form-control,.form-select,.form-check-input):focus { border-color:var(--f-control-boundary); outline:2px solid var(--f-focus); outline-offset:4px; box-shadow:none; }
html .btn { font-size:var(--f-reading-ui); border-radius:var(--bs-border-radius); padding:.5rem 1rem; box-shadow:none; }
html .btn-primary { --bs-btn-bg:var(--f-primary-fill); --bs-btn-color:var(--f-button-ink); --bs-btn-border-color:var(--f-primary-fill); --bs-btn-hover-bg:var(--f-primary-hover-fill); --bs-btn-hover-color:var(--f-primary-hover-ink); --bs-btn-hover-border-color:var(--f-primary-hover-fill); --bs-btn-active-bg:var(--f-primary-hover-fill); --bs-btn-active-color:var(--f-primary-hover-ink); --bs-btn-active-border-color:var(--f-primary-hover-fill); }
html .btn-outline-primary { --bs-btn-color:var(--f-accent-text); --bs-btn-border-color:var(--f-control-boundary); --bs-btn-hover-bg:var(--f-primary-fill); --bs-btn-hover-color:var(--f-button-ink); --bs-btn-hover-border-color:var(--f-primary-fill); --bs-btn-active-bg:var(--f-primary-fill); --bs-btn-active-color:var(--f-button-ink); }
html .btn-secondary { --bs-btn-color:var(--f-secondary-action); --bs-btn-bg:var(--f-panel); --bs-btn-border-color:var(--f-control-boundary); --bs-btn-hover-color:var(--f-secondary-action); --bs-btn-hover-bg:var(--f-paper); --bs-btn-hover-border-color:var(--f-control-boundary); --bs-btn-active-bg:var(--f-panel); --bs-btn-active-color:var(--f-secondary-action); }
html :is(.btn:disabled,.btn.disabled,.btn[aria-disabled=true],.form-control:disabled,.form-select:disabled,.form-check-input:disabled) { opacity:1; color:var(--f-disabled-ink); background-color:var(--f-disabled-fill); border-color:var(--f-control-boundary); --bs-btn-disabled-opacity:1; --bs-btn-disabled-color:var(--f-disabled-ink); --bs-btn-disabled-bg:var(--f-disabled-fill); --bs-btn-disabled-border-color:var(--f-control-boundary); }
html .form-check-input:disabled ~ .form-check-label { opacity:1; color:var(--f-disabled-ink); }
html .form-check-input:checked,html .form-check-input:indeterminate { background-color:var(--f-selected-fill); border-color:var(--f-selected-fill); }
html .navbar .nav-link.active,html .navbar .nav-link[aria-current=page],html .panel-tabset .nav-link.active,html :is(.nav-link[aria-selected=true],.nav-link[aria-current=page],.sidebar-link.active) { background:var(--f-selected-fill); color:var(--f-selected-ink); text-decoration:underline; text-underline-offset:.2em; border-color:var(--f-control-boundary); }
html .table { --bs-table-color:var(--f-ink); --bs-table-bg:transparent; --bs-table-striped-bg:var(--f-panel); --bs-table-striped-color:var(--f-ink); }
html main.content table { font-family:var(--f-font-ui); font-size:var(--f-reading-ui); line-height:var(--f-line-ui); }
html .table th { color:var(--f-ink); }
html :is(.card,.callout) { box-shadow:none; border-radius:var(--bs-border-radius); }
html .card { padding:0; }
html .card-body { padding:var(--f-reading-space-panel); }
html .callout { margin:var(--f-reading-space-group) 0; }
html .callout-body { padding:var(--f-reading-space-panel); }
html .callout-header { font-family:var(--f-font-ui); font-size:var(--f-reading-ui); padding:var(--f-space-12) var(--f-reading-space-panel); }
html main.content .callout :is(p,li) { color:inherit; font-size:var(--bs-body-font-size); }
html .callout-title-container { color:inherit; }
html .form-control.is-invalid,html .form-select.is-invalid,html [aria-invalid=true] { border:2px solid var(--f-danger-boundary); color:var(--f-ink); background-color:var(--f-paper); }
html .invalid-feedback { color:var(--f-danger-ink); background:var(--f-danger-fill); padding:.5rem; font-family:var(--f-font-ui); font-size:var(--f-reading-ui); }


html body #quarto-content main.content { width:100%; max-width:640px; margin-inline:auto; padding-top:var(--f-reading-space-group); padding-bottom:var(--f-reading-space-group); }
html body #quarto-content .callout.callout-style-default .callout-header { font-family:var(--f-font-ui); font-size:var(--f-reading-ui); line-height:var(--f-line-ui); padding:var(--f-space-12) var(--f-reading-space-panel); }
html body #quarto-content .callout.callout-style-default .callout-body-container :is(p,li) { padding:0; }
html body #quarto-content .callout.callout-style-default .callout-body-container { font-family:var(--f-font-body); font-size:var(--f-reading-body); line-height:var(--f-line-reading); padding:var(--f-reading-space-panel); }
html .form-control,html .form-select { padding:var(--f-space-8) var(--f-space-12); }
html .form-select,html .form-control.is-invalid,html .form-select.is-invalid { padding-right:var(--f-space-32); }

html body #quarto-content #TOC .nav-link { color:var(--f-muted); background:transparent; font-family:var(--f-font-ui); font-size:var(--f-reading-ui); line-height:var(--f-line-ui); padding:var(--f-space-4) var(--f-space-12); }
html body #quarto-content #TOC ul ul .nav-link { padding-left:var(--f-space-24); }
html body #quarto-content #TOC .nav-link.active { color:var(--f-accent-text); text-decoration:underline; background:transparent; }
html body #quarto-header .navbar .nav-link.active,html body #quarto-header .navbar .nav-link[aria-current=page] { color:var(--f-selected-ink); background:var(--f-selected-fill); text-decoration:underline; }
html body #quarto-header .navbar .navbar-toggler-icon { background-image:var(--f-menu-image); }
html body #quarto-content :is(.form-control,.form-select,.form-check-input):focus,html body #quarto-content .btn:focus-visible { outline:2px solid var(--f-focus); outline-offset:4px; box-shadow:none; }
html body #quarto-header .quarto-color-scheme-toggle,html body #quarto-header .quarto-color-scheme-toggle .bi,html body #quarto-header .aa-SubmitIcon,html body #quarto-header .aa-SubmitIcon *,html body #quarto-header .aa-DetachedSearchButtonIcon { color:var(--f-ink); fill:var(--f-ink); opacity:1; }
html body #quarto-content pre { font-family:var(--f-font-code); font-size:var(--f-reading-code); line-height:var(--f-line-code); color:var(--f-code-ink); padding:var(--f-reading-space-panel); }
html body #quarto-content pre code { font-family:var(--f-font-code); font-size:var(--f-reading-code); line-height:var(--f-line-code); color:var(--f-code-ink); padding:0; }
html body #quarto-content div.sourceCode { padding:var(--f-reading-space-panel); }
html body #quarto-content div.sourceCode :is(pre,code,span) { font-family:var(--f-font-code); font-size:var(--f-reading-code); line-height:var(--f-line-code); }
html body #quarto-content div.sourceCode :is(pre,code) { padding:0; margin:0; }
html body #quarto-content .code-with-filename-file pre { font-family:var(--f-font-code); font-size:var(--f-reading-metadata); line-height:var(--f-line-ui); padding:var(--f-space-8) var(--f-space-16); }

/* Complete component jobs: later shell-specific selectors must not shrink them. */
html .navbar .nav-link,html .sidebar-navigation .sidebar-link,html .panel-tabset .nav-link { font-weight:400; font-size:var(--f-reading-ui); line-height:var(--f-line-ui); font-family:var(--f-font-ui); }
html .navbar .nav-link { padding:var(--f-space-8) var(--f-space-16); }
html .quarto-post .listing-title { font-weight:400; font-size:var(--f-reading-heading); line-height:var(--f-line-heading); font-family:var(--f-font-heading); color:var(--f-ink); }
html .quarto-post .listing-description { font-size:var(--f-reading-body); line-height:var(--f-line-reading); }
html .quarto-grid-item .card-title { font-weight:400; font-size:var(--f-size-24); line-height:var(--f-line-heading); font-family:var(--f-font-heading); color:var(--f-ink); }
html .table td,html .table th { padding:var(--f-space-12) var(--f-space-16); }
html .panel-tabset .tab-content,html .code-with-filename-file { border-radius:var(--bs-border-radius); }
html .quarto-title-block { padding-bottom:var(--f-space-24); margin-bottom:var(--f-space-32); }
html .quarto-title::after { margin-top:var(--f-space-24); }
html .callout .callout-body-container,html .callout .callout-body { font-family:var(--f-font-body); font-size:var(--f-reading-body); line-height:var(--f-line-reading); padding:var(--f-reading-space-panel); }
html .navbar { --bs-navbar-color:var(--f-ink); --bs-navbar-hover-color:var(--f-link-hover); --bs-navbar-active-color:var(--f-accent-text); --bs-navbar-brand-color:var(--f-accent-text); --bs-navbar-brand-hover-color:var(--f-link-hover); --bs-navbar-toggler-border-color:var(--f-control-boundary); }
html .navbar .navbar-toggler { color:var(--f-ink); border-color:var(--f-control-boundary); }
html .navbar .navbar-toggler-icon { background-image:var(--f-menu-image); }
html .quarto-navbar-tools :is(a,button),html .quarto-color-scheme-toggle,html .navbar .aa-DetachedSearchButton { color:var(--f-ink); background-color:transparent; }
html .btn-primary { color:var(--f-button-ink); background-color:var(--f-primary-fill); border-color:var(--f-primary-fill); }
html .btn-primary:hover,html .btn-primary:active { color:var(--f-primary-hover-ink); background-color:var(--f-primary-hover-fill); border-color:var(--f-primary-hover-fill); }
html .btn-secondary { color:var(--f-secondary-action); background-color:var(--f-panel); border-color:var(--f-control-boundary); }
html .btn-secondary:hover,html .btn-secondary:active { color:var(--f-secondary-action); background-color:var(--f-paper); border-color:var(--f-control-boundary); }
html .btn:disabled,html .btn.disabled { color:var(--f-disabled-ink); background-color:var(--f-disabled-fill); border-color:var(--f-control-boundary); opacity:1; }

html #quarto-content:not(.page-columns) { --sd-pad:var(--f-reading-space-outer); }
@media(max-width:575.98px) {
  html #quarto-content:not(.page-columns) { --sd-pad:var(--f-reading-space-narrowOuter); }
  html body #quarto-content main.content { padding-inline:0; margin-inline:0; }
  html #quarto-content.page-columns { display:block; padding-inline:var(--f-reading-space-narrowOuter); }
  html .quarto-title h1.title { font-size:var(--f-reading-title); }
}
"""
        + "\n".join(
            state_rules(name, callout)
            for name, callout in [
                ("success", "tip"),
                ("warning", "warning"),
                ("danger", "important"),
                ("danger", "caution"),
                ("info", "note"),
            ]
        )
        + "\n"
        + "\n".join(
            semantic_button_rules(state)
            for state in ["success", "warning", "danger", "info"]
        )
        + "\n"
        + additional_action_rules()
    )


def state_rules(name: str, callout: str) -> str:
    """State words remain authored content; CSS supplies consistent non-brand colors."""
    return f"""html .alert-{name},html .callout-{callout} {{ --bs-alert-color:var(--f-{name}-ink); --bs-alert-bg:var(--f-{name}-fill); --bs-alert-border-color:var(--f-{name}-boundary); --sd-callout:var(--f-{name}-boundary); color:var(--f-{name}-ink); background:var(--f-{name}-fill); border-color:var(--f-{name}-boundary); }}
html body #quarto-content .callout.callout-{callout} {{ border-color:var(--f-{name}-boundary); }}
html body #quarto-content .callout.callout-style-default.callout-{callout} .callout-header {{ color:var(--f-{name}-ink); background:var(--f-{name}-fill); }}
html body #quarto-content .callout.callout-{callout} .callout-body {{ color:var(--f-ink); background:var(--f-paper); }}"""


def semantic_button_rules(state: str) -> str:
    """Bind filled/outline semantic actions to tested states and a meaningful edge.

    The neutral control boundary identifies the outer edge on paper/panel/code;
    decorative state boundaries are only reserved against their own state fills.
    """
    selectors = f"html .btn-{state},html .btn-outline-{state}"
    variables = " ".join(
        f"--bs-btn-{prefix}{role}:var(--f-{token});"
        for prefix in ["", "hover-", "active-"]
        for role, token in [
            ("color", f"{state}-ink"),
            ("bg", f"{state}-fill"),
            ("border-color", "control-boundary"),
        ]
    )
    enabled = ":not(:disabled):not(.disabled):not([aria-disabled=true])"
    return f"""{selectors} {{ {variables} color:var(--f-{state}-ink); background-color:var(--f-{state}-fill); border-color:var(--f-control-boundary); }}
html .btn-outline-{state} {{ background-color:transparent; }}
html .btn-{state}{enabled}:hover,html .btn-outline-{state}{enabled}:hover,
html .btn-{state}{enabled}:active,html .btn-outline-{state}{enabled}:active,
html .btn-{state}.active,html .btn-outline-{state}.active {{ color:var(--f-{state}-ink); background-color:var(--f-{state}-fill); border-color:var(--f-control-boundary); text-decoration:underline; }}
html .btn-{state}:focus-visible,html .btn-outline-{state}:focus-visible {{ outline:2px solid var(--f-focus); outline-offset:4px; box-shadow:none; }}"""


def additional_action_rules() -> str:
    """Cover neutral outlines and keep disabled actions opaque in every variant."""
    return r"""html .btn-outline-secondary { --bs-btn-color:var(--f-secondary-action); --bs-btn-bg:transparent; --bs-btn-border-color:var(--f-control-boundary); --bs-btn-hover-color:var(--f-secondary-action); --bs-btn-hover-bg:var(--f-panel); --bs-btn-hover-border-color:var(--f-control-boundary); --bs-btn-active-color:var(--f-secondary-action); --bs-btn-active-bg:var(--f-panel); --bs-btn-active-border-color:var(--f-control-boundary); color:var(--f-secondary-action); background-color:transparent; border-color:var(--f-control-boundary); }
html .btn-outline-secondary:not(:disabled):not(.disabled):not([aria-disabled=true]):hover,html .btn-outline-secondary:not(:disabled):not(.disabled):not([aria-disabled=true]):active,html .btn-outline-secondary.active { color:var(--f-secondary-action); background-color:var(--f-panel); border-color:var(--f-control-boundary); text-decoration:underline; }
html .btn-outline-secondary:focus-visible { outline:2px solid var(--f-focus); outline-offset:4px; box-shadow:none; }
html .btn:disabled,html .btn.disabled,html .btn[aria-disabled=true] { --bs-btn-disabled-opacity:1; --bs-btn-disabled-color:var(--f-disabled-ink); --bs-btn-disabled-bg:var(--f-disabled-fill); --bs-btn-disabled-border-color:var(--f-control-boundary); color:var(--f-disabled-ink); background-color:var(--f-disabled-fill); border-color:var(--f-control-boundary); opacity:1; text-decoration:none; }"""
