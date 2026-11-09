/* Ripple landing interaction: no login, no paid Clocked requests. */
(() => {
  const root = document.documentElement;
  const themeButton = document.querySelector('#landing-theme');
  const themeLabel = document.querySelector('#landing-theme-label');
  const setTheme = theme => {
    root.dataset.theme = theme;
    themeButton.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    themeLabel.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    try { localStorage.setItem('ripple-theme', theme); } catch (_) {}
  };
  setTheme(root.dataset.theme === 'dark' ? 'dark' : 'light');
  themeButton.addEventListener('click', () => setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'));

  const previous = document.querySelector('#lp-version-old');
  const current = document.querySelector('#lp-version-new');
  const container = document.querySelector('#lp-applicant-dots');
  const note = document.querySelector('#lp-demo-note');
  let demo = null;
  let version = 'old';
  const currency = new Intl.NumberFormat('en-US', {style: 'currency', currency:'USD', maximumFractionDigits:0});

  const paint = () => {
    previous.classList.toggle('is-selected', version === 'old');
    current.classList.toggle('is-selected', version === 'new');
    previous.setAttribute('aria-pressed', String(version === 'old'));
    current.setAttribute('aria-pressed', String(version === 'new'));
    if (!demo) return;
    const policy = demo.policies[version];
    document.querySelector('#lp-preview-gpa').textContent = Number(policy.min_gpa).toFixed(2);
    document.querySelector('#lp-preview-income').textContent = currency.format(policy.max_income);
    const eligible = demo.impact.cases.filter(c => c[version].status === 'eligible').length;
    document.querySelector('#lp-eligibility-count').textContent = `${eligible} / ${demo.impact.cases.length} eligible`;
    container.replaceChildren();
    demo.impact.cases.forEach(c => {
      const el = document.createElement('span');
      el.className = `lp-applicant-dot ${c[version].status === 'eligible' ? 'is-eligible' : 'is-ineligible'}`;
      el.title = `${c.name}: ${c[version].status} under ${version === 'old' ? 'previous' : 'updated'} policy`;
      el.setAttribute('aria-label', el.title);
      el.setAttribute('role', 'img');
      container.append(el);
    });
    note.textContent = version === 'old' ? 'Original requirements: a 3.2 GPA and $50,000 income ceiling.' :
      `Updated policy: ${demo.impact.counts.lost} lost and ${demo.impact.counts.gained} gained eligibility across the same fictional applicants.`;
  };
  previous.addEventListener('click', () => { version='old'; paint(); });
  current.addEventListener('click', () => { version='new'; paint(); });
  fetch('/api/demo', {cache: 'no-store'})
    .then(res => { if (!res.ok) throw new Error('demo unavailable'); return res.json(); })
    .then(data => {if (!data?.impact?.cases?.length || !data.policies?.new || !data.policies?.old) throw new Error('invalid demo'); demo=data; paint();})
    .catch(() => {note.textContent = 'The demo preview is temporarily unavailable. Open the Studio to explore the full model.'; document.querySelector('#lp-eligibility-count').textContent='Preview unavailable';});
})();