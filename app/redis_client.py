import redis
import os

# Настройка подключения к Redis
redis_client = redis.StrictRedis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
