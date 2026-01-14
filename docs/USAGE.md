# 📖 Guía de Uso del Sistema

## 🎯 Flujo de Trabajo del Sistema

### 1. Pipeline en Tiempo Real (Streaming)

#### Iniciar Producer
```powershell
python streaming/producer.py
```

**Qué hace:**
- Consulta APIs de Yahoo Finance cada 10 segundos
- Obtiene precios en tiempo real de las acciones configuradas
- Publica datos en Kafka topic `stock-prices`

#### Iniciar Consumer
```powershell
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 streaming/consumer.py
```

**Qué hace:**
- Consume datos del topic de Kafka
- Procesa en micro-batches
- Detecta cambios significativos de precio
- Almacena en MongoDB
- Genera alertas cuando hay cambios > 5%

#### Iniciar Sistema de Alertas
```powershell
python streaming/alerts.py
```

**Qué hace:**
- Monitorea MongoDB en busca de nuevas alertas
- Envía emails a usuarios suscritos
- Registra historial de alertas enviadas

---

### 2. Pipeline Batch Diario

#### Ejecución Manual
```powershell
python batch/daily_aggregation.py
```

#### Con Airflow (Automático)
```powershell
# Ver estado del DAG
airflow dags list

# Ejecutar manualmente
airflow dags trigger daily_batch_pipeline

# Ver logs
airflow tasks logs daily_batch_pipeline run_daily_aggregation 2026-01-13
```

**Qué hace:**
- Se ejecuta automáticamente a las 00:00
- Agrega datos del día anterior
- Calcula métricas: promedio, máximo, mínimo, volumen
- Calcula indicadores técnicos: SMA, RSI
- Guarda en MySQL
- Limpia datos antiguos de MongoDB (>90 días)

---

### 3. Pipeline de Noticias

#### Scraping Manual
```powershell
python articles/news_scraper.py
```

#### Enviar Resúmenes Manual
```powershell
python articles/email_sender.py
```

#### Con Airflow (Automático)
```powershell
# Ejecutar pipeline de noticias
airflow dags trigger news_pipeline
```

**Qué hace:**
- Se ejecuta automáticamente a las 09:00
- Scrapea noticias de Yahoo Finance
- Filtra noticias relevantes
- Guarda en MongoDB
- Envía resumen diario por email a usuarios

---

### 4. Aplicación Web

#### Iniciar Flask App
```powershell
python flask_web_app/app.py
```

**Acceder a:** http://localhost:5000

#### Funcionalidades:

**Página Principal:**
- Ver precios en tiempo real
- Ver cambios porcentuales
- Ver volumen de operaciones
- Auto-refresh cada 10 segundos

**Dashboard de Acción:**
- Acceder: http://localhost:5000/dashboard/AAPL
- Ver métricas detalladas
- Ver gráfico histórico
- Ver noticias recientes

**Registro de Usuario:**
- Acceder: http://localhost:5000/register
- Ingresar nombre y email
- Seleccionar acciones a monitorear
- Configurar umbral de alertas
- Habilitar resumen de noticias

---

## 🔔 Sistema de Alertas

### Configuración de Alertas

#### Por Usuario:
1. Registrarse en la web app
2. Seleccionar acciones
3. Configurar umbral (default: 5%)
4. Habilitar alertas

#### Tipos de Alertas:
- **Cambio de Precio**: Cuando el precio cambia más del umbral
- **Volumen Alto**: Cuando el volumen es inusualmente alto
- **Noticias**: Resumen diario de noticias

#### Ejemplo de Email de Alerta:
```
Asunto: 🔔 Alerta AAPL: +6.25%

Acción: AAPL
Precio Actual: $175.50
Cambio: +6.25%
Apertura: $165.00
Máximo: $176.00
Mínimo: $164.50
Volumen: 52,345,678
```

---

## 📊 Dashboards y Visualización

### Grafana Dashboards

#### Configurar MySQL Datasource:
1. Abrir http://localhost:3000
2. Configuration > Data Sources > Add MySQL
3. Host: `localhost:3306`
4. Database: `stock_analytics`
5. User: `root`
6. Password: tu_password

#### Crear Dashboard:
```sql
-- Query para gráfico de precios
SELECT 
    date as time,
    close_price as value,
    symbol
FROM daily_aggregates
WHERE symbol = 'AAPL'
ORDER BY date DESC
LIMIT 30
```

### Kibana Logs

#### Configurar Index Pattern:
1. Abrir http://localhost:5601
2. Management > Index Patterns
3. Crear pattern: `stock-system-logs*`
4. Time field: `@timestamp`

#### Ver Logs:
- Discover > Seleccionar index pattern
- Filtrar por level, module, etc.
- Crear visualizaciones

---

## 🤖 Orquestación con Airflow

### DAGs Disponibles:

#### 1. `daily_batch_pipeline`
- **Schedule**: Diario a las 00:00
- **Tareas**:
  1. Agregar datos del día
  2. Limpiar datos antiguos
  3. Enviar email de confirmación

#### 2. `news_pipeline`
- **Schedule**: Diario a las 09:00
- **Tareas**:
  1. Scrapear noticias
  2. Enviar resúmenes
  3. Notificar completado

#### 3. `maintenance_pipeline`
- **Schedule**: Semanal (domingos 02:00)
- **Tareas**:
  1. Limpiar logs de Elasticsearch
  2. Optimizar tablas MySQL
  3. Compactar colecciones MongoDB
  4. Verificar espacio en disco

### Comandos Útiles:

```powershell
# Listar DAGs
airflow dags list

# Ver estado de un DAG
airflow dags state daily_batch_pipeline 2026-01-13

# Ejecutar manualmente
airflow dags trigger daily_batch_pipeline

# Pausar/Despausar DAG
airflow dags pause daily_batch_pipeline
airflow dags unpause daily_batch_pipeline

# Ver logs de una tarea
airflow tasks logs daily_batch_pipeline run_daily_aggregation 2026-01-13

# Reintentar tarea fallida
airflow tasks clear daily_batch_pipeline -t run_daily_aggregation -s 2026-01-13 -e 2026-01-13
```

---

## 🔍 Monitoreo del Sistema

### Ver Logs en Tiempo Real:

```powershell
# Logs de Producer
# Se muestran en consola

# Logs de Consumer
# Se muestran en consola de Spark

# Logs en Elasticsearch
# Ver en Kibana: http://localhost:5601
```

### Verificar Estado de Servicios:

```powershell
# Kafka
.\kafka\bin\windows\kafka-topics.bat --describe --topic stock-prices --bootstrap-server localhost:9092

# MongoDB
python -c "from pymongo import MongoClient; print(MongoClient().stock_market.realtime_prices.count_documents({}))"

# MySQL
mysql -u root -p -e "SELECT COUNT(*) FROM stock_analytics.daily_aggregates"

# Elasticsearch
curl http://localhost:9200/_cat/indices?v
```

---

## 📈 Consultas Útiles

### MongoDB:

```javascript
// Últimos 10 precios de AAPL
db.realtime_prices.find({symbol: "AAPL"}).sort({timestamp: -1}).limit(10)

// Alertas del día
db.alert_history.find({
    timestamp: {
        $gte: new Date(new Date().setHours(0,0,0,0))
    }
})

// Usuarios registrados
db.users.find({alerts_enabled: true})
```

### MySQL:

```sql
-- Mejor día de AAPL
SELECT date, close_price, daily_change_pct
FROM daily_aggregates
WHERE symbol = 'AAPL'
ORDER BY daily_change_pct DESC
LIMIT 1;

-- Promedio semanal
SELECT 
    WEEK(date) as week,
    AVG(close_price) as avg_price,
    SUM(total_volume) as weekly_volume
FROM daily_aggregates
WHERE symbol = 'AAPL'
GROUP BY WEEK(date)
ORDER BY week DESC;

-- Top performers
SELECT symbol, AVG(daily_change_pct) as avg_change
FROM daily_aggregates
WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY symbol
ORDER BY avg_change DESC;
```

---

## 🛠️ Personalización

### Agregar Nuevas Acciones:

```python
# En config/config.py
STOCKS_TO_MONITOR = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
```

### Cambiar Intervalo de Producer:

```python
# En config/config.py
PRODUCER_FETCH_INTERVAL = 30  # segundos
```

### Cambiar Umbral de Alertas:

```python
# En config/config.py
PRICE_CHANGE_THRESHOLD = 3.0  # porcentaje
```

---

## 🐛 Debugging

### Producer no obtiene datos:
- Verificar conexión a internet
- Verificar APIs de Yahoo Finance funcionando
- Revisar rate limiting

### Consumer no procesa:
- Verificar Kafka esté corriendo
- Verificar topic existe
- Revisar logs de Spark

### Alertas no se envían:
- Verificar configuración SMTP
- Verificar usuarios registrados
- Revisar logs del alert service

### Web app no muestra datos:
- Verificar MongoDB tiene datos
- Verificar producer y consumer corriendo
- Revisar logs de Flask

---

## 📞 Soporte

Para problemas técnicos, revisar:
1. Logs en consola
2. Logs en Elasticsearch/Kibana
3. Logs de Airflow
4. Estado de servicios (Kafka, MongoDB, MySQL)
