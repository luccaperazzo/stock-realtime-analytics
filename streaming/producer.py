"""
Kafka Producer - Captura datos de acciones en tiempo real
"""
import json
import time
import sys
import os
import random
import requests
from datetime import datetime
from kafka import KafkaProducer

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('kafka_producer')


class StockProducer:
    """Producer de Kafka para datos de acciones"""
    
    def __init__(self):
        """Inicializa el producer de Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info(f"Kafka producer iniciado: {Config.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Error al inicializar Kafka producer: {e}")
            raise
    
    def fetch_stock_data(self, symbol):
        """
        Obtiene datos en tiempo real de una acción usando Alpha Vantage
        
        Args:
            symbol: Símbolo de la acción (ej: 'AAPL')
        
        Returns:
            Dict con datos de la acción
        """
        try:
            # Obtener quote de Alpha Vantage
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': Config.ALPHA_VANTAGE_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data_json = response.json()
            
            # Verificar si hay datos válidos
            if 'Global Quote' not in data_json or not data_json['Global Quote']:
                logger.error(f"No hay datos de Alpha Vantage para {symbol}")
                return None
            
            quote = data_json['Global Quote']
            
            # Parsear datos de Alpha Vantage
            data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'price': float(quote.get('05. price', 0)),
                'volume': int(quote.get('06. volume', 0)),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'market_cap': 0,  # Alpha Vantage no provee esto en GLOBAL_QUOTE
                'pe_ratio': 0
            }
            
            logger.info(f"Datos de Alpha Vantage para {symbol}: ${data['price']:.2f}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red con Alpha Vantage para {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error al obtener datos de {symbol}: {e}")
            return None
    
    def send_to_kafka(self, symbol, data):
        """
        Envía datos a Kafka topic
        
        Args:
            symbol: Símbolo de la acción
            data: Datos a enviar
        """
        try:
            future = self.producer.send(
                Config.KAFKA_TOPIC_STOCKS,
                key=symbol,
                value=data
            )
            
            # Esperar confirmación
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Mensaje enviado a Kafka - Topic: {record_metadata.topic}, "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )
            
        except Exception as e:
            logger.error(f"Error al enviar datos a Kafka: {e}")
    
    def run(self):
        """Ejecuta el producer en loop continuo"""
        logger.info(f"Iniciando monitoreo de {len(Config.STOCKS_TO_MONITOR)} acciones")
        logger.info(f"Acciones: {', '.join(Config.STOCKS_TO_MONITOR)}")
        
        try:
            while True:
                for symbol in Config.STOCKS_TO_MONITOR:
                    data = self.fetch_stock_data(symbol)
                    
                    if data:
                        self.send_to_kafka(symbol, data)
                    
                    # Delay entre símbolos para respetar rate limit de Alpha Vantage
                    # API gratuita permite 5 llamadas/minuto = 12 segundos entre llamadas
                    time.sleep(15)
                
                logger.info(f"Ciclo completado. Esperando {Config.PRODUCER_FETCH_INTERVAL} segundos...")
                time.sleep(Config.PRODUCER_FETCH_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Producer detenido por el usuario")
        except Exception as e:
            logger.error(f"Error en el producer: {e}")
        finally:
            self.close()
    
    def close(self):
        """Cierra el producer correctamente"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer cerrado")


def main():
    """Función principal"""
    producer = StockProducer()
    producer.run()


if __name__ == "__main__":
    main()
