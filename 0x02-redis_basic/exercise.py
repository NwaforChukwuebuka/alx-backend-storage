#!/usr/bin/env python3
import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    '''Decorator to count the number of times a method is called.

    Args:
        method (Callable): The method whose calls are to be counted.

    Returns:
        Callable: The wrapper method that increments the call count.
    '''
    @wraps(method)
    def wrapper(self, *args, **kwds):
        '''Wrapper function that increments the call count.'''
        key_name = method.__qualname__
        self._redis.incr(key_name)
        return method(self, *args, **kwds)
    return wrapper


def call_history(method: Callable) -> Callable:
    '''Decorator to store the history of inputs and outputs of a method.

    Args:
        method (Callable): The method whose input/output history is stored.

    Returns:
        Callable: The wrapper method that stores the input and output history.
    '''
    @wraps(method)
    def wrapper(self, *args, **kwds):
        '''Wrapper function that stores input and output history.'''
        key_m = method.__qualname__
        inp_m = key_m + ':inputs'
        outp_m = key_m + ":outputs"

        # Store input arguments
        data = str(args)
        self._redis.rpush(inp_m, data)

        # Execute the method and store its output
        result = method(self, *args, **kwds)
        self._redis.rpush(outp_m, str(result))

        return result
    return wrapper


def replay(func: Callable):
    '''Displays the history of calls to a method.

    Args:
        func (Callable): The method whose call history is to be replayed.

    Prints:
        Call history with inputs and corresponding outputs.
    '''
    r = redis.Redis()
    key_m = func.__qualname__
    inp_m = r.lrange(f"{key_m}:inputs", 0, -1)
    outp_m = r.lrange(f"{key_m}:outputs", 0, -1)

    calls_number = len(inp_m)
    times_str = 'times' if calls_number != 1 else 'time'

    # Print the number of times the method was called
    print(f'{key_m} was called {calls_number} {times_str}:')

    # Print each input and corresponding output
    for inp, out in zip(inp_m, outp_m):
        print(f'{key_m}(*{inp.decode("utf-8")}) -> '
              f'{out.decode("utf-8")}')


class Cache():
    '''Cache class to store and retrieve data using Redis.

    Attributes:
        _redis (redis.Redis): Redis client instance.
    '''
    def __init__(self):
        '''Initializes the Cache class and flushes the Redis database.'''
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        '''Stores data in Redis with a unique key.

        Args:
            data (Union[str, bytes, int, float]): The data to store.

        Returns:
            str: The unique key generated for the stored data.
        '''
        generate = str(uuid.uuid4())
        self._redis.set(generate, data)
        return generate

    def get(self, key: str,
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        '''Retrieves data from Redis by key, optional convert to  with a func.

        Args:
            key (str): The Redis key.
            fn (Optional[Callable]): A function to apply to the retrieved data.

        Returns:
            Union[str, bytes, int, float]
            '''
        value = self._redis.get(key)
        return value if not fn else fn(value)

    def get_int(self, key: str) -> int:
        '''Retrieves and converts the stored data to an integer.

        Args:
            key (str): The Redis key.

        Returns:
            int: The data converted to an integer.
        '''
        return self.get(key, int)

    def get_str(self, key: str) -> str:
        '''Retrieves and converts the stored data to a string.

        Args:
            key (str): The Redis key.

        Returns:
            str: The data converted to a string.
        '''
        value = self._redis.get(key)
        return (value.decode("utf-8")
                if value else None)
