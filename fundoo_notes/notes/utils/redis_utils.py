from typing import Any
from django.core.exceptions import ValidationError
from django.core.cache import cache
from loguru import logger

class RedisUtils:
    """
    Utility class to interact with Redis cache.
    Provides methods for saving, getting, and deleting cached data.
    """

    @staticmethod
    def get_cache_key(user_id: int) -> str:
        """
        Generate a Redis cache key based on user ID
        Parameters:
            user_id (int): The ID of the user.
        Returns:
            str: The generated cache key, e.g., 'user_1'.
        """
        return f"user_{user_id}"

    @staticmethod
    def save(key: str, value: Any, timeout: int = 3600) -> None:
        """
        Save data to cache.
        Parameters:
            key (str): The cache key.
            value (Any): The value to cache.
            timeout (int): The cache timeout in seconds.
        """
        try:
            cache.set(key, value, timeout)
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
            raise ValidationError(f"Error saving to cache: {str(e)}")

    @staticmethod
    def get(key: str) -> Any:
        """
        Retrieve data from cache.
        Parameters:
            key (str): The cache key.
        Returns:
            Any: The cached value or None if the key does not exist.
        """
        try:
            return cache.get(key)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            raise ValidationError(f"Error retrieving from cache: {str(e)}")

    @staticmethod
    def delete(key: str) -> None:
        """
        Delete data from cache.
        Parameters:
            key (str): The cache key.
        """
        try:
            cache.delete(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            raise ValidationError(f"Error deleting from cache: {str(e)}")
