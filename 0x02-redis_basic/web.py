#!/usr/bin/env python3
import requests
import time
from functools import wraps
from typing import Dict

# A dictionary to act as an in-memory cache
cache: Dict[str, str] = {}


def get_page(url: str) -> str:
    '''Retrieves the content of a webpage, either from cache
    or by making a web request.

    Args:
        url (str): The URL of the webpage to retrieve.

    Returns:
        str: The content of the webpage as a string.

    Notes:
        - If the URL is present in the cache,
        the content is returned from the cache.
        - Otherwise, a web request is made, and
        the content is cached for future use.
    '''
    if url in cache:
        print(f"Retrieving from cache: {url}")
        return cache[url]
    else:
        print(f"Retrieving from web: {url}")
        response = requests.get(url)
        result = response.text
        cache[url] = result
        return result


def cache_with_expiration(expiration: int):
    '''Decorator to cache function results with expiration.

    Args:
        expiration (int): The number of seconds before the cache expires.

    Returns:
        Callable: The wrapped function with caching and expiration logic.

    Decorator Notes:
        - This decorator caches the result of the function.
        - If the cached result has expired, recall fuunc.
        - The expiration time is controlled by the `expiration` argument.
    '''
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            '''Wrapper that handles caching with expiration for the
            decorated function.
            '''
            url = args[0]
            key = f"count:{url}"

            # Check if the URL is already in the cache
            if key in cache:
                count, timestamp = cache[key]

                # Check if the cached data has expired
                if time.time() - timestamp > expiration:
                    result = func(*args, **kwargs)
                    cache[key] = (count + 1, time.time())
                    return result
                else:
                    # If not expired, update the count and return cached result
                    cache[key] = (count + 1, timestamp)
                    return cache[url]
            else:
                # If not in cache, call the function and cache the result
                result = func(*args, **kwargs)
                cache[key] = (1, time.time())
                return result
        return wrapper
    return decorator
