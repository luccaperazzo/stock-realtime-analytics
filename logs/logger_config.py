"""
Sistema de logging centralizado con Elasticsearch
"""
import logging
import sys
from datetime import datetime
from elasticsearch import Elasticsearch
try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None
from config.config import Config

class ElasticsearchHandler(logging.Handler):
    """Handler para enviar logs a Elasticsearch"""
    
    def __init__(self, es_host, es_port, index_name):
        super().__init__()
        self.es = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
        self.index_name = index_name
    
    def emit(self, record):
        """Envía el log a Elasticsearch"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            # Agregar información de excepción si existe
            if record.exc_info:
                log_entry['exception'] = self.formatter.formatException(record.exc_info)
            
            # Agregar campos extras
            if hasattr(record, 'extra_fields'):
                log_entry.update(record.extra_fields)
            
            self.es.index(index=self.index_name, document=log_entry)
        except Exception as e:
            print(f"Error al enviar log a Elasticsearch: {e}")


def setup_logger(name, log_level=None):
    """
    Configura un logger con handlers para consola y Elasticsearch
    
    Args:
        name: Nombre del logger
        log_level: Nivel de logging (default: INFO)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    if log_level:
        logger.setLevel(getattr(logging, log_level))
    else:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Evitar duplicación de logs
    if logger.handlers:
        return logger
    
    # Formato para consola
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para Elasticsearch
    try:
        es_handler = ElasticsearchHandler(
            Config.ELASTICSEARCH_CONFIG['host'],
            Config.ELASTICSEARCH_CONFIG['port'],
            Config.ES_INDEX_LOGS
        )
        
        if jsonlogger:
            json_formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
            es_handler.setFormatter(json_formatter)
        logger.addHandler(es_handler)
    except Exception as e:
        logger.warning(f"No se pudo conectar a Elasticsearch: {e}")
    
    return logger


def log_with_context(logger, level, message, **context):
    """
    Log con contexto adicional
    
    Args:
        logger: Logger instance
        level: Nivel de log (INFO, WARNING, ERROR, etc.)
        message: Mensaje del log
        **context: Campos adicionales
    """
    extra = {'extra_fields': context}
    getattr(logger, level.lower())(message, extra=extra)


# Logger principal del sistema
system_logger = setup_logger('stock_system')
