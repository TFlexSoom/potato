"""
filename: datasource.py
date: 09/26/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines a datasource (similar to Spring datasource) which
  allows us to develop objects which are both file-backed and SQL backed
"""

from dataclasses import dataclass


class PersistantObject:
    pass

def persistant(cls):
    cls = dataclass(cls)

    