/* Ripple self-service analysis: real uploaded PDFs, bounded temporary parsing,
   literal document comparison and deterministic scholarship-rule simulation.
   This public flow makes zero Clocked API requests; it does not claim otherwise.
*/
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const state = {files: {previous: null, updated: null}, parsed: {}, cohort: null, report: null, filter: 'all', objectURLs: {}, busy: false};
  const colors = {lost: '#d35460', gained: '#138562', retained: '#6b66d6', excluded: '#9ba5bc', review: '#d89a35'};
  const labels = {lost: 'Lost eligibility', gained: 'Gained eligibility', retained: 'Still eligible', excluded: 'Still ineligible', review: 'Needs review'};
  const usd = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', maximumFractionDigits: 0});
  const nfmt = new Intl.NumberFormat('en-US');
  let toastTimer;

  function notify(message) {
    $('#toast').textContent = message;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { $('#toast').textContent = ''; }, 4200);
  }
  function error(message) { $('#analysis-error').textContent = message; $('#analysis-error').hidden = false; $('#analysis-error').scrollIntoView({behavior: 'smooth', block: 'nearest'}); }
  function clearError() { $('#analysis-error').hidden = true; $('#analysis-error').textContent = ''; }
  function el(tag, className, content) {const node = document.createElement(tag); if (className) node.className = className; if(content !== undefined) node.textContent = String(content);return node;}
  function applyTheme(theme) {
    const root = document.documentElement;
    root.dataset.theme = theme;
    $('#theme-toggle').setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    $('#theme-toggle span').textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    try {localStorage.setItem('ripple-theme', theme);} catch (_) {}
  }
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
  $('#theme-toggle').addEventListener('click', () => applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));

  function validatePdf(file) {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) throw new Error('Choose a PDF document.');
    if (!file.size || file.size > 2 * 1024 * 1024) throw new Error('Each PDF must be smaller than 2 MB.');
  }
  function setFile(kind, file) {
    try {validatePdf(file);} catch (e) {error(`${kind === 'previous' ? 'Previous' : 'Updated'} PDF: ${e.message}`);return;}
    clearError();
    state.files[kind] = file;
    delete state.parsed[kind];
    if (state.objectURLs[kind]) URL.revokeObjectURL(state.objectURLs[kind]);
    state.objectURLs[kind] = URL.createObjectURL(file);
    const status = $(`#${kind}-status`);
    status.classList.add('success');
    status.textContent = `✓ ${file.name} · ${(file.size / 1024).toFixed(1)} KB · ready`;
    $(`#${kind}-drop strong`).textContent = file.name;
    $(`#${kind}-drop > span:not(.file-icon)`).textContent = 'Choose another PDF or drop to replace';
    $('#results').hidden = true;
  }
  for(const kind of ['previous', 'updated']) {
    $(`#${kind}-file`).addEventListener('change', event => {if(event.target.files?.[0])setFile(kind, event.target.files[0]);});
    const target = $(`#${kind}-drop`);
    ['dragenter', 'dragover'].forEach(type => target.addEventListener(type, evt => {evt.preventDefault();target.classList.add('dragging');}));
    ['dragleave', 'drop'].forEach(type => target.addEventListener(type, evt => {evt.preventDefault();target.classList.remove('dragging');}));
    target.addEventListener('drop', evt => {const f = evt.dataTransfer?.files?.[0]; if(f)setFile(kind,f);});
  }

  async function loadSamples(names = ['previous-policy.pdf', 'updated-policy.pdf']) {
    if (state.busy) return;
    clearError();
    try {
      const files = await Promise.all([['previous',names[0]],['updated',names[1]]].map(async ([kind,name]) => {
        const r = await fetch(`/assets/samples/${name}`, {cache:'no-store'});
        if (!r.ok) throw new Error('Example PDFs could not be loaded.');
        const blob = await r.blob();
        return [kind, new File([blob], name, {type:'application/pdf'})];
      }));
      files.forEach(([kind,file]) => setFile(kind,file));
      $('#workspace').scrollIntoView({behavior:'smooth',block:'start'});
      notify('Both fictional policy documents are ready to analyze.');
    } catch(e) {error(e.message);}
  }
  $('#load-samples-top').addEventListener('click', () => loadSamples());
  $('#load-judge-samples').addEventListener('click', () => loadSamples(['judge-policy-2025.pdf','judge-policy-2026.pdf']));

  function selectedCohortMode() {return $('input[name="cohort-mode"]:checked')?.value || 'sample';}
  $$('input[name="cohort-mode"]').forEach(node => node.addEventListener('change', () => {
    $('#csv-upload-group').hidden = selectedCohortMode() !== 'csv';
    if(selectedCohortMode() === 'sample')state.cohort = null;
    $('#results').hidden = true;
  }));

  // RFC 4180-style quoted field handling, including quoted newlines and commas.
  function parseCsv(text) {
    const rows = [];let cells = [], field = '', quoted = false;
    const input = text.replace(/^\uFEFF/, '');
    for(let i=0; i<input.length; i++){
      const char = input[i];
      if(char === '"') {
        if(quoted && input[i + 1] === '"'){field += '"';i++;} else {quoted = !quoted;}
      } else if(char === ',' && !quoted){cells.push(field);field = '';}
      else if((char === '\n' || char === '\r') && !quoted){
        if(char === '\r' && input[i+1] === '\n')i++;
        cells.push(field);field='';
        if(cells.some(x=>x.trim())) rows.push(cells);
        cells=[];
      } else {field += char;}
    }
    if(quoted)throw new Error('CSV has an unclosed quoted value.');
    cells.push(field);
    if(cells.some(x=>x.trim()))rows.push(cells);
    if(rows.length < 2)throw new Error('The CSV must include a header and at least one applicant.');
    const header = rows[0].map(x=>x.trim().toLowerCase());
    const indexes = ['id','name','gpa','income'].map(key => header.indexOf(key));
    if(indexes.some(i=>i<0))throw new Error('CSV header must contain id, name, gpa, income.');
    if(rows.length-1 > 100)throw new Error('Limit the CSV to 100 applicants.');
    const used = new Set();
    return rows.slice(1).map((fields,index)=>{
      if(fields.length !== header.length)throw new Error(`Row ${index+2}: the number of fields differs from the header.`);
      const [id,name,gpaRaw,incomeRaw] = indexes.map(i => fields[i].trim());
      if(!id || id.length>40 || used.has(id))throw new Error(`Row ${index+2}: use a unique ID up to 40 characters.`);
      if(!name || name.length>120)throw new Error(`Row ${index+2}: name must be 1–120 characters.`);
      const gpa = Number(gpaRaw), income = Number(incomeRaw);
      if(!/^(?:\d+(?:\.\d+)?)$/.test(gpaRaw) || !Number.isFinite(gpa) || gpa<0 || gpa>4)throw new Error(`Row ${index+2}: GPA must be between 0 and 4.`);
      if(!/^\d+$/.test(incomeRaw) || !Number.isSafeInteger(income) || income<0 || income>50000000)throw new Error(`Row ${index+2}: income must be a valid nonnegative integer.`);
      used.add(id);
      return {id,name,gpa,income};
    });
  }
  $('#cohort-file').addEventListener('change', async event => {
    const file = event.target.files?.[0];state.cohort=null;
    if(!file)return;
    try {
      if(!file.name.toLowerCase().endsWith('.csv') || file.size > 256*1024) throw new Error('Choose a CSV file under 256 KB.');
      state.cohort=parseCsv(await file.text());
      $('#cohort-status').textContent = `✓ ${state.cohort.length} applicant records validated and ready.`;
      notify('Applicant CSV validated.');
    }catch(e){$('#cohort-status').textContent = e.message;error(e.message);}
  });

  function progress(percent, label) {
    $('#scan-progress-fill').style.width = `${percent}%`;
    $('#progress-percent').textContent = `${percent}%`;
    $('#progress-phase').textContent = label;
    $('#scan-progress-track').setAttribute('aria-valuenow', String(percent));
  }
  function step(index,status) {
    const rows = $$('.scan-steps li');
    rows.forEach((item,i)=>{
      item.classList.toggle('active',i===index && status==='running');
      item.classList.toggle('done',i<index || (i===index && status==='done'));
      item.querySelector('.step-state').textContent = i<index || (i===index && status==='done') ? '✓ Complete' : i===index ? 'Processing…' : 'Queued';
    });
    const heads=['Reading previous document','Reading updated document','Comparing rules and clauses','Calculating cohort consequences'];
    $('#processing-title').textContent = heads[Math.min(index,3)];
    const values=[10,37,64,86];
    progress(status==='done' ? 100 : values[Math.min(index,3)], status==='done' ? 'ANALYSIS COMPLETE' : ['READING PREVIOUS PDF','READING UPDATED PDF','COMPARING SOURCE TEXT','MODELING APPLICANTS'][Math.min(index,3)]);
  }
  const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
  async function parsePdf(kind) {
    const data=new FormData();data.append('file',state.files[kind],state.files[kind].name);
    let res;
    try {res=await fetch('/api/parse-pdf',{method:'POST',body:data,cache:'no-store'});}catch{throw new Error(`Network error reading ${kind} PDF. Try again.`);}
    let json;
    try {json=await res.json();}catch{throw new Error('The PDF parser returned an unreadable response.');}
    if(!res.ok)throw new Error(`${kind === 'previous' ? 'Previous' : 'Updated'} PDF: ${String(json.detail||'Could not parse PDF.')}`);
    if(!json.text || !Array.isArray(json.pages))throw new Error('Incomplete PDF extraction response.');
    return json;
  }

  async function startAnalysis() {
    if(state.busy)return;
    clearError();
    if(!state.files.previous || !state.files.updated){error('Upload both the previous and the updated policy PDFs first, or load the fictional sample PDFs.');return;}
    if(selectedCohortMode()==='csv' && (!state.cohort || !state.cohort.length)){error('Choose a valid applicant CSV or select the fictional 16-person sample cohort.');return;}
    state.busy=true;$('#start-analysis').disabled=true;$('#results').hidden=true;$('#processing').hidden=false;document.body.classList.add('is-analyzing');progress(0,'QUEUED');
    $('#processing').scrollIntoView({behavior:'smooth',block:'start'});
    try {
      step(0,'running'); const old = await parsePdf('previous');state.parsed.previous=old;await delay(180);step(1,'running');
      const newer = await parsePdf('updated');state.parsed.updated=newer;await delay(180);step(2,'running');
      const payload={old_policy:old.text,new_policy:newer.text,applicants:selectedCohortMode()==='csv'?state.cohort:[]};
      const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),cache:'no-store'});
      const result=await response.json();
      if(!response.ok)throw new Error(`Analysis rejected: ${String(result.detail?.[0]?.msg || result.detail || response.status)}`);
      if(result.mode!=='offline' || !result.impact || !result.policies || !result.document_diff)throw new Error('Received an incomplete analysis result.');
      step(3,'running');await delay(220);
      state.report=result;state.filter='all';renderResult();step(3,'done');
      $('#results').hidden=false;$('#results').scrollIntoView({behavior:'smooth',block:'start'});
      notify('Analysis completed using your selected documents.');
    }catch(err){
      $('#processing').hidden=true;error(err.message || 'Unable to complete analysis.');
    }finally{state.busy=false;$('#start-analysis').disabled=false;document.body.classList.remove('is-analyzing');}
  }
  $('#start-analysis').addEventListener('click',startAnalysis);
  $('#print-results').addEventListener('click',()=>{if(state.report)window.print();});
  $('#new-analysis').addEventListener('click',()=>{state.report=null;$('#results').hidden=true;$('#processing').hidden=true;$('#workspace').scrollIntoView({behavior:'smooth'});clearError();});

  function formatRule(v, currency=false) {return v==null?'Review required':currency?usd.format(v):Number(v).toFixed(2);}
  function fill(selector, value) {$(selector).textContent = String(value);}
  function renderResult(){
    const r=state.report,c=r.impact.counts,total=r.impact.total;
    const isSample = selectedCohortMode()!=='csv';
    fill('#metric-total',nfmt.format(total));fill('#metric-lost',c.lost);fill('#metric-gained',c.gained);fill('#metric-review',c.review);
    fill('#metric-population',isSample?'Fictional sample cohort':'Uploaded cohort');
    fill('#result-subtitle',`Processed ${state.files.previous.name} and ${state.files.updated.name} · ${state.parsed.previous.page_count} + ${state.parsed.updated.page_count} pages`);
    const reviewNote=c.review?` ${c.review} case(s) need human review because not all requirements can be verified.`:'';
    fill('#analysis-notice', `${isSample?'The 16 applicants are fictional examples, NOT your organization’s applicant population.':'The modeled cases come from your uploaded CSV.'} Results are deterministic simulations from explicit GPA and USD income rules, not a live Clocked call or an official eligibility determination.${reviewNote}`);
    const loss=c.lost||0, gain=c.gained||0, review=c.review||0;
    const impactTitle=review ? `${review} applicant${review===1?' needs':'s need'} a closer look` : loss || gain ? `${loss} lose eligibility. ${gain} gain it.` : 'No modeled eligibility changes';
    fill('#insight-headline',impactTitle);
    fill('#insight-description',review ? 'Some requirements are unsupported or ambiguous, so Ripple preserves uncertainty instead of guessing.' : `Comparing ${state.files.previous.name} with ${state.files.updated.name} across ${total} ${isSample?'fictional':'uploaded'} applicant${total===1?'':'s'}. Each decision can be inspected against the uploaded sources.`);
    $('#insight-banner').classList.remove('show'); requestAnimationFrame(()=>$('#insight-banner').classList.add('show'));
    $('#model-pill').textContent='LOCAL RULE MODEL · 0 CREDITS';
    fill('#rule-old-gpa',formatRule(r.policies.old.min_gpa));fill('#rule-new-gpa',formatRule(r.policies.new.min_gpa));
    fill('#rule-old-income',formatRule(r.policies.old.max_income,true));fill('#rule-new-income',formatRule(r.policies.new.max_income,true));
    fill('#rule-confidence',c.review?'At least one rule is unsupported or ambiguous. All impacted cases are marked for human review rather than assigned invented outcomes.':'Both policies contain an unambiguous GPA minimum and USD annual income ceiling. Calculated outcomes are limited to these two rules.');
    renderChanges(r.document_diff);renderCharts(c,total);renderCases();
  }
  function renderCharts(counts,total){
    fill('#donut-total',total);
    const order=['lost','gained','retained','excluded','review'];let at=0;const arcs=[];
    const legend=$('#outcome-legend'),bars=$('#outcome-bars');legend.replaceChildren();bars.replaceChildren();
    for(const key of order){
      const val=counts[key]||0, deg=total?val/total*360:0;
      if(deg){arcs.push(`${colors[key]} ${at}deg ${at+deg}deg`);at+=deg;}
      const line=el('div','legend-item');const l=el('span');const dot=el('i');dot.style.background=colors[key];l.append(dot,document.createTextNode(labels[key]));line.append(l,el('b',null,val));legend.append(line);
      const bar=el('div','bar-row');bar.append(el('span',null,labels[key].replace(' eligibility','')));const track=el('div','bar-track'),fill=el('span');fill.style.background=colors[key];fill.style.width=total?`${val/total*100}%`:'0%';track.append(fill);bar.append(track,el('strong',null,val));bars.append(bar);
    }
    $('#outcome-donut').style.background=arcs.length?`conic-gradient(${arcs.join(',')})`:'var(--line)';
  }
  function renderChanges(diff){
    fill('#diff-count', `${diff.total_changes} literal edits`);
    const list=$('#change-list');list.replaceChildren();
    if(!diff.changes.length){list.append(el('p','small-explainer','No line-level changes detected in the text extracted from these PDFs.'));return;}
    for(const change of diff.changes){
      const box=el('div','change-item');box.append(el('span','change-type',change.type.toUpperCase()));
      const content=el('div');if(change.previous){content.append(el('strong',null,'Previous'));content.append(el('p',null,change.previous));}
      if(change.updated){content.append(el('strong',null,'Updated'));content.append(el('p',null,change.updated));}
      box.append(content);list.append(box);
    }
    if(diff.truncated)list.append(el('p','small-explainer',`Showing first ${diff.changes.length} of ${diff.total_changes} literal edits.`));
  }
  function badgeClass(status){return `status-chip ${status}`;}
  function renderCases(){
    const cases=state.report.impact.cases;
    fill('#case-label',`${cases.length} ${selectedCohortMode()==='csv'?'uploaded':'fictional'} cases`);
    $$('.filter').forEach(button=>{const active=button.dataset.filter===state.filter;button.classList.toggle('selected',active);button.setAttribute('aria-pressed',String(active));});
    const selected=cases.filter(c=>state.filter==='all' || c.transition===state.filter);
    const body=$('#case-rows');body.replaceChildren();$('#case-detail').hidden=true;
    if(!selected.length){const row=el('tr');const td=el('td','empty-case','No cases in this category.');td.colSpan=7;row.append(td);body.append(row);return;}
    for(const c of selected){
      const row=el('tr');row.append(el('td',null,`${c.id} · ${c.name}`),el('td',null,Number(c.gpa).toFixed(2)),el('td',null,usd.format(c.income)));
      for(const s of [c.old.status,c.new.status]){const td=el('td');td.append(el('span',badgeClass(s),s));row.append(td);}
      const td=el('td');td.append(el('span',badgeClass(c.transition),labels[c.transition]));row.append(td);
      const actions=el('td'),btn=el('button','inspect-btn','Inspect ↗');btn.type='button';btn.addEventListener('click',()=>renderCaseDetail(c));actions.append(btn);row.append(actions);body.append(row);
    }
  }
  $$('.filter').forEach(button=>button.addEventListener('click',()=>{state.filter=button.dataset.filter;renderCases();}));
  function sourcePage(kind,excerpt){
    if(!excerpt)return 1;
    const info=state.parsed[kind];if(!info)return 1;
    const offset=info.text.indexOf(excerpt);
    const page=info.pages.find(p=>offset>=p.start && offset<p.end);
    return page?.page??1;
  }
  function evidenceCard(kind,policy){
    const card=el('div');card.append(el('strong',null,kind==='previous'?'PREVIOUS POLICY':'UPDATED POLICY'));
    card.append(el('p',null,`GPA clause: ${policy.gpa_evidence||'Unavailable — review required.'}`));
    card.append(el('p',null,`Income clause: ${policy.income_evidence||'Unavailable — review required.'}`));
    const link=el('a',null,'Open uploaded PDF ↗');link.href=state.objectURLs[kind]+`#page=${sourcePage(kind,policy.gpa_evidence || policy.income_evidence)}`;link.target='_blank';link.rel='noopener noreferrer';card.append(link);
    return card;
  }
  function renderCaseDetail(c){
    const box=$('#case-detail');box.replaceChildren();box.hidden=false;
    box.append(el('h4',null,`${c.name} — ${labels[c.transition]}`));
    box.append(el('p',null,`Previous: ${c.old.status} (${c.old.reason})  ·  Updated: ${c.new.status} (${c.new.reason})`));
    const grid=el('div','evidence-cols');grid.append(evidenceCard('previous',state.report.policies.old),evidenceCard('updated',state.report.policies.new));box.append(grid);
    box.scrollIntoView({behavior:'smooth',block:'nearest'});
  }
  function protectCsv(value){let string=String(value??'');if(/^[\s]*[=+\-@]/.test(string))string="'"+string;return '"'+string.replaceAll('"','""')+'"';}
  $('#download-results').addEventListener('click',()=>{
    if(!state.report)return;
    const lines=[['id','name','gpa','income','previous_status','updated_status','change','previous_reason','updated_reason']];
    state.report.impact.cases.forEach(c=>lines.push([c.id,c.name,c.gpa,c.income,c.old.status,c.new.status,c.transition,c.old.reason,c.new.reason]));
    const csv=lines.map(row=>row.map(protectCsv).join(',')).join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const a=el('a');a.href=url;a.download='ripple-policy-impact.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    notify('Downloaded the modeled applicant outcomes.');
  });
  window.addEventListener('pagehide',()=>Object.values(state.objectURLs).forEach(url=>URL.revokeObjectURL(url)));
})();