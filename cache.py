import time
import json
import pickle
from functools import wraps

class Cache:
    def __init__(self, redis):
        self.redis = redis

    def cached(self, timeout, key_prefix):
        def decorator(func):
            @wraps(func)
            def cache(*args, **kwargs):
                value = self.redis.get(key_prefix())
                if value is not None:
                    print("Key " + key_prefix() + " found in cache!")
                    return pickle.loads(value)

                print("Key: " + key_prefix() + " not in cache.")
                value = pickle.dumps(func(*args, **kwargs)[0])
                pipe = self.redis.pipeline()
                pipe.set(key_prefix(), value)
                pipe.expireat(key_prefix(), int(time.time()) + timeout)
                pipe.execute()
                return pickle.loads(value)
            return cache
        return decorator
