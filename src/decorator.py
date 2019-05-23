"""DB lock decorator function used in endpoint functions."""

from typing import Callable
from flask import current_app
import rocksdb


def setup_database(function) -> Callable:
    """Decorator that handlex exclusive access, and DB opening/closing."""
    def wrapper(*args, **kwargs):
        db_path = current_app.config['DB_LOCATION']
        db_lock = current_app.config['DB_LOCK']
        db_lock.acquire()
        db = rocksdb.DB(db_path, rocksdb.Options(create_if_missing=True, max_open_files=10000),
                        read_only=True)
        value = function(*args, **kwargs, db=db)
        del db
        db_lock.release()
        return value
    return wrapper
