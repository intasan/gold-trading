"""Fixed-parameter expanding-window research evaluation on monthly observations.
No random split, no claim of point-in-time vintages or executable trading returns.
"""
import hashlib,json,math,uuid
import numpy as np
import pandas as pd
from .sources import utcnow

FEATURES=['return_1','return_3','return_6','return_12','mean_ratio_3','mean_ratio_12','volatility_6','silver_return_1','platinum_return_1']
MIN_TRAIN=180
HOLDOUT=36

def feature_frame(rows):
    df=pd.DataFrame(rows)
    if df.empty:return pd.DataFrame()
    wide=df.pivot(index='observed_at',columns='series',values='value').sort_index()
    wide.index=pd.to_datetime(wide.index)
    wide=wide[wide.index>='2000-01-01']
    # Missing calendar months remain absent: no interpolation or forward fill.
    wide=wide.reindex(pd.date_range(wide.index.min(),wide.index.max(),freq='MS')) if len(wide) else wide
    g=wide.get('GOLD',pd.Series(index=wide.index,dtype=float))
    f=pd.DataFrame(index=wide.index)
    prior=g.shift(1)
    for n in [1,3,6,12]:f['return_'+str(n)]=g.pct_change(n,fill_method=None).shift(1)
    for n in [3,12]:f['mean_ratio_'+str(n)]=prior/g.shift(1).rolling(n).mean()-1
    f['volatility_6']=g.pct_change(fill_method=None).shift(1).rolling(6).std()
    for name in ['SILVER','PLATINUM']:
        s=wide.get(name,pd.Series(index=wide.index,dtype=float))
        f[name.lower()+'_return_1']=s.pct_change(fill_method=None).shift(1)
    f['previous_price']=prior
    f['actual']=g
    f['target_log_return']=np.log(g/prior)
    return f.replace([np.inf,-np.inf],np.nan)

def metrics(actual,pred):
    a=np.asarray(actual);p=np.asarray(pred)
    return {'mae':float(np.mean(np.abs(a-p))),'rmse':float(np.sqrt(np.mean((a-p)**2))),'mape_percent':float(np.mean(np.abs((a-p)/a))*100)}

def acceptance_gate(predictions):
    """Fixed retrospective research gate; never a trading acceptance claim."""
    criteria={'minimum_mae_gain':0.05,'minimum_rmse_gain':0.05,'minimum_winning_annual_folds':2,'required_holdout_rows':36}
    if len(predictions)!=36:return {'passed':False,'criteria':criteria,'reason':'Requires exactly 36 chronological holdouts','annual_folds':[]}
    actual=[p['actual'] for p in predictions]
    m=metrics(actual,[p['model'] for p in predictions]);n=metrics(actual,[p['naive'] for p in predictions]);folds=[]
    for offset in range(0,36,12):
        pp=predictions[offset:offset+12];a=[p['actual'] for p in pp]
        mm=metrics(a,[p['model'] for p in pp]);nn=metrics(a,[p['naive'] for p in pp])
        folds.append({'start':pp[0]['period'],'end':pp[-1]['period'],'model_mae':mm['mae'],'naive_mae':nn['mae'],'wins':mm['mae']<nn['mae']})
    mae_gain=1-m['mae']/n['mae'] if n['mae']>0 else 0
    rmse_gain=1-m['rmse']/n['rmse'] if n['rmse']>0 else 0
    passed=mae_gain>=.05 and rmse_gain>=.05 and sum(f['wins'] for f in folds)>=2
    return {'passed':passed,'criteria':criteria,'mae_gain':mae_gain,'rmse_gain':rmse_gain,'annual_folds':folds,'scope':'Retrospective research only; publication vintages and execution are not backtested'}

def evaluate(rows):
    import sklearn
    from sklearn.ensemble import HistGradientBoostingRegressor
    from threadpoolctl import threadpool_limits
    frame=feature_frame(rows)
    ready=frame.dropna(subset=FEATURES+['previous_price','actual','target_log_return']) if not frame.empty else frame
    signature=hashlib.sha256(json.dumps(sorted(rows,key=lambda r:(r['observed_at'],r['series'])),sort_keys=True).encode()).hexdigest()
    result={'status':'not_ready','evaluated_at':utcnow(),'frequency':'monthly','target':'Next observed monthly average gold price, USD/troy oz','series_start':'2000-01-01','feature_columns':FEATURES,'min_training_rows':MIN_TRAIN,'holdout_rows':HOLDOUT,'eligible_rows':len(ready),'input_sha256':signature,'method':'Expanding-window, one-observation-ahead; fixed hyperparameters; no random split','limitations':['Current-vintage World Bank data; historical revisions/publication lags are not backtested point-in-time.','Monthly-average research is separate from the spot quotes and FX reference rates.','No fees, positions, profit/backtest returns or investment recommendation are modeled.']}
    if len(ready)<MIN_TRAIN+HOLDOUT:
        result['reason']=f'Requires {MIN_TRAIN+HOLDOUT} complete feature rows; available {len(ready)}.'
        return result
    # Reject gaps in evaluation history rather than treating nonadjacent months as next month.
    if not ready.index.to_period('M').equals(pd.period_range(ready.index.min(),ready.index.max(),freq='M')):
        result['reason']='Gaps in the complete monthly feature sequence; evaluation disabled.'
        return result
    config={'max_iter':80,'max_depth':3,'min_samples_leaf':20,'l2_regularization':10.0,'random_state':42,'early_stopping':False}
    predictions=[];cutoff=len(ready)-HOLDOUT
    with threadpool_limits(limits=1):
        for i in range(cutoff,len(ready)):
            train=ready.iloc[:i];test=ready.iloc[i:i+1]
            estimator=HistGradientBoostingRegressor(**config).fit(train[FEATURES],train.target_log_return)
            ret=float(estimator.predict(test[FEATURES])[0]);previous=float(test.previous_price.iloc[0])
            pred=previous*math.exp(ret)
            predictions.append({'period':test.index[0].strftime('%Y-%m-%d'),'train_last_period':train.index[-1].strftime('%Y-%m-%d'),'actual':float(test.actual.iloc[0]),'model':pred,'naive':previous,'training_rows':len(train)})
        estimator=HistGradientBoostingRegressor(**config).fit(ready[FEATURES],ready.target_log_return)
        # Construct next period features from historical values only.
        next_period=frame.index[-1]+pd.offsets.MonthBegin(1)
        extended=list(rows)+[{'observed_at':next_period.strftime('%Y-%m-%d'),'series':s,'value':np.nan} for s in ['GOLD','SILVER','PLATINUM']]
        future=feature_frame(extended).iloc[-1:]
        forecast=None
        if future[FEATURES+['previous_price']].notna().all(axis=None):
            forecast={'period':next_period.strftime('%Y-%m-%d'),'value':float(future.previous_price.iloc[0]*math.exp(float(estimator.predict(future[FEATURES])[0]))),'origin_last_observed_period':frame.index[-1].strftime('%Y-%m-%d'),'scope':'Research estimate of monthly average; not a live/spot forecast'}
    actual=[p['actual'] for p in predictions]
    m=metrics(actual,[p['model'] for p in predictions]);n=metrics(actual,[p['naive'] for p in predictions])
    gate=acceptance_gate(predictions)
    forecast = forecast if gate['passed'] else None
    result.update(acceptance_gate=gate,retrospective_gate_passed=gate['passed'],promotion_status='research_only' if gate['passed'] else 'not_promoted',status='evaluated',reason=None,model_name='HistGradientBoostingRegressor on log returns',sklearn_version=sklearn.__version__,parameters=config,training_rows_before_holdout=cutoff,test_start=predictions[0]['period'],test_end=predictions[-1]['period'],model_metrics=m,naive_metrics=n,beats_naive_mae=m['mae']<n['mae'],predictions=predictions,forecast=forecast)
    return result

def run_model(store):
    rows=store.query("SELECT series,observed_at,value FROM observations WHERE source='worldbank' AND frequency='monthly' ORDER BY observed_at,series")
    result=evaluate(rows)
    with store.transaction():store.execute('INSERT INTO model_runs VALUES(?,?,?,?)',(str(uuid.uuid4()),utcnow(),result['status'],json.dumps(result,allow_nan=False)))
    return result
