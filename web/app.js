/* Ripple — intentionally dependency-free judge demo. */
'use strict';
const $ = id => document.getElementById(id);
const ui = {data:null, selected:null, gpa:null, income:null};
const colors = {lost:'#ff8d88',gained:'#ccf880',retained:'#baa5fc',excluded:'#4b6075',review:'#edcd87'};
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
function jumpToEvidence(which,field){
  const phrase=ui.data?.policies?.[which]?.[field];
  const editor=$(which==='old'?'old-policy':'new-policy');
  if(!phrase){toast('No verified evidence for this clause.');return;}
  const start=editor.value.indexOf(phrase);
  if(start<0||editor.value.indexOf(phrase,start+phrase.length)>=0){toast('Unique source text not found in the editor.');return;}
  editor.focus();editor.setSelectionRange(start,start+phrase.length);editor.scrollIntoView({behavior:'smooth',block:'center'});
}
function currentCase(){return ui.data?.impact?.cases?.find(c=>c.id===ui.selected) || ui.data?.impact?.cases?.[0];}
function setData(data, {preserveInput=false}={}){
  ui.data=data;
  if(!preserveInput){$('old-policy').value=data.documents.old;$('new-policy').value=data.documents.new;}
  ui.selected=data.impact.cases[0]?.id;
  ui.gpa=null;ui.income=null;
  render();
}
function render(){
  const d=ui.data;if(!d)return;
  const counts=d.impact.counts;
  $('stat-total').textContent=d.impact.total;
  ['lost','gained','review'].forEach(k=>$('stat-'+k).textContent=counts[k]||0);
  $('mode-indicator').textContent=d.mode==='live'?'LIVE CLOCKED ANALYSIS':'SYNTHETIC DEMO';
  $('mode-indicator').classList.toggle('live',d.mode==='live');
  const pieces=['lost','gained','retained','excluded','review'].map(k=>({key:k,n:counts[k]||0}));
  $('dist-bar').innerHTML=pieces.map(p=>`<div class="dist-segment ${p.key}" style="width:${d.impact.total?p.n/d.impact.total*100:0}%" title="${p.key}: ${p.n}"></div>`).join('');
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
  $('case-matrix').innerHTML=d.impact.cases.map(c=>`<button class="case-node ${c.transition} ${c.id===ui.selected?'selected':''}" data-case-id="${escapeHtml(c.id)}" aria-label="${escapeHtml(c.name)}: ${escapeHtml(c.transition)}" title="${escapeHtml(c.name)} · ${escapeHtml(c.transition)}"><span class="node-dots"><i class="${c.old.status==='eligible'?'good':'bad'}"></i><span class="node-arrow">→</span><i class="${c.new.status==='eligible'?'good':'bad'}"></i></span><small>${escapeHtml(c.id)}</small></button>`).join('');
  $('case-matrix').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{ui.selected=btn.dataset.caseId;ui.gpa=null;ui.income=null;render();}));
  renderCase();
  const calls=d.api_calls?.length?d.api_calls.join(' · '):'No Clocked calls: this is a synthetic demonstration.';
  $('backend-disclosure').textContent=d.mode==='live'?`Verified execution path: ${calls}. Extracted rules drive deterministic decisions; missing evidence triggers review.`:`${calls} Press Analyze live to send the currently displayed policy texts to Clocked. The example is fictional and does not rely on hidden API calls.`;
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
  try{const r=await fetch('/api/demo');if(!r.ok)throw new Error('Demo server not available');setData(await r.json());}
  catch(err){toast('The demo could not load. Start the FastAPI server and refresh.');console.error(err);}
}
async function analyze(){
  const btn=$('analyze-live');btn.disabled=true;const original=btn.innerHTML;btn.textContent='Analyzing…';
  try{
    const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_policy:$('old-policy').value,new_policy:$('new-policy').value,applicants:(ui.data?.impact?.cases||[]).map(({id,name,gpa,income})=>({id,name,gpa,income}))})});
    const obj=await r.json();if(!r.ok)throw new Error(typeof obj.detail==='string'?obj.detail:`Request failed (HTTP ${r.status})`);
    setData(obj,{preserveInput:true});toast('Live Clocked integration completed. Inspect the API trace for evidence.');
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
  $('toggle-trace').addEventListener('click',()=>{$('trace-output').hidden=!$('trace-output').hidden;if(!$('trace-output').hidden)$('trace-output').scrollIntoView({behavior:'smooth',block:'nearest'});});
  $('export-report').addEventListener('click',exportReport);
}
async function boot(){
  wireEvents();
  try{const r=await fetch('/api/health');const h=await r.json();$('api-status').textContent=h.live_enabled?'Clocked live ready':'Demo ready · Live disabled';}catch{$('api-status').textContent='Backend unavailable';}
  await loadDemo();
}
boot();
