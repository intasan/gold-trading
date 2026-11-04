"""Optional Airflow 2.10.x orchestration. Requires a separate Python 3.12 pipeline venv.
Runtime not asserted by syntax checks; trigger manually (schedule=None).
"""
from datetime import datetime,timedelta
import os
from airflow import DAG
from airflow.operators.bash import BashOperator
project=os.environ.get('GOLD_PROJECT_DIR','/opt/airflow/gold-trading')
python=os.environ.get('GOLD_PIPELINE_PYTHON','/opt/gold-venv/bin/python')
with DAG('gold_analytics_pipeline',start_date=datetime(2026,1,1),schedule=None,catchup=False,max_active_runs=1,default_args={'retries':1,'retry_delay':timedelta(minutes=5)},tags=['gold','etl','research']) as dag:
 env={'GOLD_PROJECT_DIR':project,'GOLD_PIPELINE_PYTHON':python}
 prefix='cd "$GOLD_PROJECT_DIR" && "$GOLD_PIPELINE_PYTHON" -m goldtrading '
 ingest_task=BashOperator(task_id='extract_validate_load',bash_command=prefix+'ingest',env=env,append_env=True)
 model_task=BashOperator(task_id='evaluate_if_sufficient_history',bash_command=prefix+'model',env=env,append_env=True)
 export_task=BashOperator(task_id='export_snapshot',bash_command=prefix+'export',env=env,append_env=True,trigger_rule='all_done')
 ingest_task >> model_task >> export_task
