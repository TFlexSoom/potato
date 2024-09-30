"""

"""


from dataclasses import dataclass
from typing import Any, Callable, NewType

SQLString = NewType('SQLString', str)
SQLResult = NewType('SQLResult', Any)
JsonResult = NewType('JsonResult', Any)
CsvResult = NewType('CsvResult', Any)
YamlResult = NewType('YamlResult', Any)
Filename = NewType('Filename', str)
Result = NewType('Result', Any)

@dataclass
class Json:
    filename: str
    values: dict

@dataclass
class Csv:
    filename: str
    values: list[str]

@dataclass
class PersistanceLayer:
    query_object: Callable[[
        Filename, 
        SQLString, 
        Callable[[JsonResult], Result], 
        Callable[[SQLResult], Result]], 
        Result
    ]

    query_rows: Callable[[
        Filename, 
        SQLString, 
        Callable[[CsvResult], Result], 
        Callable[[SQLResult], Result]], 
        Result
    ]

    query_config: Callable[[
        Filename,
        SQLString,
        Callable[[YamlResult], Result],
        Callable[[SQLResult], Result],
        Result
    ]]
        
    accept_object: Callable[[Json, SQLString], bool]
    accept_rows: Callable[[Csv, SQLString], bool]