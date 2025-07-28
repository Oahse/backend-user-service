"""
Redis connection and caching utilities.
"""
import json
from datetime import timedelta
from typing import Optional, Any, Union
import redis.asyncio as redis
from core.config import settings


class RedisClient:
    """Redis client wrapper with caching utilities."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test the connection
            await self.redis.ping()
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis = None
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self.redis:
            return None
        return await self.redis.get(key)
    
    async def set(
        self, 
        key: str, 
        value: Union[str, dict, list], 
        expire: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional expiration."""
        if not self.redis:
            return False
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        expire = expire or settings.REDIS_CACHE_TTL
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.redis:
            return False
        return bool(await self.redis.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.redis:
            return False
        return bool(await self.redis.exists(key))
    
    async def get_json(self, key: str) -> Optional[Union[dict, list]]:
        """Get JSON value from Redis."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: Union[dict, list], 
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis."""
        return await self.set(key, value, expire)
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis."""
        if not self.redis:
            return 0
        return await self.redis.incrby(key, amount)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if not self.redis:
            return False
        return await self.redis.expire(key, seconds)
    
    async def setex(self, key: str, time: Union[int, timedelta], value: Union[str, dict, list]) -> bool:
        """Set key with expiration time."""
        if not self.redis:
            return False
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        # Convert timedelta to seconds if needed
        if hasattr(time, 'total_seconds'):
            time = int(time.total_seconds())
        
        return await self.redis.setex(key, time, value)
    
    async def hset(self, name: str, key: str, value: Union[str, dict, list]) -> int:
        """Set field in hash."""
        if not self.redis:
            return 0
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.redis.hset(name, key, value)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get field from hash."""
        if not self.redis:
            return None
        return await self.redis.hget(name, key)
    
    async def hgetall(self, name: str) -> dict:
        """Get all fields from hash."""
        if not self.redis:
            return {}
        return await self.redis.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete fields from hash."""
        if not self.redis:
            return 0
        return await self.redis.hdel(name, *keys)
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern."""
        if not self.redis:
            return []
        return await self.redis.keys(pattern)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client."""
    return redis_client