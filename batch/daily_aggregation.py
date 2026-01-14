
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pymongo import MongoClient
import mysql.connector
from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('daily_batch')


class DailyAggregation:
    
    
    def __init__(self):
        
        # MongoDB (fuente de datos en tiempo real)
        self.mongo_client = MongoClient(Config.MONGO_URI)
        self.mongo_db = self.mongo_client[Config.MONGO_DB_NAME]
        self.realtime_collection = self.mongo_db[Config.MONGO_COLLECTION_REALTIME]
        
        # MySQL (almacenamiento de agregados)
        self.mysql_conn = mysql.connector.connect(**Config.MYSQL_CONFIG)
        self.mysql_cursor = self.mysql_conn.cursor()
        
        logger.info("DailyAggregation iniciado")
    
    def get_yesterday_data(self, symbol):
        
        # Cambiar a hoy para pruebas (cambiar a -1 para producción)
        target_day = datetime.now() - timedelta(days=1)  # 0 = hoy, 1 = ayer
        start_of_day = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        query = {
            'symbol': symbol,
            'timestamp': {
                '$gte': start_of_day.isoformat(),
                '$lte': end_of_day.isoformat()
            }
        }
        
        data = list(self.realtime_collection.find(query))
        
        if not data:
            logger.warning(f"No hay datos para {symbol} del día {target_day.date()}")
            return None
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Obtenidos {len(df)} registros para {symbol}")
        return df
    
    def calculate_daily_metrics(self, df):
        
        metrics = {
            'avg_price': df['price'].mean(),
            'max_price': df['price'].max(),
            'min_price': df['price'].min(),
            'close_price': df.iloc[-1]['price'],
            'open_price': df.iloc[0]['price'],
            'total_volume': df['volume'].sum(),
            'avg_volume': df['volume'].mean(),
            'price_volatility': df['price'].std(),
            'num_trades': len(df)
        }
        
        # Calcular cambio porcentual del día
        metrics['daily_change_pct'] = (
            (metrics['close_price'] - metrics['open_price']) / metrics['open_price'] * 100
        )
        
        return metrics
    
    def calculate_technical_indicators(self, df, window=20):
        
        indicators = {}
        
        # SMA - Simple Moving Average
        if len(df) >= window:
            indicators['sma_20'] = df['price'].rolling(window=window).mean().iloc[-1]
        else:
            indicators['sma_20'] = None
        
        # RSI - Relative Strength Index
        if len(df) >= 14:
            delta = df['price'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = (100 - (100 / (1 + rs))).iloc[-1]
        else:
            indicators['rsi'] = None
        
        return indicators
    
    def save_to_mysql(self, symbol, date, metrics, indicators):
        
        try:
            query = """
            INSERT INTO daily_aggregates 
            (symbol, date, open_price, close_price, high_price, low_price, 
             avg_price, total_volume, avg_volume, price_volatility, 
             daily_change_pct, sma_20, rsi, num_trades)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            close_price = VALUES(close_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            avg_price = VALUES(avg_price),
            total_volume = VALUES(total_volume),
            avg_volume = VALUES(avg_volume),
            price_volatility = VALUES(price_volatility),
            daily_change_pct = VALUES(daily_change_pct),
            sma_20 = VALUES(sma_20),
            rsi = VALUES(rsi),
            num_trades = VALUES(num_trades)
            """
            
            # Convertir valores NaN a None para MySQL
            def to_float_or_none(val):
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return None
                return float(val)
            
            def to_int_or_none(val):
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return None
                return int(val)
            
            values = (
                symbol,
                date,
                to_float_or_none(metrics['open_price']),
                to_float_or_none(metrics['close_price']),
                to_float_or_none(metrics['max_price']),
                to_float_or_none(metrics['min_price']),
                to_float_or_none(metrics['avg_price']),
                to_int_or_none(metrics['total_volume']),
                to_int_or_none(metrics['avg_volume']),
                to_float_or_none(metrics['price_volatility']),
                to_float_or_none(metrics['daily_change_pct']),
                to_float_or_none(indicators.get('sma_20')),
                to_float_or_none(indicators.get('rsi')),
                to_int_or_none(metrics['num_trades'])
            )
            
            self.mysql_cursor.execute(query, values)
            self.mysql_conn.commit()
            
            logger.info(f"Datos guardados en MySQL para {symbol} - {date}")
            
        except Exception as e:
            logger.error(f"Error al guardar en MySQL: {e}")
            self.mysql_conn.rollback()
    
    def process_all_stocks(self):
        
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        logger.info(f"Procesando datos del {yesterday}")
        
        for symbol in Config.STOCKS_TO_MONITOR:
            try:
                logger.info(f"Procesando {symbol}...")
                
                # Obtener datos del día
                df = self.get_yesterday_data(symbol)
                
                if df is None or df.empty:
                    continue
                
                # Calcular métricas
                metrics = self.calculate_daily_metrics(df)
                
                # Calcular indicadores técnicos
                indicators = self.calculate_technical_indicators(df)
                
                # Guardar en MySQL
                self.save_to_mysql(symbol, yesterday, metrics, indicators)
                
                logger.info(
                    f"{symbol} completado - Precio: ${metrics['close_price']:.2f}, "
                    f"Cambio: {metrics['daily_change_pct']:+.2f}%"
                )
                
            except Exception as e:
                logger.error(f"Error procesando {symbol}: {e}")
                continue
        
        logger.info("Procesamiento batch completado")
    
    def cleanup_old_data(self, days_to_keep=90):
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        result = self.realtime_collection.delete_many({
            'timestamp': {'$lt': cutoff_date.isoformat()}
        })
        
        logger.info(f"Eliminados {result.deleted_count} registros antiguos de MongoDB")
    
    def close(self):
        
        self.mongo_client.close()
        self.mysql_cursor.close()
        self.mysql_conn.close()
        logger.info("Conexiones cerradas")


def main():
    aggregator = DailyAggregation()
    
    try:
        # Procesar datos del día anterior
        aggregator.process_all_stocks()
        
        # Limpiar datos antiguos
        aggregator.cleanup_old_data(days_to_keep=90)
        
    except Exception as e:
        logger.error(f"Error en procesamiento batch: {e}")
    finally:
        aggregator.close()


if __name__ == "__main__":
    main()
