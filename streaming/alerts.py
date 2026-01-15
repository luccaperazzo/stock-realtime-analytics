
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pymongo import MongoClient
from config.config import Config
from logs.logger_config import setup_logger

logger = setup_logger('alerts_system')


class AlertService:
    def __init__(self):
        self.smtp_config = Config.SMTP_CONFIG
        self.mongo_client = MongoClient(Config.MONGO_URI)
        self.db = self.mongo_client[Config.MONGO_DB_NAME]
        self.users_collection = self.db[Config.MONGO_COLLECTION_USERS]
        self.alerts_collection = self.db[Config.MONGO_COLLECTION_ALERTS]
        logger.info("Alert service iniciado")
    

    
    def send_email(self, to_email, subject, body):

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_config['sender']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['sender'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email enviado a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email a {to_email}: {e}")
            return False
    
    def create_alert_email(self, symbol, data):
        alert_type = data.get('alert_type', 'price_change')
        
        if alert_type == 'high_volume':
            # Email para alerta de volumen anormalmente alto
            alert_reason = data.get('alert_reason', 'Volumen anormalmente alto')
            color = "#ff9800"  # Naranja para alertas de volumen
            icon = "📊"
            
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f8f9fa; }}
                    .volume {{ font-size: 32px; font-weight: bold; color: {color}; }}
                    .highlight {{ font-size: 20px; font-weight: bold; color: {color}; }}
                    .footer {{ padding: 20px; text-align: center; color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{icon} VOLUMEN ALTO - {symbol}</h1>
                    </div>
                    <div class="content">
                        <h2>Alerta de Volumen Anormalmente Alto</h2>
                        <p><strong>Acción:</strong> {symbol}</p>
                        <p><strong>Razón:</strong> <span class="highlight">{alert_reason}</span></p>
                        <p><strong>Volumen Actual:</strong> <span class="volume">{data.get('volume', 0):,}</span></p>
                        <p><strong>Precio Actual:</strong> ${data.get('price', 0):.2f}</p>
                        <p><strong>Cambio del Día:</strong> {data.get('price_change_pct', 0):+.2f}%</p>
                        <p><strong>Apertura:</strong> ${data.get('open', 0):.2f}</p>
                        <p><strong>Máximo:</strong> ${data.get('high', 0):.2f}</p>
                        <p><strong>Mínimo:</strong> ${data.get('low', 0):.2f}</p>
                        <p><strong>Fecha/Hora:</strong> {data.get('timestamp', '')}</p>
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automático del Sistema de Análisis de Acciones</p>
                        <p><small>Para desuscribirte, ingresa a tu cuenta y desactiva las alertas</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            # Email para alerta de cambio de precio
            price_change = data.get('price_change_pct', 0)
            direction = "📈 SUBIÓ" if price_change > 0 else "📉 BAJÓ"
            color = "#28a745" if price_change > 0 else "#dc3545"
            
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f8f9fa; }}
                    .price {{ font-size: 32px; font-weight: bold; color: {color}; }}
                    .change {{ font-size: 24px; font-weight: bold; color: {color}; }}
                    .footer {{ padding: 20px; text-align: center; color: #6c757d; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{direction} - {symbol}</h1>
                    </div>
                    <div class="content">
                        <h2>Alerta de Cambio Significativo de Precio</h2>
                        <p><strong>Acción:</strong> {symbol}</p>
                        <p><strong>Precio Actual:</strong> <span class="price">${data.get('price', 0):.2f}</span></p>
                        <p><strong>Cambio:</strong> <span class="change">{price_change:+.2f}%</span></p>
                        <p><strong>Apertura:</strong> ${data.get('open', 0):.2f}</p>
                        <p><strong>Máximo:</strong> ${data.get('high', 0):.2f}</p>
                        <p><strong>Mínimo:</strong> ${data.get('low', 0):.2f}</p>
                        <p><strong>Volumen:</strong> {data.get('volume', 0):,}</p>
                        <p><strong>Fecha/Hora:</strong> {data.get('timestamp', '')}</p>
                    </div>
                    <div class="footer">
                        <p>Este es un mensaje automático del Sistema de Análisis de Acciones</p>
                        <p><small>Para desuscribirte, ingresa a tu cuenta y desactiva las alertas</small></p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        return html
    
    def process_alert(self, alert_data):

        symbol = alert_data.get('symbol')
        alert_type = alert_data.get('alert_type', 'price_change')
        alert_reason = alert_data.get('alert_reason', '')
        
        if alert_type == 'price_change':
            price_change = alert_data.get('price_change_pct', 0)
            logger.info(f"Procesando alerta de precio para {symbol}: {price_change:+.2f}%")
        else:
            logger.info(f"Procesando alerta de volumen para {symbol}: {alert_reason}")
        
        # (La lista de usuarios ya la evalúa el consumer y aporta `matched_users`.)
        
        # Enviar solo a `matched_users` (producido por el consumer). Si no hay matched users, no enviar.
        matched = alert_data.get('matched_users')
        if not matched:
            logger.info(f"Alerta para {symbol} no enviada: no hay usuarios que cumplan umbral")
            return

        body = self.create_alert_email(symbol, alert_data)
        if alert_type == 'price_change':
            price_change = alert_data.get('price_change_pct', 0)
            subject = f"🔔 Alerta {symbol}: {price_change:+.2f}%"
        else:
            subject = f"📊 Alerta de Volumen {symbol}"

        for email in matched:
            if self.send_email(email, subject, body):
                self.alerts_collection.update_one(
                    {'_id': alert_data['_id']},
                    {
                        '$push': {
                            'notifications_sent': {
                                'email': email,
                                'sent_at': datetime.now()
                            }
                        }
                    }
                )
    
    def monitor_alerts(self):
        logger.info("Iniciando monitoreo de alertas...")
        
        try:
            # Usar change streams de MongoDB para detectar nuevas alertas
            with self.alerts_collection.watch() as stream:
                for change in stream:
                    if change['operationType'] == 'insert':
                        alert_data = change['fullDocument']
                        self.process_alert(alert_data)
                        
        except KeyboardInterrupt:
            logger.info("Monitoreo de alertas detenido por el usuario")
        except Exception as e:
            logger.error(f"Error en monitoreo de alertas: {e}")
        finally:
            self.mongo_client.close()


def main():
    alert_service = AlertService()
    alert_service.monitor_alerts()


if __name__ == "__main__":
    main()
