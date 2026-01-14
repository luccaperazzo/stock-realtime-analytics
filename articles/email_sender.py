"""
Email Sender - Envía resúmenes diarios de noticias a usuarios
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pymongo import MongoClient
from config.config import Config
from logs.logger_config import setup_logger
from articles.news_scraper import NewsScraperService

logger = setup_logger('email_sender')


class NewsEmailService:
    """Servicio para enviar resúmenes de noticias por email"""
    
    def __init__(self):
        """Inicializa el servicio de emails"""
        self.smtp_config = Config.SMTP_CONFIG
        self.mongo_client = MongoClient(Config.MONGO_URI)
        self.db = self.mongo_client[Config.MONGO_DB_NAME]
        self.users_collection = self.db[Config.MONGO_COLLECTION_USERS]
        self.scraper = NewsScraperService()
        logger.info("News Email Service iniciado")
    
    def create_news_summary_html(self, summary_data):
        """
        Crea HTML para el resumen de noticias
        
        Args:
            summary_data: Datos del resumen
        
        Returns:
            str: HTML del email
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 700px;
                    margin: 20px auto;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    padding: 30px;
                }}
                .stock-section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    border-left: 4px solid #667eea;
                }}
                .stock-title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 15px;
                }}
                .article {{
                    padding: 15px;
                    margin: 10px 0;
                    background-color: white;
                    border-radius: 4px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .article-title {{
                    font-size: 16px;
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .article-title:hover {{
                    text-decoration: underline;
                }}
                .article-source {{
                    font-size: 12px;
                    color: #6c757d;
                    margin-top: 5px;
                }}
                .footer {{
                    padding: 20px;
                    text-align: center;
                    background-color: #f8f9fa;
                    border-radius: 0 0 8px 8px;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .badge {{
                    background-color: #667eea;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📰 Daily News Summary</h1>
                    <p>{datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                <div class="content">
                    {self._create_stock_sections(summary_data)}
                </div>
                <div class="footer">
                    <p>📈 Stock Analytics System</p>
                    <p><small>This is an automated message. To change your preferences, log in to your account.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_stock_sections(self, summary_data):
        """Crea secciones HTML para cada acción"""
        sections = ""
        
        for symbol, data in summary_data.items():
            count = data['count']
            articles = data['top_articles']
            if count == 0:
                continue
            sections += f"""
            <div class="stock-section">
                <div class="stock-title">
                    {symbol} <span class="badge">{count} news</span>
                </div>
            """
            for article in articles:
                sections += f"""
                <div class="article">
                    <a href="{article['link']}" class="article-title" target="_blank">
                        {article['title']}
                    </a>
                    <div class="article-source">📰 {article['source']}</div>
                </div>
                """
            sections += "</div>"
        return sections if sections else "<p>No new news today.</p>"
    
    def send_email(self, to_email, subject, html_body):
        """
        Envía un email
        
        Args:
            to_email: Email destinatario
            subject: Asunto
            html_body: Cuerpo HTML
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config['sender']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['sender'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Resumen de noticias enviado a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email a {to_email}: {e}")
            return False
    
    def send_daily_summaries(self):
        """Envía resúmenes diarios a todos los usuarios activos"""
        logger.info("Enviando resúmenes diarios de noticias...")
        
        # Obtener resumen de noticias
        summary = self.scraper.get_daily_summary()
        
        # Obtener usuarios con news_summary_enabled
        users = self.users_collection.find({'news_summary_enabled': True})
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Filtrar resumen según acciones suscritas del usuario
                user_stocks = user.get('subscribed_stocks', [])
                user_summary = {
                    symbol: data 
                    for symbol, data in summary.items() 
                    if symbol in user_stocks
                }
                
                if not user_summary:
                    logger.info(f"No hay noticias para {user['email']}")
                    continue
                
                # Crear y enviar email
                html = self.create_news_summary_html(user_summary)
                subject = f"📰 Resumen de Noticias - {datetime.now().strftime('%d/%m/%Y')}"
                
                if self.send_email(user['email'], subject, html):
                    sent_count += 1
                else:
                    failed_count += 1
                
            except Exception as e:
                logger.error(f"Error procesando usuario {user.get('email', 'unknown')}: {e}")
                failed_count += 1
                continue
        
        logger.info(f"Resúmenes enviados: {sent_count}, Fallidos: {failed_count}")
    
    def close(self):
        """Cierra conexiones"""
        self.mongo_client.close()
        self.scraper.close()
        logger.info("Conexiones cerradas")


def main():
    """Función principal"""
    email_service = NewsEmailService()
    
    try:
        email_service.send_daily_summaries()
    except Exception as e:
        logger.error(f"Error en email sender: {e}")
    finally:
        email_service.close()


if __name__ == "__main__":
    main()
