"""
filename: query_utils.py
date: 10/1/2024
author: Tristan Hilbert (aka TFlexSoom)
desc: Defines utilities for creating query functions
"""

from enum import Enum

class QueryType(Enum):
    SelectQuery = 1
    InsertQuery = 2
    UpdateQuery = 3
    DeleteQuery = 4

# This will be helpful later testing
def query(func, type: QueryType = QueryType.SelectQuery):
    pass
