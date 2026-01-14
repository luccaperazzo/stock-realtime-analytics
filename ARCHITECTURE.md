# Sistema de Análisis y Alertas de Acciones

## 📋 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAPA DE INGESTA                               │
├─────────────────────────────────────────────────────────────────────┤
│  APIs Externas (Yahoo Finance, Alpha Vantage)                       │
│            ↓                                                         │
│  Kafka Producer → Kafka Topic (stock-prices)                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PROCESAMIENTO                             │
├─────────────────────────────────────────────────────────────────────┤
│  Spark Streaming Consumer                                           │
│    - Procesamiento en tiempo real                                   │
│    - Detección de cambios significativos                            │
│    - Cálculo de métricas                                            │
└─────────────────────────────────────────────────────────────────────┘
            ↓                    ↓                    ↓
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   MongoDB        │  │   Amazon S3      │  │  Alert System    │
│  (Tiempo Real)   │  │   (Archivo)      │  │  (Emails)        │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA BATCH                                      │
├─────────────────────────────────────────────────────────────────────┤
│  Daily Aggregation Job (Airflow)                                    │
│    ↓                                                                 │
│  MySQL (Datos Históricos Agregados)                                 │
│    ↓                                                                 │
│  Grafana Dashboards                                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE NOTICIAS                                  │
├─────────────────────────────────────────────────────────────────────┤
│  News Scraper (Airflow) → MongoDB → Email Summaries                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   CAPA DE MONITOREO                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Todos los servicios → Elasticsearch → Kibana                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                  CAPA DE PRESENTACIÓN                                │
├─────────────────────────────────────────────────────────────────────┤
│  Flask Web App (http://localhost:5000)                              │
│    - Visualización en tiempo real                                   │
│    - Registro de usuarios                                           │
│    - Configuración de alertas                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Componentes del Sistema

### 1. **Streaming Pipeline** (40%)
- **Kafka Producer**: Captura datos cada 10 segundos
- **Spark Consumer**: Procesa streams en micro-batches
- **Alert System**: Detecta cambios >5% y envía emails
- **Storage**: MongoDB (tiempo real) + S3 (archivo)

### 2. **Batch Pipeline** (25%)
- **Daily Job**: Agregación a las 00:00
- **Métricas**: Precio promedio, máx, mín, volumen
- **Indicadores**: SMA, RSI
- **Storage**: MySQL
- **Visualización**: Grafana

### 3. **News Pipeline** (15%)
- **Scraper**: Yahoo Finance news
- **Filtrado**: Keywords relevantes
- **Storage**: MongoDB
- **Email**: Resumen diario

### 4. **Logging System** (10%)
- **Centralized**: Elasticsearch
- **Levels**: INFO, WARNING, ERROR
- **Visualization**: Kibana

### 5. **Web Application** (10%)
- **Framework**: Flask
- **Features**: Tiempo real, registro, alertas
- **Updates**: Auto-refresh AJAX

### 6. **Orchestration** (Bonus +10%)
- **Airflow**: 3 DAGs principales
- **Scheduling**: Automatización
- **Monitoring**: Estado de pipelines

## 📊 Tecnologías Utilizadas

| Categoría | Tecnología | Propósito |
|-----------|-----------|-----------|
| **Streaming** | Apache Kafka | Mensajería en tiempo real |
| **Processing** | Apache Spark | Procesamiento de streams |
| **Orchestration** | Apache Airflow | Scheduling y DAGs |
| **Databases** | MongoDB, MySQL | NoSQL + Relacional |
| **Search** | Elasticsearch | Logs centralizados |
| **Storage** | Amazon S3 | Archivo de datos |
| **Visualization** | Grafana, Kibana | Dashboards y logs |
| **Web** | Flask | Interfaz de usuario |
| **Language** | Python 3.9+ | Lenguaje principal |

## 📁 Estructura del Proyecto

```
data_project/
├── streaming/              # Pipeline en tiempo real
│   ├── producer.py        # Kafka producer
│   ├── consumer.py        # Spark streaming
│   └── alerts.py          # Sistema de alertas
├── batch/                 # Pipeline batch
│   └── daily_aggregation.py
├── articles/              # Pipeline de noticias
│   ├── news_scraper.py
│   └── email_sender.py
├── logs/                  # Sistema de logging
│   └── logger_config.py
├── flask_web_app/         # Aplicación web
│   ├── app.py
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── register.html
│       ├── dashboard.html
│       └── error.html
├── airflow/               # Orquestación
│   ├── dags/
│   │   ├── daily_batch_dag.py
│   │   ├── news_pipeline_dag.py
│   │   └── maintenance_dag.py
│   └── airflow.cfg
├── database/              # Schemas y setup
│   ├── mysql_schema.sql
│   └── setup_mongodb.py
├── config/                # Configuración
│   └── config.py
├── tests/                 # Tests unitarios
│   └── test_system.py
├── docs/                  # Documentación
│   ├── SETUP.md
│   └── USAGE.md
├── requirements.txt       # Dependencias
├── .env.example          # Variables de entorno
├── start_system.py       # Script de inicio
└── README.md             # Este archivo
```

## 🚀 Inicio Rápido

### Instalación:
```powershell
# 1. Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales

# 4. Configurar bases de datos
python database/setup_mongodb.py
mysql -u root -p < database/mysql_schema.sql
```

### Ejecución:
```powershell
# Opción 1: Script de inicio automático
python start_system.py

# Opción 2: Iniciar componentes individualmente
python streaming/producer.py          # Terminal 1
python streaming/alerts.py            # Terminal 2
python flask_web_app/app.py           # Terminal 3
spark-submit streaming/consumer.py    # Terminal 4
```

## 📖 Documentación Completa

- **[SETUP.md](docs/SETUP.md)**: Instalación detallada de todos los componentes
- **[USAGE.md](docs/USAGE.md)**: Guía de uso del sistema

## 🌐 Interfaces del Sistema

- **Flask Web App**: http://localhost:5000
- **Airflow**: http://localhost:8080
- **Grafana**: http://localhost:3000
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

## ✨ Características Principales

### ✅ Pipeline en Tiempo Real
- ✓ Monitoreo de 7 acciones principales
- ✓ Actualización cada 10 segundos
- ✓ Detección automática de cambios >5%
- ✓ Alertas por email personalizables
- ✓ Archivo en S3 para análisis histórico

### ✅ Procesamiento Batch
- ✓ Agregación diaria automática
- ✓ Cálculo de indicadores técnicos (SMA, RSI)
- ✓ Almacenamiento en MySQL
- ✓ Limpieza automática de datos antiguos
- ✓ Dashboards en Grafana

### ✅ Noticias
- ✓ Scraping diario de Yahoo Finance
- ✓ Filtrado por relevancia
- ✓ Resumen diario por email
- ✓ Almacenamiento en MongoDB

### ✅ Monitoreo
- ✓ Logs centralizados en Elasticsearch
- ✓ Visualización en Kibana
- ✓ Alertas de errores
- ✓ Métricas de performance

### ✅ Web App
- ✓ Precios en tiempo real
- ✓ Registro de usuarios
- ✓ Configuración de alertas
- ✓ Dashboards interactivos
- ✓ Auto-refresh

### ✅ Orquestación
- ✓ 3 DAGs de Airflow
- ✓ Scheduling automático
- ✓ Reintentos en fallos
- ✓ Notificaciones por email

## 🧪 Testing

```powershell
# Ejecutar tests
pytest tests/test_system.py -v

# Con coverage
pytest tests/test_system.py --cov=. --cov-report=html
```

## 🔧 Configuración

### Acciones Monitoreadas (config/config.py):
```python
STOCKS_TO_MONITOR = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']
```

### Umbrales de Alertas:
```python
PRICE_CHANGE_THRESHOLD = 5.0  # Porcentaje
VOLUME_THRESHOLD_MULTIPLIER = 2.0
```

### Intervalos:
```python
PRODUCER_FETCH_INTERVAL = 10  # segundos
SPARK_BATCH_DURATION = 30     # segundos
```

## 📊 Dashboards Sugeridos

### Grafana:
1. **Stock Prices Overview**: Precios de cierre últimos 30 días
2. **Volume Analysis**: Volumen por acción
3. **Performance Comparison**: Comparación entre acciones
4. **Technical Indicators**: SMA y RSI

### Kibana:
1. **System Health**: Estado de servicios
2. **Error Monitoring**: Logs de errores
3. **Performance Metrics**: Latencia y throughput
4. **Alert History**: Histórico de alertas

## 🤝 Contribuciones

Este es un proyecto educativo completo de ingeniería de datos.

## 📝 Licencia

MIT License - Ver archivo LICENSE

## 📞 Soporte

Para problemas o preguntas:
1. Revisar documentación en `/docs`
2. Ver logs en Kibana
3. Verificar estado de servicios

---

**Desarrollado como proyecto de Ingeniería de Datos**  
*Stack completo: Kafka + Spark + Airflow + MongoDB + MySQL + Elasticsearch + Flask*
