
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_STOCKS = os.getenv('KAFKA_TOPIC_STOCKS', 'stock-prices')
    KAFKA_CONSUMER_GROUP = 'stock-consumer-group'
    
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'stock_market')
    MONGO_COLLECTION_REALTIME = 'realtime_prices'
    MONGO_COLLECTION_ARTICLES = 'news_articles'
    MONGO_COLLECTION_USERS = 'users'
    MONGO_COLLECTION_ALERTS = 'alert_history'
    
    # MySQL
    MYSQL_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'stock_analytics'),
        'auth_plugin': 'mysql_native_password'
    }
    
    # Elasticsearch
    ELASTICSEARCH_CONFIG = {
        'host': os.getenv('ELASTICSEARCH_HOST', 'localhost'),
        'port': int(os.getenv('ELASTICSEARCH_PORT', 9200))
    }
    ES_INDEX_LOGS = 'stock-system-logs'
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'stock-data-archive')
    
    # Email
    SMTP_CONFIG = {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'sender': os.getenv('EMAIL_SENDER', ''),
        'password': os.getenv('EMAIL_PASSWORD', '')
    }
    
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    # Alert Thresholds
    PRICE_CHANGE_THRESHOLD = float(os.getenv('PRICE_CHANGE_THRESHOLD', 0.5))
    VOLUME_THRESHOLD_MULTIPLIER = float(os.getenv('VOLUME_THRESHOLD_MULTIPLIER', 2.0))
    
    # Stocks to monitor
    STOCKS_TO_MONITOR = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA']
    
    # Batch Processing
    BATCH_SCHEDULE_TIME = os.getenv('BATCH_SCHEDULE_TIME', '00:00')
    
    # Flask
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Spark
    SPARK_APP_NAME = 'StockStreamingApp'
    SPARK_MASTER = 'local[*]'
    
    # Timing
    PRODUCER_FETCH_INTERVAL = 10  # segundos
    SPARK_BATCH_DURATION = 30  # segundos
    NEWS_SCRAPER_SCHEDULE = '09:00'  # hora del día


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Override con configuraciones más seguras
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    MONGO_URI = os.getenv('MONGO_URI')


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    MONGO_DB_NAME = 'stock_market_test'
    MYSQL_CONFIG = Config.MYSQL_CONFIG.copy()
    MYSQL_CONFIG['database'] = 'stock_analytics_test'


# Seleccionar configuración según entorno
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
