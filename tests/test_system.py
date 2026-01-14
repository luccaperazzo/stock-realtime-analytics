"""
Tests unitarios para el sistema de análisis de acciones
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config


class TestStockProducer:
    """Tests para el Kafka Producer"""
    
    @patch('streaming.producer.yf.Ticker')
    @patch('streaming.producer.KafkaProducer')
    def test_fetch_stock_data(self, mock_kafka, mock_ticker):
        """Test obtención de datos de acciones"""
        from streaming.producer import StockProducer
        
        # Mock de respuesta de yfinance
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'marketCap': 3000000000000,
            'trailingPE': 28.5
        }
        
        # Mock de history
        import pandas as pd
        mock_history = pd.DataFrame({
            'Open': [150.0],
            'High': [152.0],
            'Low': [149.0],
            'Close': [151.5],
            'Volume': [50000000]
        })
        mock_ticker_instance.history.return_value = mock_history
        mock_ticker.return_value = mock_ticker_instance
        
        producer = StockProducer()
        data = producer.fetch_stock_data('AAPL')
        
        assert data is not None
        assert data['symbol'] == 'AAPL'
        assert data['price'] == 151.5
        assert data['volume'] == 50000000
    
    @patch('streaming.producer.KafkaProducer')
    def test_send_to_kafka(self, mock_kafka):
        """Test envío de datos a Kafka"""
        from streaming.producer import StockProducer
        
        mock_producer_instance = Mock()
        mock_future = Mock()
        mock_metadata = Mock()
        mock_metadata.topic = 'stock-prices'
        mock_metadata.partition = 0
        mock_metadata.offset = 123
        mock_future.get.return_value = mock_metadata
        mock_producer_instance.send.return_value = mock_future
        mock_kafka.return_value = mock_producer_instance
        
        producer = StockProducer()
        
        test_data = {
            'symbol': 'AAPL',
            'price': 150.0,
            'volume': 1000000
        }
        
        producer.send_to_kafka('AAPL', test_data)
        
        mock_producer_instance.send.assert_called_once()


class TestAlertService:
    """Tests para el sistema de alertas"""
    
    @patch('streaming.alerts.MongoClient')
    def test_get_users_for_stock(self, mock_mongo):
        """Test obtención de usuarios suscritos"""
        from streaming.alerts import AlertService
        
        mock_collection = Mock()
        mock_collection.find.return_value = [
            {'email': 'user1@example.com', 'subscribed_stocks': ['AAPL']},
            {'email': 'user2@example.com', 'subscribed_stocks': ['AAPL', 'GOOGL']}
        ]
        
        mock_db = Mock()
        mock_db.__getitem__.return_value = mock_collection
        
        mock_client = Mock()
        mock_client.__getitem__.return_value = mock_db
        mock_mongo.return_value = mock_client
        
        alert_service = AlertService()
        users = alert_service.get_users_for_stock('AAPL')
        
        assert len(users) == 2
    
    def test_create_alert_email(self):
        """Test creación de email de alerta"""
        from streaming.alerts import AlertService
        
        with patch('streaming.alerts.MongoClient'):
            alert_service = AlertService()
            
            data = {
                'price': 155.0,
                'price_change_pct': 6.5,
                'open': 145.0,
                'high': 156.0,
                'low': 144.0,
                'volume': 60000000,
                'timestamp': '2026-01-13T10:30:00'
            }
            
            html = alert_service.create_alert_email('AAPL', data)
            
            assert 'AAPL' in html
            assert '155.00' in html
            assert '6.5' in html or '+6.5' in html


class TestDailyAggregation:
    """Tests para el procesamiento batch"""
    
    def test_calculate_daily_metrics(self):
        """Test cálculo de métricas diarias"""
        from batch.daily_aggregation import DailyAggregation
        import pandas as pd
        
        with patch('batch.daily_aggregation.MongoClient'), \
             patch('batch.daily_aggregation.mysql.connector.connect'):
            
            aggregator = DailyAggregation()
            
            # Crear DataFrame de prueba
            df = pd.DataFrame({
                'price': [150.0, 151.0, 152.0, 151.5, 153.0],
                'volume': [1000000, 1100000, 1050000, 1200000, 1150000]
            })
            
            metrics = aggregator.calculate_daily_metrics(df)
            
            assert 'avg_price' in metrics
            assert 'max_price' in metrics
            assert 'min_price' in metrics
            assert metrics['max_price'] == 153.0
            assert metrics['min_price'] == 150.0
            assert metrics['total_volume'] == sum(df['volume'])


class TestNewsScraper:
    """Tests para el scraper de noticias"""
    
    def test_filter_relevant_articles(self):
        """Test filtrado de artículos relevantes"""
        from articles.news_scraper import NewsScraperService
        
        with patch('articles.news_scraper.MongoClient'):
            scraper = NewsScraperService()
            
            articles = [
                {'title': 'Apple announces new product launch', 'symbol': 'AAPL'},
                {'title': 'Stock market update', 'symbol': 'AAPL'},
                {'title': 'Apple CEO discusses revenue growth', 'symbol': 'AAPL'},
            ]
            
            keywords = ['product', 'revenue', 'CEO']
            filtered = scraper.filter_relevant_articles(articles, keywords)
            
            assert len(filtered) > 0
            assert all('relevance_score' in article for article in filtered)


class TestFlaskApp:
    """Tests para la aplicación Flask"""
    
    @pytest.fixture
    def client(self):
        """Crear cliente de prueba de Flask"""
        from flask_web_app.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @patch('flask_web_app.app.mongo_db')
    def test_index_route(self, mock_db, client):
        """Test ruta principal"""
        mock_collection = Mock()
        mock_collection.find_one.return_value = {
            'symbol': 'AAPL',
            'price': 150.0,
            'price_change_pct': 2.5,
            'volume': 50000000,
            'timestamp': '2026-01-13T10:00:00'
        }
        
        mock_db.__getitem__.return_value = mock_collection
        
        response = client.get('/')
        assert response.status_code == 200
    
    @patch('flask_web_app.app.mongo_db')
    def test_api_stock_endpoint(self, mock_db, client):
        """Test endpoint de API"""
        mock_collection = Mock()
        mock_collection.find.return_value.sort.return_value.limit.return_value = [
            {'symbol': 'AAPL', 'price': 150.0, 'timestamp': '2026-01-13'}
        ]
        
        mock_db.__getitem__.return_value = mock_collection
        
        response = client.get('/api/stock/AAPL')
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
