"""Pre-holdout candidate selection. Final holdout is reused historical evidence, not unseen future data."""
import csv,json
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor,RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from goldtrading.model import feature_frame,FEATURES,metrics
from threadpoolctl import threadpool_limits
R=Path(__file__).resolve().parents[1]
with (R/'data/published/observations.csv').open() as f: rows=[{**r,'value':float(r['value'])} for r in csv.DictReader(f) if r['source']=='worldbank']
f=feature_frame(rows).dropna(subset=FEATURES+['actual','previous_price','target_log_return'])
validation_start=pd.Timestamp('2010-01-01');test_start=f.index[-36]
configs=[('naive',0)]+[('drift',n) for n in [3,6,12,24,60,120]]+[('ridge',a) for a in [1,10,100,1000]]+[('hgb',d) for d in [1,2,3]]+[('forest',d) for d in [2,4]]
allpred={}
with threadpool_limits(limits=1):
 for kind,param in configs:
  predictions=[]
  for i in range(len(f)):
   if f.index[i]<validation_start:continue
   tr=f.iloc[:i];te=f.iloc[i:i+1];prev=float(te.previous_price.iloc[0]);ret=0
   if kind=='drift':ret=float(tr.target_log_return.tail(param).mean())
   if kind=='ridge':ret=float(make_pipeline(StandardScaler(),Ridge(alpha=param)).fit(tr[FEATURES],tr.target_log_return).predict(te[FEATURES])[0])
   if kind=='hgb':ret=float(HistGradientBoostingRegressor(max_iter=80,max_depth=param,min_samples_leaf=20,l2_regularization=10,random_state=42,early_stopping=False).fit(tr[FEATURES],tr.target_log_return).predict(te[FEATURES])[0])
   if kind=='forest':ret=float(RandomForestRegressor(n_estimators=80,max_depth=param,min_samples_leaf=15,random_state=42,n_jobs=1).fit(tr[FEATURES],tr.target_log_return).predict(te[FEATURES])[0])
   predictions.append({'period':f.index[i].strftime('%Y-%m-%d'),'train_last_period':tr.index[-1].strftime('%Y-%m-%d'),'training_rows':i,'actual':float(te.actual.iloc[0]),'model':float(prev*np.exp(ret)),'naive':prev})
  allpred[f'{kind}_{param}']=predictions
validation={}
for name,pred in allpred.items():
 v=[p for p in pred if p['period']<test_start.strftime('%Y-%m-%d')];validation[name]=metrics([p['actual'] for p in v],[p['model'] for p in v])
chosen=min(validation,key=lambda k:validation[k]['mae'])
pred=[p for p in allpred[chosen] if p['period']>=test_start.strftime('%Y-%m-%d')];m=metrics([p['actual'] for p in pred],[p['model'] for p in pred]);n=metrics([p['actual'] for p in pred],[p['naive'] for p in pred]);gain=1-m['mae']/n['mae'];rgain=1-m['rmse']/n['rmse']
folds=[]
for start in range(0,36,12):
 pp=pred[start:start+12];mm=metrics([p['actual'] for p in pp],[p['model'] for p in pp]);nn=metrics([p['actual'] for p in pp],[p['naive'] for p in pp]);folds.append({'start':pp[0]['period'],'end':pp[-1]['period'],'model':mm,'naive':nn,'beats_mae':mm['mae']<nn['mae']})
passed=chosen!='naive_0' and gain>=.05 and rgain>=.05 and sum(x['beats_mae'] for x in folds)>=2
report={'selection_scope':'2010 onward through month before final 36 months; choose lowest validation MAE, no holdout tuning','historical_holdout_disclosure':'The existing 36-month holdout has already been viewed in a prior model. This is a reused retrospective benchmark, not a newly unseen prospective test.','promotion_criteria':{'mae_gain_min':.05,'rmse_gain_min':.05,'winning_annual_folds_min':2,'total_annual_folds':3},'validation_metrics':validation,'selected':chosen,'test_start':pred[0]['period'],'test_end':pred[-1]['period'],'model_metrics':m,'naive_metrics':n,'mae_gain':gain,'rmse_gain':rgain,'folds':folds,'passes_retrospective_gate':passed,'predictions':pred}
(R/'evidence/model-research.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['predictions','validation_metrics']},indent=2))
