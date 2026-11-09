/** Read-only metrics plus real mode-button clicks through CUA.
 * First run `just foundation-fixtures` and serve example/_site.
 * Call checkFoundationsBrowser(tab, baseURL, parsedFoundationsManifest).
 * Returns all failures rather than stopping at the first mismatch. This covers
 * solid computed styles, real forms and mode gestures. Font resource loading and
 * real narrow iframe layouts are manual package/resource and AX/screenshot gates.
 */
export async function checkFoundationsBrowser(tab, base, foundation) {
  const failures = [];
  const snapshots = [];
  const rgb = hex => `rgb(${[1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)).join(', ')})`;
  const check = (condition, message) => { if (!condition) failures.push(message); };
  const expectedColor = (mode, role) => {
    const data = foundation.modes[mode];
    return rgb(data.swatches[data.roles[role]]);
  };
  const collect = () => tab.playwright.evaluate(() => {
    const style = selector => {
      const node = document.querySelector(selector);
      if (!node) return null;
      const s = getComputedStyle(node);
      return {font: s.fontFamily, size: s.fontSize, weight: s.fontWeight, line: s.lineHeight,
        color: s.color, bg: s.backgroundColor, padding: [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft],
        opacity: s.opacity, fill: s.fill, border: s.borderTopColor, width: node.getBoundingClientRect().width};
    };
    const states = ['note', 'tip', 'warning', 'important', 'caution'].map(name => ({
      name, header: style(`.callout-${name} .callout-header`), body: style(`.callout-${name} .callout-body`),
      paragraph: style(`.callout-${name} .callout-body p`),
    }));
    const actions = ['success', 'warning', 'danger', 'info'].map(name => ({name, filled: style(`#reading-${name}`), outline: style(`#reading-outline-${name}`), disabled: style(`#reading-disabled-${name}`)}));
    const modeGlyph = document.querySelector('.quarto-color-scheme-toggle .bi');
    const modeGlyphBackground = modeGlyph ? getComputedStyle(modeGlyph, '::before').backgroundImage : null;
    return {modeGlyphBackground, modeGlyph: style('.quarto-color-scheme-toggle .bi'), searchGlyph: style('.aa-SubmitIcon'), actions, outlineSecondary: style('#reading-outline-secondary'), root: getComputedStyle(document.documentElement).fontSize,
      body: style('body'), code: style('main.content pre'), codeInner: style('pre.sourceCode code.sourceCode'), codeSpan: style('pre.sourceCode span'), codePanel: style('div.sourceCode'), title: style('h1.title'), display: style('.editorial-display'), metadata: style('.metadata'),
      main: style('main.content'), input: style('#reading-name'), primary: style('#reading-primary'),
      secondary: style('#reading-secondary'), table: style('main.content td'), toc: style('#TOC .nav-link'),
      card: style('.card'), cardBody: style('.card-body'), disabled: style('#reading-disabled-button'), states,
      errorAssociated: document.querySelector('#reading-error')?.getAttribute('aria-describedby') === 'reading-error-message',
      nativeDisabled: document.querySelector('#reading-disabled-button')?.disabled,
      overflow: document.documentElement.scrollWidth > innerWidth,
    };
  });
  for (const renderer of ['smalldocs', 'quarto']) {
    const path = renderer === 'smalldocs' ? '/pages/foundations.html?mode=light' : '/quarto-foundations/index.html';
    await tab.goto(base + path);
    await tab.getAXState({emit: false});
    for (const mode of ['light', 'dark']) {
      let metrics = await collect();
      if (metrics.body?.bg !== expectedColor(mode, 'paper')) {
        await tab.playwright.locator('.quarto-color-scheme-toggle').click();
        await tab.getAXState({emit: false});
        metrics = await collect();
      }
      const prefix = `${foundation.theme}/${renderer}/${mode}`;
      const profile = foundation.typography.profiles.reading;
      const bodyLine = `${profile.body * foundation.typography.lineHeights.reading}px`;
      const uiLine = `${profile.ui * foundation.typography.lineHeights.ui}px`;
      check(metrics.root === '16px', `${prefix}: root 16`);
      check(metrics.body?.bg === expectedColor(mode, 'paper'), `${prefix}: mode paper`);
      check(metrics.body?.size === `${profile.body}px` && metrics.body?.line === bodyLine, `${prefix}: body size/line`);
      check(metrics.body?.color === expectedColor(mode, 'ink'), `${prefix}: body ink`);
      check(metrics.modeGlyph?.color === expectedColor(mode, 'ink'), `${prefix}: mode child glyph color`);
      if (renderer === 'quarto') {
        check(metrics.searchGlyph?.color === expectedColor(mode, 'ink') && metrics.searchGlyph?.fill === expectedColor(mode, 'ink'), `${prefix}: search child SVG color/fill`);
        const components = expectedColor(mode, 'ink').replace('rgb(', '').replace(')', '').replaceAll(' ', '');
        const image = decodeURIComponent(metrics.modeGlyphBackground ?? '').replaceAll(' ', '');
        check(image.includes(`rgba(${components},1)`) || image.includes(`rgb(${components})`), `${prefix}: embedded mode SVG paint`);
      }
      check(metrics.input?.color === expectedColor(mode, 'ink') && metrics.input?.bg === expectedColor(mode, 'paper'), `${prefix}: input pair`);
      check(metrics.primary?.color === expectedColor(mode, 'button-ink') && metrics.primary?.bg === expectedColor(mode, 'primary-fill'), `${prefix}: primary pair`);
      check(metrics.secondary?.color === expectedColor(mode, 'secondary-action'), `${prefix}: neutral secondary ink`);
      check([expectedColor(mode, 'muted'), expectedColor(mode, 'accent-text')].includes(metrics.toc?.color), `${prefix}: opaque TOC ink`);
      check(metrics.code?.size === `${profile.code}px` && metrics.code?.line === `${profile.code * foundation.typography.lineHeights.code}px`, `${prefix}: code size/line`);
      for (const part of ['code', 'codeInner', 'codeSpan']) {
        check(metrics[part]?.size === `${profile.code}px` && metrics[part]?.line === `${profile.code * foundation.typography.lineHeights.code}px`, `${prefix}: ${part} code size/line`);
      }
      check(metrics.code?.padding.every(v => v === '0px') && metrics.codeInner?.padding.every(v => v === '0px') && metrics.codePanel?.padding.every(v => v === '24px'), `${prefix}: single code panel padding`);
      check(metrics.code?.color === expectedColor(mode, 'code-ink') && metrics.codeInner?.color === expectedColor(mode, 'code-ink'), `${prefix}: code base ink`);
      check(metrics.title?.size === `${profile.title}px` && metrics.title?.weight === '400', `${prefix}: title size/weight`);
      check(metrics.display?.size === `${profile.display}px` && metrics.display?.weight === '400', `${prefix}: display`);
      check(metrics.metadata?.size === `${profile.metadata}px`, `${prefix}: metadata`);
      check(metrics.main?.width <= 641, `${prefix}: 640 maximum measure`);
      for (const role of ['input', 'primary', 'secondary', 'table', 'toc']) {
        check(metrics[role]?.size === `${profile.ui}px` && metrics[role]?.line === uiLine, `${prefix}: ${role} UI size/line`);
      }
      check(metrics.input?.padding.join('/') === '8px/12px/8px/12px', `${prefix}: input spacing`);
      check(metrics.card?.padding.every(v => v === '0px') && metrics.cardBody?.padding.every(v => v === '24px'), `${prefix}: one card padding boundary`);
      check(metrics.nativeDisabled && metrics.disabled?.opacity === '1' && metrics.errorAssociated, `${prefix}: disabled/error semantics`);
      const mapping = {note: 'info', tip: 'success', warning: 'warning', important: 'danger', caution: 'danger'};
      for (const state of metrics.states) {
        const expected = foundation.modes[mode].states[mapping[state.name]];
        check(state.header?.size === `${profile.ui}px` && state.header?.line === uiLine && state.header?.padding.join('/') === '12px/24px/12px/24px', `${prefix}: ${state.name} header type/spacing`);
        check(state.body?.size === `${profile.body}px` && state.body?.line === bodyLine && state.body?.padding.every(v => v === '24px'), `${prefix}: ${state.name} body type/spacing`);
        check(state.header?.color === rgb(expected.ink) && state.header?.bg === rgb(expected.fill), `${prefix}: ${state.name} header pair`);
        check(state.body?.color === expectedColor(mode, 'ink') && state.body?.bg === expectedColor(mode, 'paper'), `${prefix}: ${state.name} body pair`);
        check(state.paragraph?.padding.every(v => v === '0px'), `${prefix}: ${state.name} child padding`);
      }
      const fontJobs = {body: metrics.body?.font, display: metrics.display?.font, ui: metrics.input?.font, code: metrics.code?.font};
      for (const [job, actual] of Object.entries(fontJobs)) {
        const family = foundation.typography.fonts[job].split(',')[0].replaceAll('"', '').trim();
        check(actual?.includes(family), `${prefix}: computed ${job} font family`);
      }
      for (const action of metrics.actions) {
        const state = foundation.modes[mode].states[action.name];
        check(action.filled?.color === rgb(state.ink) && action.filled?.bg === rgb(state.fill), `${prefix}: ${action.name} action pair`);
        check(action.outline?.color === rgb(state.ink) && ['rgba(0, 0, 0, 0)', 'transparent'].includes(action.outline?.bg), `${prefix}: ${action.name} outline pair`);
        check(action.filled?.border === expectedColor(mode, 'control-boundary') && action.outline?.border === expectedColor(mode, 'control-boundary'), `${prefix}: ${action.name} meaningful edge`);
        check(action.disabled?.color === expectedColor(mode, 'disabled-ink') && action.disabled?.bg === expectedColor(mode, 'disabled-fill') && action.disabled?.opacity === '1', `${prefix}: ${action.name} disabled pair`);
      }
      check(metrics.outlineSecondary?.color === expectedColor(mode, 'secondary-action'), `${prefix}: neutral outline ink`);
      await tab.playwright.locator('#reading-name').fill('Foundation input checked');
      await tab.playwright.locator('#reading-select').selectOption({label: 'Notebook'});
      await tab.playwright.locator('#reading-checked').uncheck();
      await tab.getAXState({emit: false});
      const form = await tab.playwright.evaluate(() => ({name: document.querySelector('#reading-name').value, selected: document.querySelector('#reading-select').value, checked: document.querySelector('#reading-checked').checked}));
      check(form.name === 'Foundation input checked' && form.selected === 'Notebook' && !form.checked, `${prefix}: real entry/select/checkbox`);
      await tab.playwright.locator('#reading-checked').check();
      await tab.playwright.locator('#reading-select').selectOption({label: 'Article'});
      await tab.playwright.locator('#reading-name').fill('Readable input');
      await tab.playwright.locator('#reading-name').press('Tab');
      await tab.getAXState({emit: false});
      const focus = await tab.playwright.evaluate(() => {
        const node = document.activeElement;
        const style = getComputedStyle(node);
        return {id: node.id, color: style.outlineColor, width: style.outlineWidth, offset: style.outlineOffset, shadow: style.boxShadow};
      });
      check(focus.id === 'reading-error' && focus.color === expectedColor(mode, 'focus') && focus.width === '2px' && focus.offset === '4px' && focus.shadow === 'none', `${prefix}: keyboard input focus`);
      check(!metrics.overflow, `${prefix}: page overflow`);
      snapshots.push({renderer, mode, metrics});
    }
    snapshots.push({renderer, manualNarrowRequired: renderer === 'smalldocs' ? base + '/qa-390.html' : base + '/qa-quarto-390.html'});
  }
  return {ok: failures.length === 0, failures, snapshots};
}
