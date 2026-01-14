
import json
import sys
import os
from datetime import datetime
from kafka import KafkaConsumer
from pymongo import MongoClient

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('kafka_consumer')


class StockStreamConsumer:
    
    
    def __init__(self):
        
        try:
            # Inicializar Kafka Consumer
            self.consumer = KafkaConsumer(
                Config.KAFKA_TOPIC_STOCKS,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id=Config.KAFKA_CONSUMER_GROUP,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            logger.info(f"Kafka consumer iniciado: {Config.KAFKA_BOOTSTRAP_SERVERS}")
            
            # Inicializar MongoDB
            self.mongo_client = MongoClient(Config.MONGO_URI)
            self.db = self.mongo_client[Config.MONGO_DB_NAME]
            self.collection = self.db[Config.MONGO_COLLECTION_REALTIME]
            self.alerts_collection = self.db[Config.MONGO_COLLECTION_ALERTS]
            logger.info(f"MongoDB conectado: {Config.MONGO_URI}")
            
        except Exception as e:
            logger.error(f"Error al inicializar consumer: {e}")
            raise
    
    def process_message(self, message):
        try:
            data = message.value
            
            # Agregar timestamp de procesamiento
            data['processed_at'] = datetime.now().isoformat()
            
            # Calcular price_change_pct si hay datos
            if data.get('price') and data.get('open'):
                data['price_change_pct'] = ((data['price'] - data['open']) / data['open'] * 100)
            
            # Insertar en MongoDB
            result = self.collection.insert_one(data)
            
            logger.info(
                f"Dato guardado - Symbol: {data['symbol']}, "
                f"Price: ${data['price']:.2f}, "
                f"Change: {data.get('price_change_pct', 0):.2f}%"
            )
            
            # Verificar si se cumple condición de alerta
            alert_triggered = False
            alert_type = None
            alert_reason = ""
            
            # 1. Verificar cambio de precio
            price_change = abs(data.get('price_change_pct', 0))
            if price_change >= Config.PRICE_CHANGE_THRESHOLD:
                alert_triggered = True
                alert_type = 'price_change'
                alert_reason = f"Cambio de {data.get('price_change_pct', 0):.2f}% supera umbral de {Config.PRICE_CHANGE_THRESHOLD}%"
            
            # 2. Verificar volumen anormalmente alto
            current_volume = data.get('volume', 0)
            if current_volume > 0:
                # Calcular volumen promedio de los últimos 20 registros del mismo símbolo
                avg_volume_docs = list(self.collection.find(
                    {'symbol': data['symbol']},
                    {'volume': 1}
                ).sort('_id', -1).limit(20))
                
                if len(avg_volume_docs) >= 5:  # Al menos 5 registros históricos
                    avg_volume = sum(doc.get('volume', 0) for doc in avg_volume_docs) / len(avg_volume_docs)
                    volume_threshold = avg_volume * Config.VOLUME_THRESHOLD_MULTIPLIER
                    
                    if current_volume >= volume_threshold:
                        alert_triggered = True
                        alert_type = 'high_volume'
                        alert_reason = f"Volumen {current_volume:,} es {current_volume/avg_volume:.1f}x el promedio ({avg_volume:,.0f})"
            
            # Crear alerta si se cumplió alguna condición
            if alert_triggered:
                # Verificar si ya existe alerta con mismo símbolo y precio (redondeado a 2 decimales)
                # para evitar duplicados cuando los mercados están cerrados
                price_rounded = round(data['price'], 2)
                change_rounded = round(data.get('price_change_pct', 0), 2)
                volume_rounded = round(current_volume, -3)  # Redondear a miles
                
                existing_alert = self.alerts_collection.find_one({
                    'symbol': data['symbol'],
                    'price_rounded': price_rounded,
                    'alert_type': alert_type
                })
                
                if not existing_alert:
                    # Crear alerta en colección de alertas
                    alert_data = data.copy()
                    alert_data['alert_type'] = alert_type
                    alert_data['alert_reason'] = alert_reason
                    alert_data['threshold_met'] = Config.PRICE_CHANGE_THRESHOLD if alert_type == 'price_change' else Config.VOLUME_THRESHOLD_MULTIPLIER
                    alert_data['created_at'] = datetime.now().isoformat()
                    alert_data['price_rounded'] = price_rounded
                    alert_data['change_rounded'] = change_rounded
                    alert_data['volume_rounded'] = volume_rounded
                    
                    self.alerts_collection.insert_one(alert_data)
                    
                    logger.warning(
                        f"🔔 ALERTA - {data['symbol']}: {alert_reason}"
                        f"supera umbral de {Config.PRICE_CHANGE_THRESHOLD}%"
                    )
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {e}")
    
    def run(self):
        logger.info("Iniciando consumo de mensajes desde Kafka...")
        logger.info(f"Topic: {Config.KAFKA_TOPIC_STOCKS}")
        
        try:
            for message in self.consumer:
                self.process_message(message)
                
        except KeyboardInterrupt:
            logger.info("Consumer detenido por el usuario")
        except Exception as e:
            logger.error(f"Error en el consumer: {e}")
        finally:
            self.consumer.close()
            self.mongo_client.close()
            logger.info("Consumer cerrado")


def main():
    logger.info("=== Stock Market Consumer ===")
    consumer = StockStreamConsumer()
    consumer.run()


if __name__ == "__main__":
    main()
