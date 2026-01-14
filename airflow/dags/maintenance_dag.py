"""
Airflow DAG - Mantenimiento y Limpieza
Tareas de mantenimiento del sistema
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.append('/path/to/data_project')  # Actualizar con la ruta real

from pymongo import MongoClient
import mysql.connector
from config.config import Config

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': [Config.SMTP_CONFIG['sender']],
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def cleanup_elasticsearch_logs(**context):
    """Limpia logs antiguos de Elasticsearch"""
    from elasticsearch import Elasticsearch
    
    es = Elasticsearch([{
        'host': Config.ELASTICSEARCH_CONFIG['host'],
        'port': Config.ELASTICSEARCH_CONFIG['port'],
        'scheme': 'http'
    }])
    
    # Eliminar logs de más de 30 días
    cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
    
    query = {
        "query": {
            "range": {
                "timestamp": {
                    "lt": cutoff_date
                }
            }
        }
    }
    
    result = es.delete_by_query(index=Config.ES_INDEX_LOGS, body=query)
    return f"Deleted {result['deleted']} log entries"


def optimize_mysql_tables(**context):
    """Optimiza tablas de MySQL"""
    conn = mysql.connector.connect(**Config.MYSQL_CONFIG)
    cursor = conn.cursor()
    
    tables = ['daily_aggregates', 'weekly_aggregates', 'stock_performance', 'alert_log']
    
    for table in tables:
        cursor.execute(f"OPTIMIZE TABLE {table}")
    
    cursor.close()
    conn.close()
    
    return f"Optimized {len(tables)} tables"


def compact_mongodb_collections(**context):
    """Compacta colecciones de MongoDB"""
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.MONGO_DB_NAME]
    
    collections = [
        Config.MONGO_COLLECTION_REALTIME,
        Config.MONGO_COLLECTION_ARTICLES,
        Config.MONGO_COLLECTION_ALERTS
    ]
    
    for collection_name in collections:
        db.command('compact', collection_name)
    
    client.close()
    
    return f"Compacted {len(collections)} collections"


with DAG(
    'maintenance_pipeline',
    default_args=default_args,
    description='Pipeline de mantenimiento y limpieza del sistema',
    schedule_interval='0 2 * * 0',  # 2:00 AM todos los domingos
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['maintenance', 'cleanup', 'weekly'],
) as dag:
    
    # Tarea 1: Limpiar logs de Elasticsearch
    cleanup_es_task = PythonOperator(
        task_id='cleanup_elasticsearch_logs',
        python_callable=cleanup_elasticsearch_logs,
        provide_context=True,
    )
    
    # Tarea 2: Optimizar MySQL
    optimize_mysql_task = PythonOperator(
        task_id='optimize_mysql_tables',
        python_callable=optimize_mysql_tables,
        provide_context=True,
    )
    
    # Tarea 3: Compactar MongoDB
    compact_mongo_task = PythonOperator(
        task_id='compact_mongodb_collections',
        python_callable=compact_mongodb_collections,
        provide_context=True,
    )
    
    # Tarea 4: Verificar espacio en disco
    check_disk_space = BashOperator(
        task_id='check_disk_space',
        bash_command='df -h',
    )
    
    # Ejecutar tareas en paralelo
    [cleanup_es_task, optimize_mysql_task, compact_mongo_task] >> check_disk_space
