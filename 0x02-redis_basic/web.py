#!/usr/bin/env python3
"""
Caching request module with Redis and expiration
"""
import redis
import requests
from functools import wraps
from typing import Callable

# Create a Redis client instance
client = redis.Redis()


def track_get_page(fn: Callable) -> Callable:
    """Decorator for get_page that tracks the number of calls and
    handles caching with expiration.

    The wrapper:
    - Tracks how many times `get_page` is called for a specific URL.
    - Caches the response in Redis with a 10-second expiration.
    """
    @wraps(fn)
    def wrapper(url: str) -> str:
        # Increment the count for the given URL
        client.incr(f'count:{url}')

        # Check if the response for the URL is cached
        cached_page = client.get(f'{url}')
        if cached_page:
            # If cached, return the cached content
            print(f"Retrieving from cache: {url}")
            return cached_page.decode('utf-8')

        # Otherwise, make the request and cache the result for 10 seconds
        print(f"Retrieving from web: {url}")
        response = fn(url)
        client.setex(f'{url}', 10, response)
        return response

    return wrapper


@track_get_page
def get_page(url: str) -> str:
    """Makes an HTTP request to a given URL and returns the page content."""
    response = requests.get(url)
    return response.text
