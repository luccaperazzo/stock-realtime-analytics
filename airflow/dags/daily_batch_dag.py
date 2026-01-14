"""
Airflow DAG - Pipeline Batch Diario
Ejecuta el procesamiento batch de datos cada día a medianoche
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
import sys
import os

# Agregar path del proyecto
sys.path.append('/path/to/data_project')  # Actualizar con la ruta real

from batch.daily_aggregation import DailyAggregation
from config.config import Config

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': [Config.SMTP_CONFIG['sender']],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}



def run_daily_aggregation(**context):
    """Ejecuta el procesamiento batch diario"""
    aggregator = DailyAggregation()
    try:
        aggregator.process_all_stocks()
        return "Agregación diaria completada exitosamente"
    except Exception as e:
        raise Exception(f"Error en agregación diaria: {e}")
    finally:
        aggregator.close()


def cleanup_old_data(**context):
    """Limpia datos antiguos de MongoDB"""
    aggregator = DailyAggregation()
    try:
        aggregator.cleanup_old_data(days_to_keep=90)
        return "Limpieza completada"
    except Exception as e:
        raise Exception(f"Error en limpieza: {e}")
    finally:
        aggregator.close()


with DAG(
    'daily_batch_pipeline',
    default_args=default_args,
    description='Pipeline batch para procesamiento diario de datos de acciones',
    schedule_interval='0 0 * * *',  # Medianoche todos los días
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['batch', 'daily', 'stocks'],
) as dag:
    
    # Tarea 1: Procesar agregaciones diarias
    aggregate_task = PythonOperator(
        task_id='run_daily_aggregation',
        python_callable=run_daily_aggregation,
        provide_context=True,
    )
    
    # Tarea 2: Limpiar datos antiguos
    cleanup_task = PythonOperator(
        task_id='cleanup_old_data',
        python_callable=cleanup_old_data,
        provide_context=True,
    )
    
    # Tarea 3: Notificar éxito
    success_email = EmailOperator(
        task_id='send_success_email',
        to=Config.SMTP_CONFIG['sender'],
        subject='✅ Pipeline Batch Diario - Completado',
        html_content="""
        <h2>Pipeline Batch Diario Completado</h2>
        <p>El procesamiento batch del día {{ ds }} se ha completado exitosamente.</p>
        <p><strong>Fecha de ejecución:</strong> {{ execution_date }}</p>
        <p><strong>Acciones procesadas:</strong> {{ var.value.get('STOCKS_TO_MONITOR', []) }}</p>
        """,
    )
    
    # Definir dependencias
    aggregate_task >> cleanup_task >> success_email
