"""
Airflow DAG - Pipeline de Noticias
Scrapea noticias y envía resúmenes diarios
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.append('/path/to/data_project')  # Actualizar con la ruta real

from articles.news_scraper import NewsScraperService
from articles.email_sender import NewsEmailService
from config.config import Config

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': [Config.SMTP_CONFIG['sender']],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}


def scrape_news(**context):
    """Scrapea noticias de acciones"""
    scraper = NewsScraperService()
    try:
        articles = scraper.scrape_all_stocks()
        context['task_instance'].xcom_push(key='articles_count', value=len(articles))
        return f"Scraped {len(articles)} articles"
    except Exception as e:
        raise Exception(f"Error scraping news: {e}")
    finally:
        scraper.close()


def send_news_summaries(**context):
    """Envía resúmenes de noticias a usuarios"""
    email_service = NewsEmailService()
    try:
        email_service.send_daily_summaries()
        return "News summaries sent"
    except Exception as e:
        raise Exception(f"Error sending news summaries: {e}")
    finally:
        email_service.close()


with DAG(
    'news_pipeline',
    default_args=default_args,
    description='Pipeline para scrapear y enviar noticias de acciones',
    schedule_interval='0 9 * * *',  # 9:00 AM todos los días
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['news', 'scraping', 'daily'],
) as dag:
    
    # Tarea 1: Scrapear noticias
    scrape_task = PythonOperator(
        task_id='scrape_stock_news',
        python_callable=scrape_news,
        provide_context=True,
    )
    
    # Tarea 2: Enviar resúmenes
    send_summaries_task = PythonOperator(
        task_id='send_news_summaries',
        python_callable=send_news_summaries,
        provide_context=True,
    )
    
    # Tarea 3: Notificar completado
    success_email = EmailOperator(
        task_id='send_completion_notification',
        to=Config.SMTP_CONFIG['sender'],
        subject='📰 Pipeline de Noticias - Completado',
        html_content="""
        <h2>Pipeline de Noticias Completado</h2>
        <p>Las noticias han sido scrapeadas y los resúmenes enviados.</p>
        <p><strong>Fecha:</strong> {{ ds }}</p>
        <p><strong>Artículos procesados:</strong> {{ task_instance.xcom_pull(task_ids='scrape_stock_news', key='articles_count') }}</p>
        """,
    )
    
    # Definir dependencias
    scrape_task >> send_summaries_task >> success_email
