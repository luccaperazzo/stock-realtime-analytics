# 🐳 Guía de Docker - Stock Analysis System

## 🚀 Inicio Rápido

### Iniciar todo el sistema
```powershell
docker-compose up -d
```

### Ver logs en tiempo real
```powershell
docker-compose logs -f
```

### Detener todo el sistema
```powershell
docker-compose down
```

### Detener y eliminar todo (incluyendo datos)
```powershell
docker-compose down -v
```

---

## 📋 Comandos Útiles

### Ver estado de los servicios
```powershell
docker-compose ps
```

### Ver logs de un servicio específico
```powershell
docker-compose logs -f producer
docker-compose logs -f consumer
docker-compose logs -f flask
```

### Reiniciar un servicio
```powershell
docker-compose restart producer
docker-compose restart consumer
```

### Reconstruir servicios (después de cambios en código)
```powershell
docker-compose up -d --build
```

### Reconstruir un servicio específico
```powershell
docker-compose up -d --build producer
```

### Ejecutar comandos dentro de un container
```powershell
docker-compose exec mongodb mongosh
docker-compose exec mysql mysql -uroot -ppascualina stock_analytics
```

### Ver recursos utilizados
```powershell
docker stats
```

---

## 🔍 Verificación del Sistema

### 1. Verificar que todos los servicios estén corriendo
```powershell
docker-compose ps
```

Deberías ver todos los servicios con estado "Up" o "running".

### 2. Verificar logs de cada componente
```powershell
# Producer
docker-compose logs producer | Select-Object -Last 20

# Consumer
docker-compose logs consumer | Select-Object -Last 20

# Flask
docker-compose logs flask | Select-Object -Last 20
```

### 3. Verificar conectividad

**Kafka:**
```powershell
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

**MongoDB:**
```powershell
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

**MySQL:**
```powershell
docker-compose exec mysql mysql -uroot -ppascualina -e "SHOW DATABASES;"
```

**Elasticsearch:**
```powershell
curl http://localhost:9200
```

---

## 🌐 Accesos Web

- **Flask App**: http://localhost:5000
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

---

## 🗂️ Gestión de Datos

### Ver datos en MongoDB
```powershell
docker-compose exec mongodb mongosh stock_market --eval "db.realtime_prices.countDocuments()"
docker-compose exec mongodb mongosh stock_market --eval "db.realtime_prices.find().limit(5)"
```

### Ver datos en MySQL
```powershell
docker-compose exec mysql mysql -uroot -ppascualina stock_analytics -e "SELECT * FROM daily_aggregates LIMIT 5;"
```

### Backup de datos

**MongoDB:**
```powershell
docker-compose exec mongodb mongodump --out=/data/backup
docker cp mongodb:/data/backup ./mongodb_backup
```

**MySQL:**
```powershell
docker-compose exec mysql mysqldump -uroot -ppascualina stock_analytics > backup.sql
```

---

## 🔧 Troubleshooting

### Problema: Servicios no inician
```powershell
# Ver logs detallados
docker-compose logs

# Verificar configuración
docker-compose config
```

### Problema: Puerto ya en uso
```powershell
# Ver qué está usando el puerto
netstat -ano | findstr :9092

# Detener servicios locales si es necesario
```

### Problema: Cambios de código no se reflejan
```powershell
# Reconstruir la imagen
docker-compose up -d --build nombre_servicio
```

### Problema: Sin espacio en disco
```powershell
# Limpiar imágenes no utilizadas
docker system prune -a

# Limpiar volúmenes no utilizados
docker volume prune
```

### Problema: Consumer/Producer no se conecta a Kafka
```powershell
# Verificar que Kafka esté saludable
docker-compose ps kafka

# Reiniciar Kafka
docker-compose restart kafka

# Esperar 30 segundos y reiniciar consumer/producer
docker-compose restart consumer producer
```

---

## 🏗️ Arquitectura Docker

```
┌─────────────────────────────────────────────────┐
│         Docker Network: stock-network           │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐  ┌────────┐  ┌─────────┐        │
│  │Zookeeper │→ │ Kafka  │← │Producer │        │
│  └──────────┘  └────┬───┘  └─────────┘        │
│                     │                           │
│                     ↓                           │
│            ┌────────┴────────┐                 │
│            │                 │                  │
│       ┌────▼────┐      ┌────▼────┐            │
│       │Consumer │      │ Alerts  │            │
│       └────┬────┘      └────┬────┘            │
│            │                 │                  │
│            ↓                 ↓                  │
│       ┌────────┐       ┌────────┐             │
│       │MongoDB │       │ MySQL  │             │
│       └────┬───┘       └────┬───┘             │
│            │                 │                  │
│            └────────┬────────┘                 │
│                     ↓                           │
│               ┌─────────┐                      │
│               │  Flask  │→ :5000              │
│               └─────────┘                      │
│                                                 │
│  ┌──────────────┐  ┌────────┐                 │
│  │Elasticsearch │← │ Logs   │                 │
│  └──────┬───────┘  └────────┘                 │
│         ↓                                       │
│    ┌────────┐                                  │
│    │ Kibana │→ :5601                          │
│    └────────┘                                  │
└─────────────────────────────────────────────────┘
```

---

## 📊 Volúmenes Persistentes

Los siguientes datos se mantienen incluso si detienes los containers:

- `mongodb_data`: Datos de MongoDB
- `mysql_data`: Datos de MySQL
- `elasticsearch_data`: Índices de Elasticsearch

Para eliminar datos:
```powershell
docker-compose down -v
```

---

## 🔄 Workflow de Desarrollo

### 1. Hacer cambios en el código
Edita los archivos Python normalmente.

### 2. Reconstruir el servicio afectado
```powershell
# Por ejemplo, si cambiaste producer.py:
docker-compose up -d --build producer
```

### 3. Ver los logs
```powershell
docker-compose logs -f producer
```

### 4. Si hay errores, debugging
```powershell
# Entrar al container
docker-compose exec producer /bin/bash

# O ver logs detallados
docker-compose logs producer
```

---

## 📦 Gestión de Imágenes

### Ver imágenes locales
```powershell
docker images
```

### Eliminar imágenes no utilizadas
```powershell
docker image prune -a
```

### Ver tamaño de imágenes
```powershell
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

---

## ⚙️ Variables de Entorno

Las variables se toman del archivo `.env`:
- `ALPHA_VANTAGE_API_KEY`
- `SMTP_SERVER`, `EMAIL_SENDER`, `EMAIL_PASSWORD`
- `SECRET_KEY`

Asegúrate de tener el archivo `.env` configurado correctamente.

---

## 🚦 Healthchecks

Docker Compose verifica automáticamente que los servicios estén saludables:

- **Kafka**: Verifica que pueda listar topics
- **MongoDB**: Verifica con ping
- **MySQL**: Verifica con mysqladmin
- **Elasticsearch**: Verifica con curl

Los servicios dependientes no inician hasta que sus dependencias estén saludables.

---

## 💡 Tips

1. **Desarrollo rápido**: Usa `docker-compose up` (sin -d) para ver logs en tiempo real
2. **Producción**: Usa `docker-compose up -d` para correr en background
3. **Reinicio automático**: Los servicios se reinician automáticamente si fallan (restart: unless-stopped)
4. **Logs rotativos**: Docker maneja automáticamente el tamaño de logs

---

## 🎯 Comandos de Un Solo Paso

### Setup completo desde cero
```powershell
docker-compose up -d
```

### Ver todo funcionando
```powershell
docker-compose ps
docker-compose logs -f
```

### Detener todo
```powershell
docker-compose down
```

### Reset completo (eliminar todo)
```powershell
docker-compose down -v
docker system prune -a
```
