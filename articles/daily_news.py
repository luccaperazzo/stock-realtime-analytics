"""
Daily News - Script principal para scraper y envío de emails
Se ejecuta una vez al día via cron
"""
from articles.news_scraper import NewsScraperService
from articles.email_sender import NewsEmailService
from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('daily_news')


def main():
    """Ejecuta el proceso completo de noticias diarias"""
    try:
        logger.info("=== Iniciando proceso de noticias diarias ===")
        
        # 1. Scraper noticias
        logger.info("Paso 1: Scraping de noticias")
        scraper = NewsScraperService()
        
        for symbol in Config.STOCKS:
            logger.info(f"Buscando noticias para {symbol}")
            scraper.scrape_all_sources(symbol)
        
        scraper.close()
        logger.info("Scraping completado")
        
        # 2. Enviar emails
        logger.info("Paso 2: Enviando resúmenes por email")
        email_service = NewsEmailService()
        email_service.send_daily_summary()
        email_service.close()
        
        logger.info("=== Proceso de noticias diarias completado ===")
        
    except Exception as e:
        logger.error(f"Error en proceso de noticias diarias: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
