"""Tests use committed actual observations. Invalid values/outages are labeled fault injection,
never published as observed market data or a real provider outage.
"""
import csv,json,math,tempfile,unittest
from pathlib import Path
from dataclasses import replace
import pandas as pd
from goldtrading.sources import Observation,validate,parse_quote
from goldtrading.storage import Store,ROOT
from goldtrading.pipeline import ingest
from goldtrading.model import feature_frame,evaluate,FEATURES,HOLDOUT,MIN_TRAIN
from goldtrading.export import snapshot,export

def recorded():
 with (ROOT/'data/published/observations.csv').open(newline='') as f:return [Observation(**{**r,'value':float(r['value'])}) for r in csv.DictReader(f)]

class PipelineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=recorded();cls.monthly=[r for r in cls.rows if r.source=='worldbank'];cls.quote=next(r for r in cls.rows if r.series=='XAU')
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'test.db');self.store=Store(self.path)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def test_real_snapshot_rows_validate(self):
  for r in self.rows:validate(r)
 def test_idempotence_and_persistence(self):
  with self.store.transaction():self.assertEqual(self.store.upsert(self.rows),(len(self.rows),0))
  with self.store.transaction():self.assertEqual(self.store.upsert(self.rows),(0,len(self.rows)))
  self.store.close();self.store=Store(self.path);self.assertEqual(self.store.query('SELECT COUNT(*) AS n FROM observations')[0]['n'],len(self.rows))
 def test_invalid_batch_is_atomic(self):
  # Deliberately corrupted copy of one observed value; never a market-data fixture.
  bad=[*self.monthly[:12],replace(self.quote,value=-1)]
  with self.assertRaises(ValueError):
   with self.store.transaction():self.store.upsert(bad)
  self.assertEqual(self.store.query('SELECT COUNT(*) AS n FROM observations')[0]['n'],0)
 def test_units_and_future_dates_rejected(self):
  for bad in [replace(self.quote,unit='THB per baht gold'),replace(self.quote,value=float('nan')),replace(self.quote,observed_at='2999-01-01T00:00:00Z')]:
   with self.assertRaises(ValueError):validate(bad)
 def test_duplicate_batch_rejected(self):
  with self.assertRaises(ValueError):self.store.upsert([self.quote,self.quote])
 def test_source_outage_preserves_prior_records(self):
  with self.store.transaction():self.store.upsert([self.quote])
  def injected(name):
   if name=='gold_api_xau':raise RuntimeError('Intentional test-only source outage')
   return self.monthly[:12],{'url':'recorded real rows used in isolated test'}
  r=ingest(self.store,Path(self.tmp.name)/'raw',sources=['worldbank','gold_api_xau'],collector=injected)
  self.assertEqual(r['status'],'partial');self.assertEqual(r['sources']['gold_api_xau']['status'],'failed')
  self.assertEqual(self.store.query("SELECT value FROM observations WHERE series='XAU'")[0]['value'],self.quote.value)
 def test_all_sources_fail_is_visible(self):
  def fail(name):raise RuntimeError('Intentional test-only failure')
  r=ingest(self.store,Path(self.tmp.name)/'raw',sources=['worldbank'],collector=fail)
  self.assertEqual(r['status'],'failed');self.assertEqual(snapshot(self.store)[0]['pipeline']['status'],'failed')
 def test_export_matches_sql_rows_and_series_boundaries(self):
  with self.store.transaction():self.store.upsert(self.rows)
  d=export(self.store,Path(self.tmp.name)/'published')
  self.assertEqual(d['quality']['rows'],len(self.rows));self.assertEqual(len(d['history']['GOLD']),len([r for r in self.monthly if r.series=='GOLD']))
  self.assertTrue(all(r['frequency']!='monthly' for r in d['quotes']))
  self.assertEqual(d['quality']['duplicate_keys'],0)

class ModelTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=[{'series':r.series,'observed_at':r.observed_at,'value':r.value} for r in recorded() if r.source=='worldbank']
 def test_insufficient_data_does_not_train(self):
  few=[r for r in self.rows if '2000-01-01'<=r['observed_at']<='2002-01-01']
  self.assertEqual(evaluate(few)['status'],'not_ready')
 def test_features_never_use_same_period_target(self):
  before=feature_frame(self.rows);last=max(r['observed_at'] for r in self.rows)
  altered=[{**r,'value':r['value']*2} if r['observed_at']==last and r['series']=='GOLD' else r for r in self.rows]
  after=feature_frame(altered);pd.testing.assert_frame_equal(before[FEATURES],after[FEATURES]);self.assertNotEqual(before.actual.iloc[-1],after.actual.iloc[-1])
 def test_gaps_disable_evaluation(self):
  rows=[r for r in self.rows if r['observed_at']!='2015-06-01']
  self.assertEqual(evaluate(rows)['status'],'not_ready')
 def test_walk_forward_alignment_and_metrics_on_real_history(self):
  r=evaluate(self.rows);self.assertEqual(r['status'],'evaluated');self.assertEqual(len(r['predictions']),HOLDOUT)
  gold={x['observed_at']:x['value'] for x in self.rows if x['series']=='GOLD'}
  errors=[]
  for point in r['predictions']:
   self.assertLess(point['train_last_period'],point['period']);self.assertGreaterEqual(point['training_rows'],MIN_TRAIN)
   self.assertEqual(point['naive'],gold[point['train_last_period']]);self.assertEqual(point['actual'],gold[point['period']]);errors.append(abs(point['model']-point['actual']))
  self.assertAlmostEqual(sum(errors)/len(errors),r['model_metrics']['mae'])
  gate=r['acceptance_gate'];self.assertEqual(len(gate['annual_folds']),3)
  expected=(r['model_metrics']['mae']<=.95*r['naive_metrics']['mae'] and r['model_metrics']['rmse']<=.95*r['naive_metrics']['rmse'] and sum(f['wins'] for f in gate['annual_folds'])>=2)
  self.assertEqual(r['retrospective_gate_passed'],expected)
  if not expected:self.assertIsNone(r['forecast'])

if __name__=='__main__':unittest.main()
