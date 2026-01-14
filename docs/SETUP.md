# 🚀 Guía de Instalación y Configuración

## Requisitos Previos

### Software Necesario
- Python 3.9+
- Apache Kafka 3.0+
- Apache Spark 3.5+
- MongoDB 6.0+
- MySQL 8.0+
- Elasticsearch 8.0+
- Apache Airflow 2.8+
- Node.js (para Kibana/Grafana)

### Servicios Cloud (Opcional)
- AWS S3 (para archivo de datos)
- MongoDB Atlas (alternativa a MongoDB local)
- AWS RDS MySQL (alternativa a MySQL local)

---

## 📦 Instalación Paso a Paso

### 1. Clonar/Descargar el Proyecto

```bash
cd c:\Users\lucca\OneDrive\Desktop\data_project
```

### 2. Crear Entorno Virtual

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar Dependencias de Python

```powershell
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

```powershell
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus credenciales
notepad .env
```

**Variables importantes a configurar:**
- `KAFKA_BOOTSTRAP_SERVERS`
- `MONGO_URI`
- `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `EMAIL_SENDER`, `EMAIL_PASSWORD`
- `ALPHA_VANTAGE_API_KEY`

---

## 🔧 Configuración de Servicios

### Apache Kafka

#### Windows:
```powershell
# Descargar Kafka desde https://kafka.apache.org/downloads

# Iniciar Zookeeper
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Iniciar Kafka (en otra terminal)
.\bin\windows\kafka-server-start.bat .\config\server.properties

# Crear topic
.\bin\windows\kafka-topics.bat --create --topic stock-prices --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### MongoDB

#### Instalación Local:
```powershell
# Descargar desde https://www.mongodb.com/try/download/community
# Instalar y ejecutar

# Iniciar MongoDB
mongod --dbpath "C:\data\db"

# Configurar base de datos
python database/setup_mongodb.py
```

#### MongoDB Atlas (Cloud):
1. Crear cuenta en https://www.mongodb.com/cloud/atlas
2. Crear cluster gratuito
3. Obtener connection string
4. Actualizar `MONGO_URI` en `.env`

### MySQL

```powershell
# Instalar MySQL desde https://dev.mysql.com/downloads/mysql/

# Ejecutar servidor MySQL
# Crear base de datos y tablas
mysql -u root -p < database/mysql_schema.sql
```

### Elasticsearch

```powershell
# Descargar desde https://www.elastic.co/downloads/elasticsearch

# Iniciar Elasticsearch
.\bin\elasticsearch.bat

# Verificar
curl http://localhost:9200
```

### Kibana (Visualización de Logs)

```powershell
# Descargar desde https://www.elastic.co/downloads/kibana

# Configurar elasticsearch.hosts en config/kibana.yml
# Iniciar Kibana
.\bin\kibana.bat

# Acceder a http://localhost:5601
```

### Grafana (Dashboards)

```powershell
# Descargar desde https://grafana.com/grafana/download

# Iniciar Grafana
.\bin\grafana-server.exe

# Acceder a http://localhost:3000
# User/Pass default: admin/admin

# Configurar datasource MySQL
# Importar dashboards desde grafana/dashboards/
```

---

## ⚙️ Configuración de Apache Spark

### Instalación:

```powershell
# Descargar Spark desde https://spark.apache.org/downloads.html
# Extraer en C:\spark

# Configurar variables de entorno
$env:SPARK_HOME = "C:\spark"
$env:PATH += ";C:\spark\bin"

# Descargar Hadoop WinUtils para Windows
# https://github.com/cdarlint/winutils
# Copiar en C:\hadoop\bin

$env:HADOOP_HOME = "C:\hadoop"
```

---

## 🚀 Configuración de Apache Airflow

```powershell
# Inicializar base de datos de Airflow
airflow db init

# Crear usuario admin
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com

# Copiar configuración
copy airflow\airflow.cfg $env:AIRFLOW_HOME\airflow.cfg

# Iniciar webserver
airflow webserver --port 8080

# En otra terminal, iniciar scheduler
airflow scheduler
```

---

## 🔑 Configuración de APIs

### Yahoo Finance
- No requiere API key
- Límite de rate: ~2000 requests/hora

### Alpha Vantage
1. Registrarse en https://www.alphavantage.co/support/#api-key
2. Obtener API key gratuita
3. Agregar a `.env`: `ALPHA_VANTAGE_API_KEY=tu_key`

### AWS S3
```powershell
# Instalar AWS CLI
# https://aws.amazon.com/cli/

# Configurar credenciales
aws configure

# Crear bucket
aws s3 mb s3://stock-data-archive
```

---

## 📧 Configuración de Email

### Gmail:
1. Habilitar verificación en 2 pasos
2. Crear App Password: https://myaccount.google.com/apppasswords
3. Configurar en `.env`:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_SENDER=tu_email@gmail.com
   EMAIL_PASSWORD=tu_app_password
   ```

---

## ✅ Verificación de Instalación

```powershell
# Verificar Python y dependencias
python --version
pip list

# Verificar Kafka
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092

# Verificar MongoDB
python -c "from pymongo import MongoClient; print(MongoClient().server_info())"

# Verificar MySQL
mysql --version

# Verificar Elasticsearch
curl http://localhost:9200

# Verificar Spark
spark-submit --version
```

---

## 🏃 Ejecutar el Sistema

### 1. Iniciar Servicios Base
```powershell
# Terminal 1: Zookeeper
.\kafka\bin\windows\zookeeper-server-start.bat .\kafka\config\zookeeper.properties

# Terminal 2: Kafka
.\kafka\bin\windows\kafka-server-start.bat .\kafka\config\server.properties

# Terminal 3: MongoDB (si local)
mongod

# Terminal 4: MySQL (si local)
# Ya iniciado como servicio

# Terminal 5: Elasticsearch
.\elasticsearch\bin\elasticsearch.bat
```

### 2. Iniciar Aplicaciones del Proyecto
```powershell
# Terminal 6: Kafka Producer
python streaming/producer.py

# Terminal 7: Spark Consumer
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 streaming/consumer.py

# Terminal 8: Alert Service
python streaming/alerts.py

# Terminal 9: Flask Web App
python flask_web_app/app.py

# Terminal 10: Airflow Webserver
airflow webserver

# Terminal 11: Airflow Scheduler
airflow scheduler
```

---

## 🔍 Acceso a Interfaces

- **Flask App**: http://localhost:5000
- **Airflow**: http://localhost:8080
- **Kibana**: http://localhost:5601
- **Grafana**: http://localhost:3000
- **Elasticsearch**: http://localhost:9200

---

## 🐛 Troubleshooting

### Kafka no inicia
- Verificar que Zookeeper esté corriendo primero
- Verificar puerto 9092 no esté en uso

### MongoDB connection error
- Verificar que MongoDB esté corriendo
- Verificar MONGO_URI en .env

### Spark submit error
- Verificar SPARK_HOME y HADOOP_HOME
- Verificar Java JDK instalado

### Email no se envía
- Verificar App Password de Gmail
- Verificar configuración SMTP

---

## 📚 Siguiente Paso

Ver [USAGE.md](USAGE.md) para instrucciones de uso del sistema.
