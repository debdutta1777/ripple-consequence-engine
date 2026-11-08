/* Ripple — intentionally dependency-free judge demo. */
'use strict';
const $ = id => document.getElementById(id);
const ui = {data:null, selected:null, gpa:null, income:null, filter:'all', liveReady:false, uploads:{old:null,new:null}};
const colors = {lost:'var(--red)',gained:'var(--green)',retained:'var(--purple)',excluded:'#9ca9bf',review:'var(--amber)'};
const fmtUSD = x => x == null ? 'Unknown' : '$' + Math.round(x).toLocaleString('en-US');
const escapeHtml = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function toast(msg){const el=$('toast');el.textContent=msg;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),5000);}
function check(policy, app){
  if(policy.min_gpa==null||policy.max_income==null) return {status:'review',reason:'A required eligibility threshold lacks verified evidence.'};
  if(app.gpa==null||app.income==null) return {status:'review',reason:'Applicant details incomplete.'};
  const r=[];
  if(app.gpa<policy.min_gpa)r.push('GPA is too low');
  if(app.income>policy.max_income)r.push('income is too high');
  return r.length?{status:'ineligible',reason:r.join('; ')+'.'}:{status:'eligible',reason:'Both documented requirements satisfied.'};
}
function transition(a,b){if(a.status==='review'||b.status==='review')return'review';if(a.status==='eligible'&&b.status==='ineligible')return'lost';if(a.status==='ineligible'&&b.status==='eligible')return'gained';return a.status==='eligible'?'retained':'excluded';}
function flipPath(policy,app){
  const outcome=check(policy,app);
  if(outcome.status==='review')return {status:'review',changes:[]};
  if(outcome.status==='eligible')return {status:'already_eligible',changes:[]};
  const changes=[];
  if(app.gpa<policy.min_gpa)changes.push({field:'gpa',current:app.gpa,target:policy.min_gpa,delta:Math.round((policy.min_gpa-app.gpa)*100)/100});
  if(app.income>policy.max_income)changes.push({field:'income',current:app.income,target:policy.max_income,delta:policy.max_income-app.income});
  return {status:'changes_required',changes};
}
function showFlipPath(path){
  const content=$('flip-content'),action=$('apply-flip');
  action.hidden=true;
  if(path.status==='review'){
    content.innerHTML='<p class="flip-empty">Cannot calculate a safe flip path until all required policy clauses and applicant facts are verified.</p>';return;
  }
  if(path.status==='already_eligible'){
    content.innerHTML='<p class="flip-success">✓ The applicant meets both modeled requirements in the current policy. No adjustment is needed.</p>';return;
  }
  content.innerHTML=path.changes.map(x=>{
    const isGpa=x.field==='gpa';
    const name=isGpa?'CUMULATIVE GPA':'ANNUAL HOUSEHOLD INCOME';
    const before=isGpa?Number(x.current).toFixed(2):fmtUSD(x.current);
    const after=isGpa?Number(x.target).toFixed(2):fmtUSD(x.target);
    const diff=isGpa?'+'+Number(x.delta).toFixed(2)+' GPA':'−'+fmtUSD(Math.abs(x.delta));
    return `<div class="flip-step"><span class="flip-step-name">${name}</span><div class="flip-step-values"><span>${before}</span><span class="flip-arrow">→</span><strong>${after}</strong><span class="flip-difference">${diff}</span></div></div>`;
  }).join('');
  action.hidden=false;
}
function resetPdfState(){
  ui.uploads={old:null,new:null};
  for(const which of ['old','new']){
    $(which+'-pdf').value='';
    const status=$(which+'-upload-status');
    status.className='pdf-upload-status';
    status.textContent='Or paste policy text directly below. Uploading uses no Clocked credits.';
  }
}
async function importPdf(which){
  const fileInput=$(which+'-pdf'), file=fileInput.files[0];
  if(!file)return;
  const status=$(which+'-upload-status');
  status.className='pdf-upload-status';
  const fail=msg=>{status.className='pdf-upload-status error';status.textContent=msg;toast(msg);};
  if(!file.name.toLowerCase().endsWith('.pdf') || (file.type && !['application/pdf','application/octet-stream'].includes(file.type))){
    fail('Please choose a PDF document.');return;
  }
  if(file.size>2*1024*1024){fail('PDF exceeds 2 MB. Try a smaller text-based PDF.');return;}
  status.textContent='Extracting selectable text locally on the server…';
  try{
    const body=new FormData();body.append('file',file);
    const response=await fetch('/api/parse-pdf',{method:'POST',body});
    const result=await response.json();
    if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:`PDF upload failed (HTTP ${response.status})`);
    // Pages are derived from the extracted text, not interpreted by an LLM.
    if(typeof result.text!=='string' || !Array.isArray(result.pages))throw new Error('Invalid PDF extraction response.');
    $(which+'-policy').value=result.text;
    ui.uploads[which]={pages:result.pages,filename:file.name};
    status.className='pdf-upload-status ready';
    status.textContent=`✓ ${file.name} · ${result.page_count} page${result.page_count===1?'':'s'} · ${result.characters} characters. Review the text, then run Clocked analysis if enabled.`;
    markDirty();
    toast('PDF text loaded. No Clocked credits used. Existing demo results are unchanged until analysis.');
  }catch(err){
    ui.uploads[which]=null;
    fail(err.message||'Could not extract PDF text.');
  }finally{
    fileInput.value='';
  }
}
function jumpToEvidence(which,field){
  if(!$('unsaved-notice').hidden){toast('These results are from the previous analysis. Run Clocked analysis before trusting evidence for edited policies.');return;}
  const phrase=ui.data?.policies?.[which]?.[field];
  const editor=$(which==='old'?'old-policy':'new-policy');
  if(!phrase){toast('No verified evidence for this clause.');return;}
  const start=editor.value.indexOf(phrase);
  if(start<0||editor.value.indexOf(phrase,start+phrase.length)>=0){toast('Unique source text not found in the editor.');return;}
  editor.focus();editor.setSelectionRange(start,start+phrase.length);editor.scrollIntoView({behavior:'smooth',block:'center'});
  const page=ui.uploads[which]?.pages.find(p=>start>=p.start&&start<p.end);
  if(page)toast(`Found in uploaded PDF · page ${page.page}. Text is shown in the editor; PDF highlighting is a later milestone.`);
}
function visibleCases(){
  const cases=ui.data?.impact?.cases||[];
  if(ui.filter==='all')return cases;
  if(ui.filter==='stable')return cases.filter(c=>c.transition==='retained'||c.transition==='excluded');
  return cases.filter(c=>c.transition===ui.filter);
}
function chooseFilter(filter){
  ui.filter=filter;
  const visible=visibleCases();
  if(!visible.some(c=>c.id===ui.selected)){
    ui.selected=visible[0]?.id||ui.data?.impact?.cases?.[0]?.id;
    ui.gpa=null;ui.income=null;
  }
  render();
}
function markDirty(){
  if(!ui.data)return;
  const changed=$('old-policy').value!==ui.data.documents.old || $('new-policy').value!==ui.data.documents.new;
  $('unsaved-notice').hidden=!changed;
}
function setTheme(theme){
  const mode=theme==='dark'?'dark':'light';
  document.documentElement.dataset.theme=mode;
  const btn=$('theme-toggle');
  btn.setAttribute('aria-label',mode==='dark'?'Switch to light mode':'Switch to dark mode');
  btn.querySelector('.toggle-text').textContent=mode==='dark'?'Light mode':'Dark mode';
  document.querySelector('meta[name="theme-color"]').content=mode==='dark'?'#0e1421':'#f6f7fb';
  try{localStorage.setItem('ripple-theme',mode);}catch(e){/* Storage may be blocked. */}
}
function currentCase(){return ui.data?.impact?.cases?.find(c=>c.id===ui.selected) || ui.data?.impact?.cases?.[0];}
function setData(data, {preserveInput=false}={}){
  ui.data=data;
  if(!preserveInput){$('old-policy').value=data.documents.old;$('new-policy').value=data.documents.new;}
  ui.selected=data.impact.cases[0]?.id;
  ui.filter='all';ui.gpa=null;ui.income=null;
  $('unsaved-notice').hidden=true;
  render();
}
function render(){
  const d=ui.data;if(!d)return;
  const counts=d.impact.counts;
  $('stat-total').textContent=d.impact.total;
  ['lost','gained','review'].forEach(k=>$('stat-'+k).textContent=counts[k]||0);
  $('mode-indicator').innerHTML='<span class="mode-dot"></span> '+(d.mode==='live'?'LIVE CLOCKED ANALYSIS':'SYNTHETIC DEMO');
  $('mode-indicator').classList.toggle('live',d.mode==='live');
  const pieces=['lost','gained','retained','excluded','review'].map(k=>({key:k,n:counts[k]||0}));
  $('dist-bar').innerHTML=pieces.map(p=>`<div class="dist-segment ${p.key}" style="width:${d.impact.total?p.n/d.impact.total*100:0}%" title="${p.key}: ${p.n}"></div>`).join('');
  $('dist-bar').setAttribute('aria-label',`Outcome distribution: ${pieces.map(p=>`${p.key} ${p.n}`).join(', ')}`);
  $('filter-total').textContent=d.impact.total;
  $('dist-legend').innerHTML=pieces.map(p=>`<span><i class="legend-dot" style="background:${colors[p.key]}"></i>${p.key.replace(/^./,c=>c.toUpperCase())}: ${p.n}</span>`).join('');
  const names=[['min_gpa','Minimum GPA',v=>v==null?'Unknown':v.toFixed(2)],['max_income','Income ceiling',fmtUSD]];
  $('delta-items').innerHTML=names.map(([key,label,format])=>{
    const old=d.policies.old[key],now=d.policies.new[key];
    const diff=old==null||now==null?'REVIEW':old===now?'UNCHANGED':now>old?'INCREASED':'DECREASED';
    return `<div class="delta-item"><div class="delta-top"><strong>${label}</strong><span>${diff}</span></div><div class="delta-values"><div class="threshold ${old==null?'unknown':''}">${escapeHtml(format(old))}</div><span class="arrow-symbol">→</span><div class="threshold after ${now==null?'unknown':''}">${escapeHtml(format(now))}</div></div></div>`;
  }).join('');
  $('review-warning').hidden=!Object.values(d.policies).some(p=>p.min_gpa==null||p.max_income==null);
  const compared=$('compare-verdict');
  compared.hidden=d.mode!=='live';
  if(d.mode==='live') {
    const conflicts=Array.isArray(d.comparison?.conflicts)?d.comparison.conflicts.length:0;
    compared.textContent=`CLOCKED COMPARE · ${String(d.comparison?.verdict??'No verdict reported')} · ${conflicts} reported conflicts. See API trace for source details.`;
  }
  document.querySelectorAll('[data-filter]').forEach(b=>{
    const active=b.dataset.filter===ui.filter;
    b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));
  });
  const words={lost:'Lost',gained:'Gained',retained:'Eligible',excluded:'Ineligible',review:'Review'};
  const list=visibleCases();
  $('case-matrix').innerHTML=list.length?list.map(c=>`<button class="case-node ${escapeHtml(c.transition)} ${c.id===ui.selected?'selected':''}" data-case-id="${escapeHtml(c.id)}" aria-label="${escapeHtml(c.name)}: ${escapeHtml(c.transition)}" aria-pressed="${c.id===ui.selected}"><span class="case-node-top"><span class="case-node-name">${escapeHtml(c.name)}</span><span class="case-node-index">${escapeHtml(c.id)}</span></span><span class="case-node-bottom"><span class="node-dots"><i class="${c.old.status==='eligible'?'good':c.old.status==='review'?'review':'bad'}"></i><span class="node-arrow">→</span><i class="${c.new.status==='eligible'?'good':c.new.status==='review'?'review':'bad'}"></i></span><span class="case-outcome">${words[c.transition]||'Review'}</span></span></button>`).join(''):'<p class="case-matrix-empty">No applicants in this category. Choose another filter.</p>';
  $('case-matrix').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{ui.selected=btn.dataset.caseId;ui.gpa=null;ui.income=null;render();document.getElementById('inspector').scrollIntoView({behavior:'smooth',block:'start'});}));
  renderCase();
  const calls=d.api_calls?.length?d.api_calls.join(' · '):'No Clocked calls: this is a synthetic demonstration.';
  $('backend-disclosure').textContent=d.mode==='live'?`Clocked API calls: ${calls}. Policy rules drive deterministic case decisions; missing evidence requires human review.`:`${calls} This fictional sample uses deterministic GPA/income checks. Live API analysis is a separate action and requires server-side configuration.`;
  $('trace-output').textContent=JSON.stringify({mode:d.mode,notice:d.notice,api_calls:d.api_calls,comparison:d.comparison,extraction:d.extraction,relevance:d.relevance},null,2);
}
function renderCase(){
  const c=currentCase();if(!c)return;
  const gpa=ui.gpa??c.gpa, income=ui.income??c.income;
  $('selected-case-title').textContent=c.name;
  $('gpa-range').value=gpa;$('gpa-value').textContent=Number(gpa).toFixed(2);
  $('income-range').value=income;$('income-value').textContent=fmtUSD(income);
  const app={...c,gpa,income};
  const before=check(ui.data.policies.old,app), after=check(ui.data.policies.new,app), trans=transition(before,after);
  const words={lost:'Lost eligibility',gained:'Gained eligibility',retained:'Remains eligible',excluded:'Remains ineligible',review:'Needs review'};
  $('selected-transition').textContent=words[trans];$('selected-transition').className='case-chip '+trans;
  for(const [prefix,outcome] of [['before',before],['after',after]]){
    const status=$(prefix+'-status');status.textContent=outcome.status==='eligible'?'Eligible':outcome.status==='review'?'Needs review':'Not eligible';status.className=outcome.status==='eligible'?'good':outcome.status==='review'?'review':'bad';
    $(prefix+'-reason').textContent=outcome.reason;
  }
  const changed=ui.gpa!==null||ui.income!==null;
  $('what-if-note').textContent=changed?'Counterfactual preview (not a new Clocked API call).':'Adjust the sliders to test another scenario.';
  const rule=ui.data.policies.new;
  const why=[];
  if(rule.min_gpa!=null && gpa<rule.min_gpa)why.push(`GPA ${Number(gpa).toFixed(2)} is below the updated ${Number(rule.min_gpa).toFixed(2)} minimum`);
  if(rule.max_income!=null && income>rule.max_income)why.push(`household income ${fmtUSD(income)} is above the updated ${fmtUSD(rule.max_income)} ceiling`);
  const explanation=trans==='review'?'The policy is missing an essential verified rule. This case cannot be decided automatically.':trans==='lost'?`This applicant loses eligibility because ${why.join(' and ')||'the new rules are more restrictive'}.`:trans==='gained'?'This applicant becomes eligible under the updated policy. Compare the changed thresholds and the source clauses below.':trans==='retained'?'This applicant satisfies the modeled requirements under both policy versions.':'This applicant does not meet the modeled requirements under either policy version.';
  $('case-explanation').textContent=explanation+(changed?' This is an interactive what-if preview, not a new API assessment.':'');

  showFlipPath(flipPath(ui.data.policies.new,app));
  const evidenceOld=ui.data.policies.old, evidenceNew=ui.data.policies.new;
  $('old-evidence').textContent=`GPA: ${evidenceOld.gpa_evidence||'Not verified'}\nIncome: ${evidenceOld.income_evidence||'Not verified'}`;
  $('new-evidence').textContent=`GPA: ${evidenceNew.gpa_evidence||'Not verified'}\nIncome: ${evidenceNew.income_evidence||'Not verified'}`;
  const ranked=$('rerank-evidence');
  ranked.hidden=!(ui.data.mode==='live' && Array.isArray(ui.data.relevance) && ui.data.relevance.length);
  if(!ranked.hidden){
    const matches=ui.data.relevance.slice(0,4);
    ranked.innerHTML='<div class="rank-title">CLOCKED RERANK · RELEVANT CLAUSES</div>'+matches.map(r=>{
      const pct=typeof r.relevance_score==='number' ? Math.round(r.relevance_score*100)+'%' : '—';
      return `<div class="rank-item"><span>${escapeHtml(r.id??`Document ${r.index??''}`)}</span><strong>${pct}</strong><small>${escapeHtml(r.action??'')}</small></div>`;
    }).join('');
  }
}
async function loadDemo(){
  try{const r=await fetch('/api/demo');if(!r.ok)throw new Error('Demo server not available');resetPdfState();setData(await r.json());}
  catch(err){toast('The demo could not load. Start the FastAPI server and refresh.');console.error(err);}
}
async function analyze(){
  const btn=$('analyze-live');btn.disabled=true;const original=btn.innerHTML;btn.textContent='Analyzing…';
  try{
    const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_policy:$('old-policy').value,new_policy:$('new-policy').value,applicants:(ui.data?.impact?.cases||[]).map(({id,name,gpa,income})=>({id,name,gpa,income}))})});
    const obj=await r.json();if(!r.ok)throw new Error(typeof obj.detail==='string'?obj.detail:`Request failed (HTTP ${r.status})`);
    setData(obj,{preserveInput:true});ui.data.documents={old:$('old-policy').value,new:$('new-policy').value};toast('Live Clocked integration completed. Inspect the API trace for evidence.');
  }catch(err){toast(err.message);}
  finally{btn.disabled=false;btn.innerHTML=original;}
}
function exportReport(){
  if(!ui.data)return;
  const report={...ui.data,exported_at:new Date().toISOString(),disclaimer:'Synthetic demonstration or prototype review only. Not an official scholarship eligibility determination.'};
  const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ripple-evidence-report.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function wireEvents(){
  $('reset-demo').addEventListener('click',loadDemo);
  for(const which of ['old','new'])$(which+'-pdf').addEventListener('change',()=>importPdf(which));
  $('theme-toggle').addEventListener('click',()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));
  document.querySelectorAll('[data-filter]').forEach(btn=>btn.addEventListener('click',()=>chooseFilter(btn.dataset.filter)));
  $('explore-flips').addEventListener('click',()=>{
    if(!ui.data){toast('The sample has not loaded yet.');return;}
    ui.filter='lost';ui.selected=ui.data.impact.cases.find(c=>c.transition==='lost')?.id||ui.data.impact.cases[0]?.id;
    ui.gpa=null;ui.income=null;render();$('cases').scrollIntoView({behavior:'smooth',block:'start'});
  });
  for(const id of ['old-policy','new-policy'])$(id).addEventListener('input',markDirty);
  document.querySelectorAll('.rail-item').forEach(link=>link.addEventListener('click',()=>{
    document.querySelectorAll('.rail-item').forEach(item=>item.classList.toggle('active',item===link));
  }));
  $('analyze-live').addEventListener('click',analyze);
  $('gpa-range').addEventListener('input',e=>{ui.gpa=Number(e.target.value);renderCase()});
  $('income-range').addEventListener('input',e=>{ui.income=Number(e.target.value);renderCase()});
  $('reset-case').addEventListener('click',()=>{ui.gpa=null;ui.income=null;renderCase()});
  $('apply-flip').addEventListener('click',()=>{
    const c=currentCase();if(!c)return;
    const path=flipPath(ui.data.policies.new,{...c,gpa:ui.gpa??c.gpa,income:ui.income??c.income});
    if(path.status!=='changes_required')return;
    for(const change of path.changes){if(change.field==='gpa')ui.gpa=change.target;if(change.field==='income')ui.income=change.target;}
    renderCase();toast('Applied the minimum modeled thresholds. Review the updated decision above.');
  });
  document.querySelectorAll('[data-source][data-rule]').forEach(btn=>btn.addEventListener('click',()=>jumpToEvidence(btn.dataset.source,btn.dataset.rule)));
  $('toggle-trace').addEventListener('click',()=>{const trace=$('trace-output');trace.hidden=!trace.hidden;$('toggle-trace').setAttribute('aria-expanded',String(!trace.hidden));if(!trace.hidden)trace.scrollIntoView({behavior:'smooth',block:'nearest'});});
  $('export-report').addEventListener('click',exportReport);
}
async function boot(){
  wireEvents();
  setTheme(document.documentElement.dataset.theme==='dark'?'dark':'light');
  try{
    const r=await fetch('/api/health');if(!r.ok)throw new Error('Health unavailable');
    const h=await r.json();ui.liveReady=!!h.live_enabled;
    $('api-status').textContent=h.live_enabled?'Clocked connected':'Demo ready';
    if(!h.live_enabled){
      $('analyze-live').disabled=true;
      $('analyze-live').title='Enable CLOCKED_API_KEY and ENABLE_LIVE in the Vercel project to analyze custom text';
      $('live-explainer').textContent='Live Clocked analysis needs a backend API key. The one-click synthetic demo, evidence viewer, filters and simulations are fully interactive.';
    }
  }catch{
    $('api-status').textContent='Backend unavailable';
    $('analyze-live').disabled=true;
    $('live-explainer').textContent='Backend unavailable. Refresh when the API is running; no key is stored in the browser.';
  }
  await loadDemo();
}
boot();