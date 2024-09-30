"""
filename: cache.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Cacheing Annotations for data cached within
   the process boundary but outside the flask application
"""

from functools import lru_cache

def singleton(func):
    return lru_cache(maxsize=None)(func)