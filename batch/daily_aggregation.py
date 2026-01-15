
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
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
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

        # Usar cierres diarios históricos para indicadores
        try:
            symbol = df['symbol'].iloc[0] if 'symbol' in df.columns and not df.empty else None
        except Exception:
            symbol = None

        # Fecha límite (día del dataframe)
        try:
            last_date = pd.to_datetime(df['timestamp'].iloc[-1]).date()
        except Exception:
            last_date = None

        # SMA 20 días: requerimos exactamente 20 cierres; si faltan, dejamos None
        if symbol and last_date:
            closes_20 = self.get_last_n_daily_closes(symbol, 20, last_date)
            if len(closes_20) == 20:
                indicators['sma_20'] = float(np.mean(closes_20))
            else:
                indicators['sma_20'] = None
        else:
            indicators['sma_20'] = None

        # RSI de 14 días: calcular sobre los 14 cierres diarios; dejar None si hay menos
        if symbol and last_date:
            closes_14 = self.get_last_n_daily_closes(symbol, 14, last_date)
            if len(closes_14) == 14:
                closes_series = pd.Series(closes_14).astype(float)
                delta = closes_series.diff()
                gain = delta.where(delta > 0, 0).mean()
                loss = -delta.where(delta < 0, 0).mean()
                if loss == 0:
                    indicators['rsi'] = 100.0 if gain > 0 else 50.0
                else:
                    rs = gain / loss
                    indicators['rsi'] = float(100 - (100 / (1 + rs)))
            else:
                indicators['rsi'] = None
        else:
            indicators['rsi'] = None

        return indicators

    def get_last_n_daily_closes(self, symbol, n, upto_date):
        """Return last `n` daily close prices for `symbol` up to `upto_date` (inclusive).

        Returns a list ordered from oldest to newest. If fewer than `n` days
        are available, returns the available closes (length < n).
        """
        try:
            end_of_day = datetime(upto_date.year, upto_date.month, upto_date.day, 23, 59, 59, 999999)

            pipeline = [
                { '$match': { 'symbol': symbol } },
                { '$addFields': { 'ts': { '$dateFromString': { 'dateString': '$timestamp' } } } },
                { '$match': { 'ts': { '$lte': end_of_day } } },
                { '$sort': { 'ts': 1 } },
                { '$group': {
                    '_id': { '$dateToString': { 'format': '%Y-%m-%d', 'date': '$ts' } },
                    'close_price': { '$last': '$price' },
                    'ts': { '$last': '$ts' }
                } },
                { '$sort': { '_id': -1 } },
                { '$limit': n }
            ]

            result = list(self.realtime_collection.aggregate(pipeline))
            # result is sorted by date desc; reverse to get oldest->newest
            result = list(reversed(result))
            closes = [r.get('close_price') for r in result if r.get('close_price') is not None]
            return closes
        except Exception as e:
            logger.error(f"Error obteniendo cierres diarios para {symbol}: {e}")
            return []
    
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

        # Borra toda la tabla daily_aggregates al inicio de la corrida
        try:
            delete_query = "DELETE FROM daily_aggregates"
            self.mysql_cursor.execute(delete_query)
            deleted = self.mysql_cursor.rowcount
            self.mysql_conn.commit()
            logger.info(f"Eliminados {deleted} registros existentes en MySQL (tabla daily_aggregates)")
        except Exception as e:
            logger.error(f"Error al borrar registros de daily_aggregates: {e}")
            self.mysql_conn.rollback()

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
