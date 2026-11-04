'use strict';
let dataset=null,selected=[];
const $=id=>document.getElementById(id),format=(n,d=2)=>Number.isFinite(Number(n))?Number(n).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const month=s=>new Date(s+'T00:00:00Z').toLocaleDateString('en-GB',{month:'short',year:'numeric',timeZone:'UTC'});
const dateTime=s=>s?new Date(s).toLocaleString('en-GB',{timeZone:'UTC',hour12:false})+' UTC':'Not available';
function lineChart(container,rows,lines,label){
 if(!rows.length){container.textContent='No recorded observations in this selection.';return;}
 const W=Math.max(280,Math.min(800,container.clientWidth||800)),H=W<480?240:280,L=W<480?50:62,R=18,T=20,B=35,values=rows.flatMap(r=>lines.map(s=>r[s.key])).filter(Number.isFinite);
 if(!values.length){container.textContent='No valid values.';return;}
 const lo=Math.min(...values),hi=Math.max(...values),pad=(hi-lo||hi*.03||1)*.12,min=Math.max(0,lo-pad),max=hi+pad;
 const x=i=>L+(W-L-R)*(rows.length===1?.5:i/(rows.length-1)),y=v=>T+(H-T-B)*(1-(v-min)/(max-min));
 let svg=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title>`;
 for(let i=0;i<=4;i++){const value=min+(max-min)*i/4,yy=y(value);svg+=`<line class="grid" x1="${L}" x2="${W-R}" y1="${yy}" y2="${yy}"/><text x="${L-9}" y="${yy+4}" text-anchor="end">${esc(format(value,value<100?1:0))}</text>`;}
 for(const s of lines){const points=rows.map((r,i)=>Number.isFinite(r[s.key])?`${x(i)},${y(r[s.key])}`:null).filter(Boolean).join(' ');svg+=`<polyline class="series-line ${s.className}" points="${points}"/>`;}
 for(let i=0;i<rows.length;i++){const r=rows[i];svg+=`<circle cx="${x(i)}" cy="${y(r[lines[0].key])}" r="6"><title>${esc(month(r.period))}: ${lines.map(s=>esc(s.name)+': '+format(r[s.key])).join(' | ')} USD / troy oz</title></circle>`;}
 const indexes=[0,Math.floor((rows.length-1)/2),rows.length-1];
 [...new Set(indexes)].forEach(i=>{svg+=`<text x="${x(i)}" y="${H-7}" text-anchor="${i===0?'start':i===rows.length-1?'end':'middle'}">${esc(month(rows[i].period))}</text>`;});
 container.innerHTML=svg+'</svg>';
}
function renderHistory(){
 if(!dataset)return;
 const metal=$('metal').value,all=dataset.history[metal]||[],window=Number($('window').value);selected=window?all.slice(-window):all.slice();
 const title=metal[0]+metal.slice(1).toLowerCase();$('table-title').textContent=title+' · monthly data';
 const last=selected.at(-1),prev=selected.at(-2);
 $('history-latest').textContent=last?format(last.value):'—';$('history-period').textContent=last?month(last.period):'No recorded period';
 $('history-change').textContent=last&&prev?`${last.value>=prev.value?'+':''}${format((last.value/prev.value-1)*100)}% vs prior month`:'';
 lineChart($('history-chart'),selected,[{key:'value',name:title,className:'actual-line'}],`${title} monthly average prices in USD per troy ounce; data table follows`);
 $('history-range').textContent=selected.length?`${selected.length} recorded months · ${month(selected[0].period)} — ${month(last.period)} · World Bank Pink Sheet`:'No monthly observations';
 const amount=Number($('table-rows').value),display=selected.slice().reverse().slice(0,amount||selected.length);
 $('price-table').innerHTML=display.map(r=>`<tr><td>${esc(month(r.period))}</td><td>${format(r.value)}</td><td>Monthly average</td><td>World Bank</td></tr>`).join('');
 $('table-count').textContent=`Showing ${display.length} of ${selected.length} selected observations. No spot quote is mixed into this table.`;
}
function renderModel(){
 const m=dataset.model||{};$('model-results').hidden=m.status!=='evaluated';$('model-status').textContent=m.status==='evaluated'?(m.beats_naive_mae?'EVALUATED / RESEARCH ONLY':'EVALUATED / NOT PROMOTED'):(m.status||'not run').toUpperCase();$('model-status').classList.toggle('warn',!m.beats_naive_mae);
 $('model-summary').textContent=m.status==='evaluated'?(m.beats_naive_mae?'The candidate had lower MAE than the naive baseline in this recorded holdout. This is retrospective monthly research, not a validated trading signal.':'The candidate did not beat the naive baseline on MAE. It is not promoted, and no point forecast is published.'):(m.reason||'No evaluated model is available.');
 $('model-method').textContent=m.method?`${m.method}. Eligible feature rows: ${m.eligible_rows}. Minimum initial training: ${m.min_training_rows}. Features: ${(m.feature_columns||[]).join(', ')}.`:'Evaluation requires sufficient consecutive historical monthly observations.';
 if(m.status!=='evaluated')return;
 $('model-facts').innerHTML=`<div><strong>${esc(month(m.test_start))} — ${esc(month(m.test_end))}</strong>Holdout window</div><div><strong>${m.holdout_rows}</strong>Expanding-window predictions</div><div><strong>${m.training_rows_before_holdout}</strong>Initial training observations</div><div><strong>2000 onward</strong>Training series scope</div>`;
 $('metrics').innerHTML=[['MAE','mae'],['RMSE','rmse'],['MAPE (%)','mape_percent']].map(([name,key])=>`<tr><td>${name}</td><td>${format(m.model_metrics[key])}</td><td>${format(m.naive_metrics[key])}</td></tr>`).join('');
 lineChart($('evaluation-chart'),m.predictions||[],[{key:'actual',name:'Observed',className:'actual-line'},{key:'model',name:'Model',className:'predicted-line'},{key:'naive',name:'Naive',className:'naive-line'}],'Recorded holdout: observed gold monthly average versus model and naive baseline');
 $('forecast').textContent=m.beats_naive_mae&&m.forecast?`Research estimate for the next unpublished monthly period (${month(m.forecast.period)}): ${format(m.forecast.value)} USD / troy oz. Not a spot quote or trading signal.`:'Forecast withheld: the candidate has not outperformed the last-observed-price baseline.';
}
function render(){
 $('export-date').textContent=dateTime(dataset.exported_at);
 for(const [series,id,time,source] of [['XAU','quote-xau','time-xau','gold_api'],['XAG','quote-xag','time-xag','gold_api'],['USDTHB','quote-fx','time-fx','frankfurter']]){
  const r=dataset.quotes.find(q=>q.series===series&&q.source===source);$(id).textContent=r?format(r.value,series==='USDTHB'?3:2):'—';
  $(time).textContent=r?`${series==='USDTHB'?'Reference date: '+r.observed_at:'Provider update: '+dateTime(r.observed_at)} · ${dataset.sources[source].name}`:'No real observation available';
  const age=r?(Date.now()-new Date(r.observed_at).getTime())/3600000:Infinity;
  if(age>(series==='USDTHB'?96:6)){$(time).textContent+=' · Older observation — not live';$(time).classList.add('stale');}else $(time).classList.remove('stale');
 }
 $('row-count').textContent=format(dataset.quality.rows,0);$('quality-count').textContent=dataset.quality.invalid_prices+' / '+dataset.quality.duplicate_keys;
 $('run-status').textContent=(dataset.pipeline.status||'not_run').toUpperCase();$('run-time').textContent=dateTime(dataset.pipeline.finished_at);
 $('source-table').innerHTML=Object.entries(dataset.pipeline.sources||{}).map(([name,r])=>`<tr><td>${esc(name)}</td><td>${esc(r.status)}${r.error?`<span class="error-text">${esc(r.error)}</span>`:''}</td><td>${format(r.extracted_rows,0)}</td><td>${r.inserted_rows} / ${r.existing_rows}</td><td>${r.provenance?.retrieved_at?esc(dateTime(r.provenance.retrieved_at)):''}${r.provenance?.cached?' · cached response':''}<br>${esc(r.provenance?.release_label||'')}${r.provenance?.sha256?`<br>SHA-256: ${esc(r.provenance.sha256.slice(0,16))}…`:''}</td></tr>`).join('');
 $('coverage-table').innerHTML=dataset.coverage.map(c=>`<tr><td>${esc(c.source+' / '+c.series)}</td><td>${esc(c.frequency)}</td><td>${format(c.rows,0)}</td><td>${esc(c.first_period)} — ${esc(c.last_period)}</td></tr>`).join('');
 renderHistory();renderModel();
}
async function load(){
 $('reload').disabled=true;$('load-status').textContent='Loading export…';$('error').hidden=true;
 const mode=new URLSearchParams(location.search).get('mode'),url=mode==='api'?'api/snapshot':'data/published/snapshot.json';
 try{
  const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw Error(`HTTP ${response.status}`);
  const d=await response.json();if(d.schema_version!==1||!d.history||!Array.isArray(d.quotes)||!d.quality||!d.coverage)throw Error('Unexpected snapshot schema');
  dataset=d;$('dashboard').hidden=false;render();$('load-status').textContent=mode==='api'?'Read from database API':'Recorded export loaded';
 }catch(e){$('dashboard').hidden=true;$('error').hidden=false;$('error').textContent=`Data unavailable: ${e.message}. Run the Python pipeline and export data first. API mode requires the Python server. No sample prices are substituted.`;$('load-status').textContent='Unavailable';}
 finally{$('reload').disabled=false;}
}
for(const id of ['metal','window','table-rows'])$(id).addEventListener('change',renderHistory);
$('reload').addEventListener('click',load);
$('download').addEventListener('click',()=>{
 if(!dataset||!selected.length)return;
 const text='source,series,frequency,period,value,unit\r\n'+selected.map(r=>`worldbank,${$('metal').value},monthly,${r.period},${r.value},USD per troy ounce monthly average`).join('\r\n');
 const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`worldbank-${$('metal').value.toLowerCase()}-monthly.csv`;document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);
});
load();

let resizePending=false;addEventListener('resize',()=>{if(!dataset||resizePending)return;resizePending=true;requestAnimationFrame(()=>{resizePending=false;renderHistory();renderModel();});});
