"""
Flask Web Application - Interfaz de usuario para el sistema
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
from pymongo import MongoClient
import mysql.connector
from datetime import datetime, timedelta
import sys
import os

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('flask_app')

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
CORS(app)

# Conexiones a bases de datos
mongo_client = MongoClient(Config.MONGO_URI)
mongo_db = mongo_client[Config.MONGO_DB_NAME]


def get_mysql_connection():
    """Crea conexión a MySQL"""
    return mysql.connector.connect(**Config.MYSQL_CONFIG)


@app.route('/')
def index():
    """Página principal con precios en tiempo real"""
    try:
        # Obtener últimos precios de MongoDB
        realtime_collection = mongo_db[Config.MONGO_COLLECTION_REALTIME]
        
        stocks_data = []
        for symbol in Config.STOCKS_TO_MONITOR:
            # Obtener el precio más reciente
            latest = realtime_collection.find_one(
                {'symbol': symbol},
                sort=[('timestamp', -1)]
            )
            
            if latest:
                stocks_data.append({
                    'symbol': symbol,
                    'price': latest['price'],
                    'change_pct': latest.get('price_change_pct', 0),
                    'volume': latest['volume'],
                    'timestamp': latest['timestamp']
                })
        
        return render_template('index.html', stocks=stocks_data)
        
    except Exception as e:
        logger.error(f"Error en página principal: {e}")
        return render_template('error.html', error=str(e))


@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """API endpoint para obtener datos de una acción"""
    try:
        realtime_collection = mongo_db[Config.MONGO_COLLECTION_REALTIME]
        
        # Últimos 100 registros
        data = list(realtime_collection.find(
            {'symbol': symbol},
            {'_id': 0}
        ).sort('timestamp', -1).limit(100))
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/historical/<symbol>')
def get_historical_data(symbol):
    """Obtiene datos históricos de MySQL"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Últimos 30 días
        query = """
        SELECT * FROM daily_aggregates
        WHERE symbol = %s
        ORDER BY date DESC
        LIMIT 30
        """
        
        cursor.execute(query, (symbol,))
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convertir dates a string
        for row in data:
            if 'date' in row:
                row['date'] = row['date'].strftime('%Y-%m-%d')
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        logger.error(f"Error obteniendo histórico de {symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios"""
    if request.method == 'POST':
        try:
            data = request.form
            
            users_collection = mongo_db[Config.MONGO_COLLECTION_USERS]
            
            # Verificar si ya existe
            if users_collection.find_one({'email': data['email']}):
                flash('El email ya está registrado', 'error')
                return redirect(url_for('register'))
            
            # Crear usuario
            user = {
                'name': data['name'],
                'email': data['email'],
                'subscribed_stocks': request.form.getlist('stocks'),
                'alert_threshold': float(data.get('threshold', Config.PRICE_CHANGE_THRESHOLD)),
                'alerts_enabled': True,
                'news_summary_enabled': 'news_summary' in data,
                'created_at': datetime.now()
            }
            
            users_collection.insert_one(user)
            
            flash('Registro exitoso! Ya puedes recibir alertas.', 'success')
            logger.info(f"Nuevo usuario registrado: {user['email']}")
            
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Error en registro: {e}")
            flash(f'Error en el registro: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html', stocks=Config.STOCKS_TO_MONITOR)


@app.route('/dashboard/<symbol>')
def dashboard(symbol):
    """Dashboard detallado de una acción"""
    try:
        # Obtener datos en tiempo real
        realtime_collection = mongo_db[Config.MONGO_COLLECTION_REALTIME]
        latest = realtime_collection.find_one(
            {'symbol': symbol},
            sort=[('timestamp', -1)]
        )
        
        # Obtener noticias recientes
        articles_collection = mongo_db[Config.MONGO_COLLECTION_ARTICLES]
        news = list(articles_collection.find(
            {'symbol': symbol}
        ).sort('scraped_at', -1).limit(10))
        
        return render_template('dashboard.html', 
                             symbol=symbol, 
                             latest=latest, 
                             news=news)
        
    except Exception as e:
        logger.error(f"Error en dashboard de {symbol}: {e}")
        return render_template('error.html', error=str(e))


@app.route('/api/realtime/<symbol>')
def realtime_price(symbol):
    """Endpoint para actualización en tiempo real (AJAX/WebSocket)"""
    try:
        realtime_collection = mongo_db[Config.MONGO_COLLECTION_REALTIME]
        latest = realtime_collection.find_one(
            {'symbol': symbol},
            {'_id': 0},
            sort=[('timestamp', -1)]
        )
        
        return jsonify({'success': True, 'data': latest})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/news')
def get_all_news():
    """Obtiene todas las noticias recientes"""
    try:
        articles_collection = mongo_db[Config.MONGO_COLLECTION_ARTICLES]
        
        # Últimas 24 horas
        yesterday = datetime.now() - timedelta(days=1)
        
        news = list(articles_collection.find(
            {'scraped_at': {'$gte': yesterday}},
            {'_id': 0}
        ).sort('scraped_at', -1).limit(50))
        
        return jsonify({'success': True, 'data': news})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.errorhandler(404)
def not_found(error):
    """Página de error 404"""
    return render_template('error.html', error='Página no encontrada'), 404


@app.errorhandler(500)
def internal_error(error):
    """Página de error 500"""
    logger.error(f"Error 500: {error}")
    return render_template('error.html', error='Error interno del servidor'), 500


if __name__ == '__main__':
    logger.info(f"Iniciando Flask app en puerto {Config.FLASK_PORT}")
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_ENV == 'development'
    )
