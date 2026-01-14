# 📊 Flujo del Sistema - Stock Analysis System

## 🔄 Arquitectura General (Docker Compose)

```
[Producer] → [Kafka] → [Consumer] → [MongoDB] → [Batch (cron)] → [MySQL]
                          ↓            ↓                             ↓
                     [Alertas]    [News Scraper]              [Dashboard Flask]
                          ↓            ↓ (cron)                     ↓
                      [Email]      [Email Daily]                [Grafana]

                    [Elasticsearch] ← [Logs de todos los componentes]
                          ↓
                      [Kibana]
```

**Contenedores Docker:** 13 servicios en docker-compose.yml
- Infraestructura: Zookeeper, Kafka, MongoDB, MySQL, Elasticsearch, Kibana
- Procesamiento: Producer, Consumer, Alerts, Batch (cron), News (cron)
- Visualización: Flask (5000), Grafana (3000)

---

## 📝 Flujo Detallado de Datos

### 1️⃣ **Generación de Datos en Tiempo Real**

**Archivo:** `streaming/producer.py` (Dockerizado)

**Proceso:**
1. Se conecta a **Alpha Vantage API** para obtener datos reales de acciones (AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA)
2. Fallback a datos simulados si alcanza límite de API (5 llamadas/minuto)
3. Cada 15 segundos captura:
   - Precio actual
   - Volumen
   - Precio de apertura/cierre
   - High/Low del día
   - Cambio porcentual
4. Serializa los datos a JSON
5. Envía el mensaje al topic `stock-prices` de **Kafka**

**API:** Alpha Vantage (key en .env: BKK5OMNA2MT9CYZC)

**Salida:** Mensajes JSON en Kafka
```json
{
  "symbol": "AAPL",
  "timestamp": "2026-01-13T15:30:00",
  "price": 261.05,
  "volume": 287051,
  "open": 260.22,
  "high": 261.35,
  "low": 260.19,
  "change_percent": 0.32
}
```

---

### 2️⃣ **Distribución de Mensajes**

**Servicio:** Apache Kafka + Zookeeper

**Proceso:**
1. Kafka recibe mensajes del producer
2. Los almacena temporalmente en el topic `stock-prices` (3 particiones)
3. Distribuye los mensajes a todos los consumers suscritos
4. Garantiza entrega y orden de mensajes

**Rol:** Message broker / Cola de mensajes distribuida

---

### 3️⃣ **Consumo y Almacenamiento en Tiempo Real**

**Archivo:** `streaming/consumer.py` (Refactorizado - usa kafka-python en lugar de Spark)

**Proceso:**
1. Se suscribe al topic `stock-prices` de Kafka
2. Consume mensajes en tiempo real (consumer group: `stock-consumer-group`)
3. Para cada mensaje:
   - Deserializa el JSON
   - Calcula `price_change_pct` adicional
   - Agrega timestamp de procesamiento
   - Inserta en **MongoDB** (colección `realtime_prices`)
4. Log de cada mensaje procesado

**Nota:** Archivo original mantenido pero completamente reescrito sin PySpark (solo kafka-python + pymongo)

**Base de Datos:** MongoDB
- **Database:** `stock_market`
- **Colección:** `realtime_prices`
- **Documentos:** 100+ registros en tiempo real

---

### 4️⃣ **Sistema de Alertas en Tiempo Real**

**Archivo:** `streaming/alerts.py` (Dockerizado)

**Proceso:**
1. También consume del topic `stock-prices` de Kafka
2. Analiza cada mensaje en busca de condiciones de alerta:
   - **Cambio de precio > 5%** (configurable en `.env`)
   - **Volumen anormalmente alto** (> 2x promedio)
3. Cuando detecta una alerta:
   - Registra en logs
   - Envía email de notificación (requiere credenciales SMTP en .env)
   - Guarda en MySQL (tabla `alert_log`)

**Configuración:** `.env`
```
PRICE_CHANGE_THRESHOLD=5.0
VOLUME_THRESHOLD_MULTIPLIER=2.0
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=tu_email@gmail.com
EMAIL_PASSWORD=contraseña_de_aplicacion
```

---

### 5️⃣ **Procesamiento Batch Diario (Automatizado)**

**Archivo:** `batch/daily_aggregation.py` (Dockerizado con cron)

**Proceso:**
1. Se ejecuta **automáticamente a las 00:00** via cron job en contenedor Docker
2. Lee datos de **MongoDB** del día actual (o día anterior)
3. Para cada símbolo de acción:
   - Calcula métricas agregadas:
     - Precio de apertura/cierre
     - Precio máximo/mínimo
     - Precio promedio
     - Volumen total y promedio
     - Volatilidad (desviación estándar)
     - Cambio porcentual diario
   - Calcula indicadores técnicos:
     - SMA (Simple Moving Average) - 20 períodos
     - RSI (Relative Strength Index)
4. Guarda resultados en **MySQL** (tabla `daily_aggregates`)
5. Limpia datos antiguos de MongoDB (retiene 90 días)

**Cron Job:** `0 0 * * *` (medianoche diaria)

**Base de Datos:** MySQL
- **Database:** `stock_analytics`
- **Tabla principal:** `daily_aggregates`
- **Puerto:** 3307 (externo), 3306 (interno Docker)
- **Registros:** 1 por día por acción (7 acciones monitoreadas)

---

### 6️⃣ **News Scraper & Email Service (Automatizado)**

**Archivos:** `articles/daily_news.py`, `articles/news_scraper.py`, `articles/email_sender.py` (Dockerizado con cron)

**Proceso:**
1. Se ejecuta **automáticamente a las 08:00 AM** via cron job en contenedor Docker
2. **Scraper de noticias:**
   - Busca noticias de Yahoo Finance, Google News, Alpha Vantage
   - Para cada acción monitoreada (7 símbolos)
   - Extrae: título, resumen, fuente, fecha, URL
   - Filtra noticias relevantes
   - Almacena en **MongoDB** (colección `news_articles`)
3. **Email Service:**
   - Lee usuarios registrados de MongoDB
   - Genera resumen HTML con noticias del día
   - Envía email a cada usuario
   - Log de emails enviados

**Cron Job:** `0 8 * * *` (08:00 AM diaria)

**Configuración SMTP requerida en .env:**
- Gmail: Contraseña de aplicación (no contraseña normal)
- Acceso en: https://myaccount.google.com → Seguridad → Contraseñas de aplicaciones

---

### 7️⃣ **Aplicación Web (Dashboard)**

**Archivo:** `flask_web_app/app.py` (Dockerizado)

**Proceso:**
1. Aplicación Flask corriendo en `http://localhost:5000`
2. **Rutas principales:**
   - `/` - Página principal con precios en tiempo real
   - `/dashboard` - Dashboard con gráficos y análisis
   - `/register` - Registro de usuarios

3. **Fuentes de datos:**
   - **MongoDB** → Datos en tiempo real (últimos precios)
   - **MySQL** → Datos agregados y métricas históricas
   - **MongoDB (users)** → Autenticación de usuarios

4. **Plantillas:** `templates/`
   - `base.html` - Layout base
   - `index.html` - Página principal
   - `dashboard.html` - Dashboard de análisis
   - `register.html` - Formulario de registro

**Acceso:** http://localhost:5000

---

### 8️⃣ **Grafana - Visualización Avanzada**

**Servicio:** Grafana (Dockerizado)

**Acceso:** http://localhost:3000
- **Usuario:** admin
- **Contraseña:** admin

**Proceso:**
1. Datasource configurado automáticamente:
   - MySQL Stock Analytics (mysql:3306)
   - Conexión a `stock_analytics` database
2. Dashboard pre-configurado: "Stock Market Analytics Dashboard"
3. **Paneles incluidos:**
   - Stock Price Trends (30 días)
   - Trading Volume (30 días)
   - Daily Change % (gauges)
   - RSI Indicator (30 días)
   - Stock Performance Summary (tabla)
4. Auto-refresh cada 30 segundos

**Directorio de configuración:** `grafana/provisioning/`
- `datasources/mysql.yml` - Conexión a MySQL
- `dashboards/stock-analytics.json` - Dashboard principal

---

### 9️⃣ **Sistema de Logs Centralizado**

**Archivo:** `logs/logger_config.py`

**Proceso:**
1. Todos los componentes del sistema usan el logger centralizado
2. Cada log se envía a:
   - **Consola** (stdout) → Para desarrollo
   - **Elasticsearch** → Para almacenamiento y búsqueda
3. Estructura de logs:
   ```json
   {
     "timestamp": "2026-01-13T15:30:00",
     "level": "INFO",
     "logger": "kafka_producer",
     "message": "Mensaje enviado a Kafka",
     "module": "producer",
     "function": "send_message",
     "line": 45
   }
   ```

**Elasticsearch:**
- **Índice:** `stock-system-logs`
- **Host:** localhost:9200

---

### 🔟 **Visualización de Logs**

**Servicio:** Kibana (Dockerizado)

**Acceso:** http://localhost:5601

**Configuración:**
- Índice: `stock-system-logs`
- Conectado a Elasticsearch (elasticsearch:9200)
- 260+ log entries de todos los servicios

**Funcionalidad:**
- Búsqueda de logs en tiempo real
- Filtros por nivel (INFO, WARNING, ERROR)
- Filtros por componente (producer, consumer, batch, etc.)
- Visualizaciones y dashboards de logs
- Detección de errores y patrones

---

## 🗂️ Estructura de Bases de Datos

### MongoDB (Datos en Tiempo Real)
```
stock_market/
├── realtime_prices     → Datos de streaming (100+ docs)
├── news_articles       → Artículos scrapeados (diarios)
├── users              → Usuarios de la app Flask
└── alert_history      → Historial de alertas
```

### MySQL (Datos Agregados)
```
stock_analytics/
├── daily_aggregates    → Agregados diarios (7 acciones)
├── weekly_aggregates   → Resúmenes semanales
├── stock_performance   → Métricas de performance
└── alert_log          → Log de alertas enviadas
```

### Elasticsearch (Logs)
```
stock-system-logs/     → Logs de todos los componentes
```

---

## 🔧 Componentes Opcionales (No Configurados)

### AWS S3
**Archivo:** `streaming/consumer.py` (método deshabilitado)
- Archivaría datos históricos en formato Parquet
- Particionado por símbolo de acción
- Para análisis a largo plazo

### Apache Airflow
**Archivos:** `airflow/dags/` (no dockerizados)
- `daily_batch_dag.py` → Orquestación del batch diario
- `news_pipeline_dag.py` → Pipeline de scraping de noticias
- `maintenance_dag.py` → Tareas de mantenimiento

**Nota:** Sistema usa cron jobs en Docker en lugar de Airflow

---

## 📊 Ejemplo de Flujo Completo

### Escenario: Nueva actualización de precio de AAPL

**T+0s:** Producer obtiene precio de AAPL ($260.21)
```
streaming/producer.py → yfinance API
```

**T+0.1s:** Envío a Kafka
```
Producer → Kafka (topic: stock-prices)
```

**T+0.2s:** Consumer procesa el mensaje
```
Kafka → consumer_simple.py → MongoDB (realtime_prices)
Log: "Mensaje procesado - Symbol: AAPL, Price: $260.21"
```

**T+0.2s:** Sistema de alertas verifica condiciones
```
Kafka → alerts_simple.py
Verifica: ¿Cambio > 5%? NO
Verifica: ¿Volumen alto? NO
→ No se envía alerta
```

**T+0.3s:** Flask actualiza dashboard
```
MongoDB → Flask App → Usuario ve $260.21 en tiempo real
```

**T+0.3s:** Logs enviados a Elasticsearch
```
logger → Elasticsearch (stock-system-logs)
→ Disponible en Kibana
```

**T+24h:** Batch nocturno procesa el día
```
batch/daily_aggregation.py:
1. Lee todos los registros de AAPL del día desde MongoDB
2. Calcula: open=$260.53, close=$260.21, avg=$260.37
3. Calcula: volatility=0.15, change%=-0.12%
4. Guarda en MySQL (daily_aggregates)
5. Disponible en Flask Dashboard histórico
```

---

## 🚀 Orden de Inicio del Sistema (Docker Compose)

**Comando único:** `docker-compose up -d`

**Orden automático de dependencias:**
1. **Zookeeper** (prerequisito de Kafka)
2. **Kafka** (message broker) - healthcheck activado
3. **MongoDB** (base de datos NoSQL) - healthcheck activado
4. **MySQL** (base de datos SQL) - healthcheck activado
5. **Elasticsearch** (motor de logs) - healthcheck activado
6. **Kibana** (visualización de logs)
7. **Producer** (depende de Kafka)
8. **Consumer** (depende de Kafka + MongoDB)
9. **Alerts** (depende de Kafka)
10. **Flask App** (depende de MongoDB + MySQL)
11. **Batch** (depende de MongoDB + MySQL) - cron 00:00
12. **News** (depende de MongoDB) - cron 08:00
13. **Grafana** (depende de MySQL)

**Verificar estado:** `docker ps`
**Ver logs:** `docker-compose logs -f [servicio]`
**Reiniciar todo:** `docker-compose restart`
**Detener todo:** `docker-compose down`

---

## 📁 Archivos Clave por Componente

### Streaming
- `streaming/producer.py` - Producer con Alpha Vantage API ✅ (Dockerizado)
- `streaming/consumer.py` - Consumer refactorizado (kafka-python) ✅ (Dockerizado)
- `streaming/alerts.py` - Sistema de alertas ✅ (Dockerizado)

### Batch
- `batch/daily_aggregation.py` - Procesamiento diario ✅ (Dockerizado + cron 00:00)

### News & Email
- `articles/daily_news.py` - Script principal ✅ (Dockerizado + cron 08:00)
- `articles/news_scraper.py` - Scraper de noticias ✅
- `articles/email_sender.py` - Envío de emails ✅

### Web
- `flask_web_app/app.py` - Aplicación Flask ✅ (Dockerizado)
- `flask_web_app/templates/*.html` - Plantillas HTML ✅

### Configuración
- `.env` - Variables de entorno ✅
- `config/config.py` - Configuración centralizada ✅
- `docker-compose.yml` - Orquestación de 13 servicios ✅
- `Dockerfile.producer` - Imagen del producer ✅
- `Dockerfile.consumer` - Imagen del consumer ✅
- `Dockerfile.alerts` - Imagen de alertas ✅
- `Dockerfile.flask` - Imagen de Flask ✅
- `Dockerfile.batch` - Imagen de batch con cron ✅
- `Dockerfile.news` - Imagen de news con cron ✅

### Logs
- `logs/logger_config.py` - Sistema de logging ✅

### Base de Datos
- `database/mysql_schema.sql` - Schema de MySQL ✅
- `database/setup_mongodb.py` - Setup de MongoDB

### Grafana
- `grafana/provisioning/datasources/mysql.yml` - Datasource ✅
- `grafana/provisioning/dashboards/stock-analytics.json` - Dashboard ✅

---

## ✅ Estado Actual del Sistema

### Componentes Activos (Docker Compose)
- ✅ Zookeeper + Kafka (streaming)
- ✅ Producer con Alpha Vantage API (datos reales + fallback simulado)
- ✅ Consumer refactorizado (kafka-python, sin Spark)
- ✅ MongoDB (100+ documentos en realtime_prices)
- ✅ MySQL puerto 3307 (7 acciones en daily_aggregates)
- ✅ Batch processing **automatizado** (cron 00:00 diaria)
- ✅ News Scraper + Email **automatizado** (cron 08:00 diaria)
- ✅ Flask App (http://localhost:5000)
- ✅ Sistema de alertas (requiere SMTP configurado)
- ✅ Elasticsearch + Kibana (http://localhost:5601, 260+ logs)
- ✅ Grafana (http://localhost:3000, dashboards pre-configurados)

### Total: 13 contenedores Docker

### Componentes Pendientes
- ⏳ AWS S3 (archivado histórico)
- ⏳ Airflow (reemplazado por cron jobs)
- ⏳ Configuración SMTP para emails (requiere credenciales de usuario)

---

## 🔍 Monitoreo del Sistema

### Verificar que todo funcione (Docker):

**Ver todos los contenedores:**
```bash
docker ps
```

**Ver logs de un servicio:**
```bash
docker-compose logs -f producer
docker-compose logs -f consumer
docker-compose logs -f batch
docker-compose logs -f news
```

**Acceder a servicios web:**
- **Flask Dashboard**: http://localhost:5000
- **Grafana Analytics**: http://localhost:3000 (admin/admin)
- **Kibana Logs**: http://localhost:5601

### Ver datos directamente:

**MongoDB (desde contenedor):**
```bash
docker exec -it mongodb mongosh
use stock_market
db.realtime_prices.countDocuments()
db.realtime_prices.find().limit(5)
db.news_articles.countDocuments()
```

**MySQL (desde contenedor):**
```bash
docker exec -it mysql mysql -uroot -ppascualina stock_analytics
SELECT * FROM daily_aggregates ORDER BY date DESC LIMIT 10;
SELECT symbol, avg_price, daily_change_pct FROM daily_aggregates WHERE date = CURDATE();
```

**Elasticsearch:**
```bash
curl http://localhost:9200/_cat/indices
curl http://localhost:9200/stock-system-logs/_count
```

### Ejecutar procesos manualmente:

**Batch diario:**
```bash
docker exec batch python batch/daily_aggregation.py
```

**News scraper:**
```bash
docker exec news python articles/daily_news.py
```

---

## 📞 Flujo de Alertas

```
[Kafka] → [alerts_simple.py]
              ↓
    ¿Precio cambió > 5%?
              ↓ SÍ
    [Registra en MySQL]
              ↓
    [Envía Email] (si configurado)
              ↓
    [Log en Elasticsearch]
```

**Configuración de Email** (`.env`):
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
```

---

Este es el flujo completo del sistema Stock Analysis System. Todos los componentes trabajan juntos para proporcionar análisis en tiempo real y agregado de datos del mercado de valores.
