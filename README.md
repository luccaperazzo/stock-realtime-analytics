# 📈 Sistema de Análisis y Alertas de Acciones

Sistema completo de ingeniería de datos para monitoreo, análisis y alertas del mercado de valores en tiempo real.

## 🏗️ Arquitectura del Sistema

```
[API Stocks] → [Kafka Producer] → [Kafka Topic]
                                         ↓
                              [Spark Streaming Consumer]
                                         ↓
                    ┌────────────────────┼────────────────────┐
                    ↓                    ↓                    ↓
              [MongoDB]            [Amazon S3]           [Alert Service]
                                                              ↓
                                                         [Email Users]

[Daily Batch Job] → [MySQL] → [Grafana Dashboard]
[News Scraper] → [MongoDB] → [Email Summary]
[All Services] → [Elasticsearch] → [Kibana]
[Flask App] → [MongoDB/MySQL] (read-only)
```

## 🛠️ Stack Tecnológico

- **Streaming**: Apache Kafka, Apache Spark Structured Streaming
- **Orquestación**: Apache Airflow
- **Bases de Datos**: MongoDB, MySQL, Elasticsearch
- **Almacenamiento**: Amazon S3
- **Visualización**: Grafana, Kibana
- **Web**: Flask, Python
- **APIs**: Yahoo Finance, Alpha Vantage

## 📁 Estructura del Proyecto

```
data_project/
├── streaming/          # Pipeline en tiempo real
├── batch/             # Pipeline batch diario
├── articles/          # Pipeline de noticias
├── logs/              # Sistema de logging
├── flask_web_app/     # Aplicación web
├── airflow/           # DAGs de Airflow
├── config/            # Configuraciones
├── database/          # Scripts de BD
├── tests/             # Tests unitarios
└── requirements.txt   # Dependencias
```

## 🚀 Instalación

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

## ⚙️ Configuración

1. **Kafka**: Iniciar Zookeeper y Kafka broker
2. **MongoDB**: Configurar instancia local o cloud
3. **MySQL**: Crear base de datos y tablas
4. **Elasticsearch**: Configurar cluster
5. **AWS S3**: Configurar bucket y credenciales

Ver [SETUP.md](docs/SETUP.md) para instrucciones detalladas.

## 🏃 Ejecución

### Pipeline en Tiempo Real
```bash
# Iniciar Kafka producer
python streaming/producer.py

# Iniciar Spark consumer
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 streaming/consumer.py
```

### Pipeline Batch
```bash
# Ejecución manual
python batch/daily_aggregation.py

# Con Airflow
airflow dags trigger daily_batch_pipeline
```

### Aplicación Web
```bash
python flask_web_app/app.py
# Visitar http://localhost:5000
```

## 📊 Dashboards

- **Grafana**: http://localhost:3000 - Métricas de mercado
- **Kibana**: http://localhost:5601 - Logs del sistema
- **Flask App**: http://localhost:5000 - Interfaz de usuario

## 🔔 Sistema de Alertas

Las alertas se envían por email cuando:
- Cambio de precio > 5% (configurable)
- Volumen inusualmente alto
- Noticias relevantes detectadas

## 📝 Licencia

MIT License
