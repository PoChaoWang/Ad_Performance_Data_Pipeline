from datetime import datetime, timedelta
from airflow import DAG
from docker.types import Mount
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
import subprocess
from dotenv import load_dotenv
import os

env_path = "../../.env"
load_dotenv(env_path)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    }

def run_elt_script():
    script_path = "/opt/airflow/elt/elt_script.py"
    result = subprocess.run(["python", script_path], capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"ELT script failed with error:\n{result.stderr}")
    else:
        print(result.stdout)

dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='Extract, Transform, Load (ETL) and Data Transformation Tool (DBT) pipeline',
    start_date=datetime(2024,12,31),
    schedule_interval='0 0 * * *',  # Run every day at midnight
    catchup=False,
    )

task1 = PythonOperator(
    task_id='run_elt_script',
    python_callable=run_elt_script,
    dag=dag,
)

custom_postgres_path = os.path.abspath('./custom_ad_data')

task2 = DockerOperator(
    task_id='run_dbt',
    image='ghcr.io/dbt-labs/dbt-postgres:1.9.0',
    command=
      [
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/dbt",
        "--full-refresh"
      ],
      auto_remove=True,
      docker_url="unix://var/run/docker.sock",
      network_mode="bridge",
      mounts=[
        Mount(source='/Users/pochaowang/Documents/Profile/ad_performance_data_pipeline/custom_ad_data', target='/dbt', type='bind'),
        Mount(source='/Users/pochaowang/.dbt',target='/root',type='bind')
    ],  
    dag=dag
)

task1 >> task2