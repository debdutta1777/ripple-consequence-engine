/* Ripple — intentionally dependency-free judge demo. */
'use strict';
const $ = id => document.getElementById(id);
const ui = {data:null, view:null, selected:null, gpa:null, income:null, ruleGpa:null, ruleIncome:null, lens:{which:'new',field:'gpa_evidence'}, tourStep:0, flowAnimated:false, filter:'all', liveReady:false, uploads:{old:null,new:null}};
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
/** A hypothesis changes only the modeled thresholds; evidence stays original. */
function isRuleScenario(){
  if(!ui.data)return false;
  const p=ui.data.policies.new;
  return (ui.ruleGpa!==null&&p.min_gpa!==null&&ui.ruleGpa!==p.min_gpa) ||
         (ui.ruleIncome!==null&&p.max_income!==null&&ui.ruleIncome!==p.max_income);
}
function scenarioData(){
  const base=ui.data;
  if(!base)return null;
  const p=base.policies.new;
  if(!isRuleScenario())return base;
  const updated={...p,min_gpa:ui.ruleGpa??p.min_gpa,max_income:ui.ruleIncome??p.max_income,
    evidence_origin:'hypothetical_counterfactual'};
  const cases=base.impact.cases.map(c=>{
    const before=check(base.policies.old,c),after=check(updated,c);
    return {...c,old:before,new:after,transition:transition(before,after),flip_path:flipPath(updated,c)};
  });
  const counts={lost:0,gained:0,retained:0,excluded:0,review:0};
  cases.forEach(c=>counts[c.transition]++);
  return {...base,policies:{...base.policies,new:updated},impact:{total:cases.length,counts,cases}};
}
function applyRulePreset(gpa,income){
  if(!ui.data||ui.data.policies.new.min_gpa==null||ui.data.policies.new.max_income==null){toast('A verified rule is needed to simulate a preset.');return;}
  ui.ruleGpa=gpa;ui.ruleIncome=income;ui.gpa=null;ui.income=null;render();
  toast('Hypothetical scenario applied. No Clocked credits were used.');
}
function renderRuleLab(){
  if(!ui.data)return;
  const base=ui.data.policies.new,effective=ui.view.policies.new;
  const enabled=base.min_gpa!=null&&base.max_income!=null;
  $('rule-gpa').disabled=!enabled;$('rule-income').disabled=!enabled;
  if(enabled){
    $('rule-gpa').value=effective.min_gpa;$('rule-income').value=effective.max_income;
    $('rule-gpa-value').textContent=Number(effective.min_gpa).toFixed(2);
    $('rule-income-value').textContent=fmtUSD(effective.max_income);
  }else{
    $('rule-gpa-value').textContent='Review';$('rule-income-value').textContent='Review';
  }
  $('flow-label').textContent=isRuleScenario()?'HYPOTHETICAL':'BASELINE';
  if(!enabled){$('lab-impact').textContent='Rule Lab is unavailable: verify the source requirements first.';return;}
  const baseCounts=ui.data.impact.counts,now=ui.view.impact.counts;
  if(!isRuleScenario()){
    $('lab-impact').innerHTML='<span>✳</span> Drag either slider to preview a different policy. Nothing is sent to Clocked.';
    return;
  }
  const deltaLost=(now.lost||0)-(baseCounts.lost||0),deltaGain=(now.gained||0)-(baseCounts.gained||0);
  const label=n=>(n>0?`+${n}`:String(n));
  $('lab-impact').innerHTML=`<span>✳</span><strong>Hypothetical outcome:</strong> <span class="${deltaLost>0?'down':deltaLost<0?'up':''}">${label(deltaLost)} changed losses</span> · <span class="${deltaGain>0?'up':deltaGain<0?'down':''}">${label(deltaGain)} changed gains</span> <small>compared with source policy</small>`;
}
function renderFlow(){
  const svg=$('consequence-flow');if(!svg||!ui.view)return;
  const cases=ui.view.impact.cases;
  const groupY=(c,field,indexMap)=>{
    const status=c[field].status;
    const key=status==='eligible'?'eligible':status==='ineligible'?'ineligible':'review';
    const arr=indexMap[key];const idx=arr.indexOf(c.id);
    const center=key==='eligible'?85:key==='ineligible'?202:273;
    const spacing=Math.min(11.5,72/Math.max(1,arr.length-1));
    return center+(idx-(arr.length-1)/2)*spacing;
  };
  const before={eligible:[],ineligible:[],review:[]},after={eligible:[],ineligible:[],review:[]};
  cases.forEach(c=>{before[c.old.status].push(c.id);after[c.new.status].push(c.id)});
  const palette={lost:'var(--red)',gained:'var(--green)',retained:'var(--purple)',excluded:'var(--muted)',review:'var(--amber)'};
  const shapes=cases.map(c=>{
    const y1=groupY(c,'old',before),y2=groupY(c,'new',after),color=palette[c.transition]||'var(--muted)';
    const active=c.id===ui.selected,filtered=ui.filter!=='all'&&(ui.filter==='stable'? !['retained','excluded'].includes(c.transition):c.transition!==ui.filter);
    return `<g class="flow-case${active?' is-active':''}${filtered?' is-muted':''}${!ui.flowAnimated?' draw-once':''}" tabindex="0" role="button" data-case-id="${escapeHtml(c.id)}" aria-label="Inspect ${escapeHtml(c.name)}: ${escapeHtml(c.transition)}"><title>${escapeHtml(c.name)}: ${escapeHtml(c.old.status)} to ${escapeHtml(c.new.status)}</title><path d="M104 ${y1.toFixed(1)} C270 ${y1.toFixed(1)},350 ${y2.toFixed(1)},516 ${y2.toFixed(1)}" stroke="${color}"/><circle cx="104" cy="${y1.toFixed(1)}" r="3.3" fill="${color}"/><circle cx="516" cy="${y2.toFixed(1)}" r="3.3" fill="${color}"/></g>`;
  }).join('');
  svg.innerHTML=`<text x="12" y="20" class="flow-title">PREVIOUS POLICY</text><text x="608" y="20" text-anchor="end" class="flow-title">UPDATED POLICY</text><line class="flow-divider" x1="0" x2="620" y1="139" y2="139"/><line class="flow-divider" x1="0" x2="620" y1="253" y2="253"/><text x="12" y="42" class="flow-lane-label">Eligible ${before.eligible.length}</text><text x="608" y="42" text-anchor="end" class="flow-lane-label">Eligible ${after.eligible.length}</text><text x="12" y="162" class="flow-lane-label">Ineligible ${before.ineligible.length}</text><text x="608" y="162" text-anchor="end" class="flow-lane-label">Ineligible ${after.ineligible.length}</text><text x="12" y="270" class="flow-lane-label">Review ${before.review.length}</text><text x="608" y="270" text-anchor="end" class="flow-lane-label">Review ${after.review.length}</text>${shapes}`;
  svg.querySelectorAll('.flow-case').forEach(group=>{
    const select=()=>{ui.selected=group.dataset.caseId;ui.gpa=null;ui.income=null;render();$('inspector').scrollIntoView({behavior:'smooth',block:'start'});};
    group.addEventListener('click',select);
    group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});
  });
  ui.flowAnimated=true;
  svg.setAttribute('aria-label',`Consequence map for ${cases.length} fictional applicants. ${ui.view.impact.counts.lost} lost, ${ui.view.impact.counts.gained} gained eligibility under ${isRuleScenario()?'a hypothetical policy':'the selected policies'}.`);
}
function renderSourceLens(){
  const lens=ui.lens||{which:'new',field:'gpa_evidence'};
  const origin=ui.data?.policies?.[lens.which];if(!origin)return;
  const excerpt=origin[lens.field]||'';
  const text=ui.data.documents[lens.which]||'';
  const start=excerpt?text.indexOf(excerpt):-1;
  const page=ui.uploads[lens.which]?.pages?.find(p=>start>=p.start&&start<p.end);
  const label=lens.which==='new'?'UPDATED':'PREVIOUS';
  $('lens-origin').textContent=page?`PDF PAGE ${page.page}`:'DOCUMENT TEXT';
  $('lens-meta').textContent=`${label} POLICY · ${lens.field==='gpa_evidence'?'MINIMUM GPA':'INCOME CEILING'} · ${isRuleScenario()?'Original source clause, not the simulated threshold':'Source excerpt'}`;
  const openPdf=$('lens-open-pdf');
  openPdf.hidden=true;openPdf.removeAttribute('href');
  if($('unsaved-notice').hidden===false){$('lens-excerpt').textContent='Source document was edited after the displayed analysis. Run a new analysis before trusting this excerpt.';return;}
  if(start<0||text.indexOf(excerpt,start+excerpt.length)!==-1){$('lens-excerpt').textContent='No unique, verbatim source passage is available for this clause.';return;}
  const from=Math.max(0,start-100),to=Math.min(text.length,start+excerpt.length+110);
  $('lens-excerpt').innerHTML=`${from?'… ':''}${escapeHtml(text.slice(from,start))}<mark>${escapeHtml(excerpt)}</mark>${escapeHtml(text.slice(start+excerpt.length,to))}${to<text.length?' …':''}`;
  const original=ui.uploads[lens.which];
  if(page&&original?.url){openPdf.href=original.url+`#page=${page.page}`;openPdf.hidden=false;openPdf.textContent=`Open ${original.filename} · page ${page.page} ↗`;}

}
const tourSteps=[
  {title:'A single policy edit can change lives.',description:'Start with two fictional scholarship policies. The baseline compares a GPA increase with an income-ceiling change. We use actual arithmetic on 16 synthetic applicants—not a generated impact estimate.',target:'source-heading'},
  {title:'Follow the ripple, case by case.',description:'The Consequence Map turns every outcome into an interactive path. Red lines lose eligibility, green lines gain it. Select a line to see precisely whose decision flipped.',target:'consequence-flow'},
  {title:'Change the rule—watch everyone move.',description:'Try raising the proposed minimum GPA to 3.80. The cohort outcomes update instantly using our deterministic rule engine. The underlying source evidence stays unchanged.',target:'rule-lab',demo:true},
  {title:'Explain the decision. Show the proof.',description:'Choose a lost applicant, inspect the reason, apply the smallest threshold what-if and jump to the exact original policy sentence. Finish by exporting the review trace.',target:'inspector'}
];
let tourReturnFocus=null;
function renderTour(){
  const step=tourSteps[ui.tourStep];
  $('tour-progress').textContent=`GUIDED TOUR · ${String(ui.tourStep+1).padStart(2,'0')} / 04`;
  $('tour-title').textContent=step.title;$('tour-description').textContent=step.description;
  $('tour-back').hidden=ui.tourStep===0;$('tour-next').textContent=ui.tourStep===tourSteps.length-1?'Explore Ripple →':'Show me →';
}
function openTour(){tourReturnFocus=document.activeElement;ui.tourStep=0;renderTour();$('tour-shade').hidden=false;$('tour-next').focus();}
function closeTour(){$('tour-shade').hidden=true;tourReturnFocus?.focus();}
function advanceTour(){
  const step=tourSteps[ui.tourStep];
  if(step.demo&&ui.data?.policies.new.min_gpa!=null){ui.ruleGpa=3.8;ui.gpa=null;ui.income=null;render();}
  const focusId=step.target;const target=$(focusId);if(target)target.scrollIntoView({behavior:'smooth',block:'center'});
  if(ui.tourStep===tourSteps.length-1){closeTour();return;}
  ui.tourStep++;renderTour();
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
  for(const item of Object.values(ui.uploads)){if(item?.url)URL.revokeObjectURL(item.url);}
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
    if(ui.uploads[which]?.url)URL.revokeObjectURL(ui.uploads[which].url);
    ui.uploads[which]={pages:result.pages,filename:file.name,url:URL.createObjectURL(file)};
    status.className='pdf-upload-status ready';
    status.textContent=`✓ ${file.name} · ${result.page_count} page${result.page_count===1?'':'s'} · ${result.characters} characters. Review the text, then run Clocked analysis if enabled.`;
    markDirty();
    toast('PDF text loaded. No Clocked credits used. Existing demo results are unchanged until analysis.');
  }catch(err){
    if(ui.uploads[which]?.url)URL.revokeObjectURL(ui.uploads[which].url);
    ui.uploads[which]=null;
    fail(err.message||'Could not extract PDF text.');
  }finally{
    fileInput.value='';
  }
}
function jumpToEvidence(which,field){
  ui.lens={which,field};renderSourceLens();
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
  const cases=ui.view?.impact?.cases||ui.data?.impact?.cases||[];
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
  renderSourceLens();
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
function currentCase(){const cases=ui.view?.impact?.cases||ui.data?.impact?.cases||[];return cases.find(c=>c.id===ui.selected) || cases[0];}
function setData(data, {preserveInput=false}={}){
  ui.data=data;
  if(!preserveInput){$('old-policy').value=data.documents.old;$('new-policy').value=data.documents.new;}
  ui.selected=data.impact.cases[0]?.id;
  ui.view=null;ui.flowAnimated=false;ui.ruleGpa=null;ui.ruleIncome=null;ui.lens={which:'new',field:'gpa_evidence'};
  ui.filter='all';ui.gpa=null;ui.income=null;
  $('unsaved-notice').hidden=true;
  render();
}
function render(){
  if(!ui.data)return;
  ui.view=scenarioData();
  const d=ui.view;
  const counts=d.impact.counts;
  $('stat-total').textContent=d.impact.total;
  ['lost','gained','review'].forEach(k=>$('stat-'+k).textContent=counts[k]||0);
  $('mode-indicator').innerHTML='<span class="mode-dot"></span> '+(isRuleScenario()?'WHAT-IF SIMULATION':d.mode==='live'?'LIVE CLOCKED ANALYSIS':'SYNTHETIC DEMO');
  $('mode-indicator').classList.toggle('live',d.mode==='live');
  const pieces=['lost','gained','retained','excluded','review'].map(k=>({key:k,n:counts[k]||0}));
  $('dist-bar').innerHTML=pieces.map(p=>`<div class="dist-segment ${p.key}" style="width:${d.impact.total?p.n/d.impact.total*100:0}%" title="${p.key}: ${p.n}"></div>`).join('');
  $('dist-bar').setAttribute('aria-label',`Outcome distribution: ${pieces.map(p=>`${p.key} ${p.n}`).join(', ')}`);
  $('cohort-summary').textContent=`${d.impact.total} fictional cases · ${isRuleScenario()?'hypothetical rule change':'old vs new'}`;
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
  renderFlow();
  renderRuleLab();
  renderSourceLens();
  const calls=d.api_calls?.length?d.api_calls.join(' · '):'No Clocked calls: this is a synthetic demonstration.';
  const billed=d.mode==='live'&&d.usage?.credits!=null?` · ${d.usage.credits} SDK-reported credits this run`:'';
  $('backend-disclosure').textContent=d.mode==='live'?`Clocked API calls: ${calls}${billed}. ${isRuleScenario()?'A hypothetical rule change is being simulated; it is not sourced to the document. ':''}Policy rules drive deterministic case decisions; missing evidence requires human review.`:`${calls} ${isRuleScenario()?'Hypothetical thresholds are an unsourced sandbox simulation. ':''}This fictional sample uses deterministic GPA/income checks. Live API analysis is a separate protected action.`;
  $('trace-output').textContent=JSON.stringify({mode:d.mode,notice:d.notice,api_calls:d.api_calls,usage:d.usage,comparison:d.comparison,extraction:d.extraction,relevance:d.relevance},null,2);
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
  $('what-if-note').textContent=changed?'Counterfactual preview (not a new Clocked API call).':isRuleScenario()?'Viewing a hypothetical policy threshold. Original document is unchanged.':'Adjust the sliders to test another scenario.';
  const rule=ui.view?.policies.new||ui.data.policies.new;
  const why=[];
  if(rule.min_gpa!=null && gpa<rule.min_gpa)why.push(`GPA ${Number(gpa).toFixed(2)} is below the updated ${Number(rule.min_gpa).toFixed(2)} minimum`);
  if(rule.max_income!=null && income>rule.max_income)why.push(`household income ${fmtUSD(income)} is above the updated ${fmtUSD(rule.max_income)} ceiling`);
  const explanation=trans==='review'?'The policy is missing an essential verified rule. This case cannot be decided automatically.':trans==='lost'?`This applicant loses eligibility because ${why.join(' and ')||'the new rules are more restrictive'}.`:trans==='gained'?'This applicant becomes eligible under the updated policy. Compare the changed thresholds and the source clauses below.':trans==='retained'?'This applicant satisfies the modeled requirements under both policy versions.':'This applicant does not meet the modeled requirements under either policy version.';
  $('case-explanation').textContent=explanation+(changed?' This is an interactive what-if preview, not a new API assessment.':'');

  showFlipPath(flipPath(rule,app));
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
  const report={...ui.view,baseline_policies:ui.data.policies,simulation:{active:isRuleScenario(),proposed_new_gpa:ui.view.policies.new.min_gpa,proposed_new_income_ceiling:ui.view.policies.new.max_income},exported_at:new Date().toISOString(),disclaimer:'Fictional cohort and limited two-threshold decision model. Simulated policies are not source clauses. Not an official scholarship eligibility determination.'};
  const blob=new Blob([JSON.stringify(report,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ripple-evidence-report.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function exportCaseProof(){
  const c=currentCase();if(!c||!ui.data)return;
  if(!$('unsaved-notice').hidden){toast('The policy text has changed. Reset or complete analysis before exporting source-linked proof.');return;}
  const before=check(ui.view.policies.old,{...c,gpa:ui.gpa??c.gpa,income:ui.income??c.income});
  const after=check(ui.view.policies.new,{...c,gpa:ui.gpa??c.gpa,income:ui.income??c.income});
  const trans=transition(before,after);
  const clauses=[['Previous minimum GPA',ui.data.policies.old.gpa_evidence],['Previous income ceiling',ui.data.policies.old.income_evidence],['Updated minimum GPA',ui.data.policies.new.gpa_evidence],['Updated income ceiling',ui.data.policies.new.income_evidence]];
  const rows=clauses.map(([label,value])=>`<tr><th>${escapeHtml(label)}</th><td>${escapeHtml(value||'Not verified')}</td></tr>`).join('');
  const proof=`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ripple evidence · ${escapeHtml(c.id)}</title><style>body{max-width:740px;margin:40px auto;padding:0 24px;color:#25304a;background:#fff;font:15px/1.6 system-ui}h1{letter-spacing:-1px;font-size:35px;margin-bottom:8px}h2{margin-top:30px;font-size:20px}.tag{color:#4e57cc;font-size:12px;font-weight:800;letter-spacing:.08em}.grid{display:grid;grid-template-columns:1fr 1fr;gap:15px}.tile{border:1px solid #e3e8f2;border-radius:12px;padding:15px}.tile strong{display:block;font-size:22px}.note{background:#f3f5fe;border-left:4px solid #5158d9;padding:12px 17px}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #e4e8ef;text-align:left;padding:12px;vertical-align:top}th{font-weight:700;width:37%}footer{margin-top:30px;color:#647086;font-size:12px}@media print{body{margin:14mm auto}.no-print{display:none}}</style></head><body><p class="tag">RIPPLE / SOURCE-LINKED CASE BRIEF</p><h1>${escapeHtml(c.name)}</h1><p>Case ${escapeHtml(c.id)} · ${isRuleScenario()?'HYPOTHETICAL RULE-LAB SIMULATION':ui.data.mode==='live'?'CLOCKED-ASSISTED REVIEW':'FICTIONAL OFFLINE DEMO'}</p><div class="grid"><div class="tile"><small>PREVIOUS POLICY</small><strong>${escapeHtml(before.status)}</strong><p>${escapeHtml(before.reason)}</p></div><div class="tile"><small>UPDATED POLICY</small><strong>${escapeHtml(after.status)}</strong><p>${escapeHtml(after.reason)}</p></div></div><h2>Why the decision moved</h2><p class="note">Outcome: <strong>${escapeHtml(trans)}</strong>. Applicant facts: GPA ${Number(ui.gpa??c.gpa).toFixed(2)}, household income ${fmtUSD(ui.income??c.income)}. This outcome evaluates only the two explicit GPA and income thresholds.</p><h2>Traceable source clauses</h2><table>${rows}</table><h2>Rule-Lab provenance</h2><p>${isRuleScenario()?`Hypothetical proposed requirements: minimum GPA ${Number(ui.view.policies.new.min_gpa).toFixed(2)}, maximum household income ${fmtUSD(ui.view.policies.new.max_income)}. These values were modified in the simulation, not found in the updated source document.`:'No policy thresholds were modified in the simulation. The cited clauses originate from the displayed baseline policy.'}</p><footer>Generated from Ripple on ${escapeHtml(new Date().toISOString())}. Synthetic demonstration only. No personal applicant records are included. This report is not an official eligibility or award decision.</footer><button class="no-print" onclick="window.print()" style="padding:12px 18px;background:#5158d9;color:white;border:0;border-radius:8px;cursor:pointer">Print / save as PDF</button></body></html>`;
  const blob=new Blob([proof],{type:'text/html;charset=utf-8'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=`ripple-${String(c.id).replace(/[^a-zA-Z0-9-]/g,'')}-proof.html`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  toast('Case proof downloaded. Open the HTML to print or save a PDF.');
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
    const path=flipPath(ui.view.policies.new,{...c,gpa:ui.gpa??c.gpa,income:ui.income??c.income});
    if(path.status!=='changes_required')return;
    for(const change of path.changes){if(change.field==='gpa')ui.gpa=change.target;if(change.field==='income')ui.income=change.target;}
    renderCase();toast('Applied the minimum modeled thresholds. Review the updated decision above.');
  });
  document.querySelectorAll('[data-source][data-rule]').forEach(btn=>btn.addEventListener('click',()=>jumpToEvidence(btn.dataset.source,btn.dataset.rule)));
  $('toggle-trace').addEventListener('click',()=>{const trace=$('trace-output');trace.hidden=!trace.hidden;$('toggle-trace').setAttribute('aria-expanded',String(!trace.hidden));if(!trace.hidden)trace.scrollIntoView({behavior:'smooth',block:'nearest'});});
  $('export-report').addEventListener('click',exportReport);
  $('export-case').addEventListener('click',exportCaseProof);
  $('rule-gpa').addEventListener('input',e=>{ui.ruleGpa=Number(e.target.value);ui.gpa=null;ui.income=null;render();});
  $('rule-income').addEventListener('input',e=>{ui.ruleIncome=Number(e.target.value);ui.gpa=null;ui.income=null;render();});
  $('reset-rules').addEventListener('click',()=>{ui.ruleGpa=null;ui.ruleIncome=null;ui.gpa=null;ui.income=null;render();});
  $('preset-tighten').addEventListener('click',()=>applyRulePreset(3.85,40000));
  $('preset-expand').addEventListener('click',()=>applyRulePreset(3.0,70000));
  $('tour-start').addEventListener('click',openTour);
  $('tour-close').addEventListener('click',closeTour);
  $('tour-back').addEventListener('click',()=>{ui.tourStep=Math.max(0,ui.tourStep-1);renderTour();});
  $('tour-next').addEventListener('click',advanceTour);
  $('tour-shade').addEventListener('click',e=>{if(e.target===$('tour-shade'))closeTour();});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('tour-shade').hidden)closeTour();});
}
async function boot(){
  wireEvents();
  setTheme(document.documentElement.dataset.theme==='dark'?'dark':'light');
  try{
    const r=await fetch('/api/health');if(!r.ok)throw new Error('Health unavailable');
    const h=await r.json();ui.liveReady=!!h.live_enabled;
    $('api-status').textContent=h.live_enabled?'Clocked live enabled':'Demo ready';
    if(!h.live_enabled){
      $('analyze-live').disabled=true;
      $('analyze-live').title='Live analysis is administrator-only while the credit-safe verification gate is locked.';
      $('live-explainer').textContent='Live Clocked analysis is locked to protect your API credits. The fictional cohort, Consequence Map, Rule Lab, PDF text preview and source lens are free to explore.';
    }
  }catch{
    $('api-status').textContent='Backend unavailable';
    $('analyze-live').disabled=true;
    $('live-explainer').textContent='Backend unavailable. Refresh when the API is running; no key is stored in the browser.';
  }
  await loadDemo();
}
boot();