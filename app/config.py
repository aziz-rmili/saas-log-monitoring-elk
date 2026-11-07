"""Configuration lue depuis les variables d'environnement (définies dans docker-compose.yml)."""
import os

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
