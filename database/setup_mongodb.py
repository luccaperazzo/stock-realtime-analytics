"""
MongoDB Collections Setup and Indexes
Ejecutar este script para crear las colecciones y índices necesarios
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config

def setup_mongodb():
    """Configura colecciones e índices en MongoDB"""
    
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.MONGO_DB_NAME]
    
    print(f"Configurando base de datos: {Config.MONGO_DB_NAME}")
    
    # 1. Colección de precios en tiempo real
    realtime_collection = db[Config.MONGO_COLLECTION_REALTIME]
    realtime_collection.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
    realtime_collection.create_index([("timestamp", DESCENDING)])
    print(f"✓ Colección '{Config.MONGO_COLLECTION_REALTIME}' configurada")
    
    # 2. Colección de artículos de noticias
    articles_collection = db[Config.MONGO_COLLECTION_ARTICLES]
    articles_collection.create_index([("symbol", ASCENDING), ("scraped_at", DESCENDING)])
    articles_collection.create_index([("title", ASCENDING), ("symbol", ASCENDING)], unique=True)
    articles_collection.create_index([("scraped_at", DESCENDING)])
    print(f"✓ Colección '{Config.MONGO_COLLECTION_ARTICLES}' configurada")
    
    # 3. Colección de usuarios
    users_collection = db[Config.MONGO_COLLECTION_USERS]
    users_collection.create_index([("email", ASCENDING)], unique=True)
    users_collection.create_index([("subscribed_stocks", ASCENDING)])
    print(f"✓ Colección '{Config.MONGO_COLLECTION_USERS}' configurada")
    
    # 4. Colección de historial de alertas
    alerts_collection = db[Config.MONGO_COLLECTION_ALERTS]
    alerts_collection.create_index([("symbol", ASCENDING), ("timestamp", DESCENDING)])
    alerts_collection.create_index([("timestamp", DESCENDING)])
    print(f"✓ Colección '{Config.MONGO_COLLECTION_ALERTS}' configurada")
    
    # Insertar usuario de ejemplo (opcional)
    example_user = {
        "name": "Usuario Ejemplo",
        "email": "ejemplo@email.com",
        "subscribed_stocks": ["AAPL", "GOOGL", "MSFT"],
        "alert_threshold": 5.0,
        "alerts_enabled": True,
        "news_summary_enabled": True
    }
    
    if users_collection.count_documents({"email": "ejemplo@email.com"}) == 0:
        users_collection.insert_one(example_user)
        print("✓ Usuario de ejemplo creado")
    
    print("\n✅ MongoDB configurado correctamente")
    print(f"Base de datos: {Config.MONGO_DB_NAME}")
    print(f"Colecciones creadas: {db.list_collection_names()}")
    
    client.close()


if __name__ == "__main__":
    setup_mongodb()
