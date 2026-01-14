"""
News Scraper - Recopila noticias relacionadas con las acciones monitoreadas
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from pymongo import MongoClient
from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('news_scraper')


class NewsScraperService:
    """Servicio para scrapear noticias de acciones"""
    
    def __init__(self):
        """Inicializa el servicio de noticias"""
        self.mongo_client = MongoClient(Config.MONGO_URI)
        self.db = self.mongo_client[Config.MONGO_DB_NAME]
        self.articles_collection = self.db[Config.MONGO_COLLECTION_ARTICLES]
        logger.info("News Scraper iniciado")
    
    def fetch_yahoo_finance_news(self, symbol):
        """
        Obtiene noticias de Yahoo Finance para una acción
        
        Args:
            symbol: Símbolo de la acción
        
        Returns:
            Lista de artículos
        """
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': f'https://finance.yahoo.com/quote/{symbol}',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                # Dummy cookie for browser-like behavior
                'Cookie': 'GUCS=AXgAAg; yid=YF8AAg;'
            }
            

            session = requests.Session()
            session.headers.update(headers)
            # Initial GET to Yahoo homepage to set cookies
            try:
                session.get('https://finance.yahoo.com', timeout=10)
            except Exception:
                pass

            response = session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Buscar elementos de noticias (la estructura puede variar)
            news_items = soup.find_all('h3', limit=10)

            for item in news_items:
                try:
                    title = item.get_text(strip=True)
                    link_elem = item.find_parent('a')
                    link = link_elem.get('href') if link_elem else None

                    if link and not link.startswith('http'):
                        link = f"https://finance.yahoo.com{link}"

                    article = {
                        'symbol': symbol,
                        'title': title,
                        'link': link,
                        'source': 'Yahoo Finance',
                        'scraped_at': datetime.now(),
                        'published_date': datetime.now()  # Yahoo no siempre proporciona fecha exacta
                    }

                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Error parseando artículo: {e}")
                    continue

            logger.info(f"Obtenidos {len(articles)} artículos para {symbol} de Yahoo Finance")
            return articles
            
        except Exception as e:
            logger.error(f"Error obteniendo noticias de Yahoo Finance para {symbol}: {e}")
            return []
    
    def filter_relevant_articles(self, articles, keywords=None):
        """
        Filtra artículos relevantes basado en keywords
        
        Args:
            articles: Lista de artículos
            keywords: Lista de palabras clave
        
        Returns:
            Lista de artículos filtrados
        """
        if not keywords:
            keywords = ['earnings', 'revenue', 'profit', 'acquisition', 'merger', 
                       'CEO', 'product', 'launch', 'innovation']
        
        filtered = []
        for article in articles:
            title_lower = article['title'].lower()
            # Calcular relevance_score si contiene keywords
            article['relevance_score'] = sum(
                1 for kw in keywords if kw.lower() in title_lower
            )
            filtered.append(article)
        # Ordenar por relevancia
        filtered.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return filtered
    
    def save_articles(self, articles):
        """
        Guarda artículos en MongoDB (evitando duplicados)
        
        Args:
            articles: Lista de artículos
        """
        saved_count = 0
        
        for article in articles:
            # Filtrar artículos sin link válido
            if not article.get('link'):
                continue
            # Evitar duplicados por título y símbolo
            existing = self.articles_collection.find_one({
                'symbol': article['symbol'],
                'title': article['title']
            })
            if not existing:
                self.articles_collection.insert_one(article)
                saved_count += 1
        
        logger.info(f"Guardados {saved_count} artículos nuevos en MongoDB")
    
    def scrape_all_stocks(self):
        """Scrapea noticias para todas las acciones monitoreadas"""
        logger.info("Iniciando scraping de noticias...")
        
        all_articles = []
        
        for symbol in Config.STOCKS_TO_MONITOR:
            try:
                logger.info(f"Scrapeando noticias para {symbol}...")
                
                # Yahoo Finance
                yahoo_articles = self.fetch_yahoo_finance_news(symbol)
                all_articles.extend(yahoo_articles)
                
                # Pequeña pausa para evitar rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scrapeando {symbol}: {e}")
                continue
        
        # Filtrar artículos relevantes
        filtered_articles = self.filter_relevant_articles(all_articles)
        
        # Guardar en MongoDB
        self.save_articles(filtered_articles)
        
        logger.info(f"Scraping completado. Total de artículos relevantes: {len(filtered_articles)}")
        
        return filtered_articles
    
    def get_daily_summary(self):
        """
        Genera un resumen de las noticias del día
        
        Returns:
            Dict con resumen por acción
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        summary = {}
        
        for symbol in Config.STOCKS_TO_MONITOR:
            articles = list(self.articles_collection.find({
                'symbol': symbol,
                'scraped_at': {'$gte': today}
            }).sort('relevance_score', -1).limit(5))
            
            summary[symbol] = {
                'count': len(articles),
                'top_articles': [
                    {
                        'title': article['title'],
                        'link': article.get('link', ''),
                        'source': article['source']
                    }
                    for article in articles[:3]
                ]
            }
        
        return summary
    
    def close(self):
        """Cierra conexión a MongoDB"""
        self.mongo_client.close()
        logger.info("Conexión cerrada")


def main():
    """Función principal"""
    scraper = NewsScraperService()
    
    try:
        # Scrapear noticias
        scraper.scrape_all_stocks()
        
        # Obtener resumen
        summary = scraper.get_daily_summary()
        
        logger.info(f"Resumen de noticias: {summary}")
        
    except Exception as e:
        logger.error(f"Error en news scraper: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
