

from dataclasses import dataclass

from cachetools import TTLCache, cached
from potato.flask_app.modules.auth.form import Uuid
from potato.flask_app.modules.persistence.module import from_created_persistence
from potato.server_utils.json_utils import json_write, write_data_to_truncated_file
from potato.server_utils.query_utils import QueryType, query

@cached(cache=TTLCache(maxsize=2024, ttl=3600)) # Persist for an hour
def user_from_uuid(uuid: Uuid):
    return from_created_persistence(User, UserKey(uuid))

@dataclass
class User:
    uuid: Uuid
    username: str
    password: str

@dataclass
class UserKey:
    uuid: Uuid

@query(type=QueryType.SelectQuery)
def select_query(conn, user_key):
    return conn.execute(
        """
        SELECT uuid, username, password
        FROM auth
        WHERE uuid = %s
        ;
        """,
        (user_key.uuid)
    )

@query(type=QueryType.InsertQuery)
def insert_query(conn, user, _users):
    return conn.execute(
        """
        INSERT INTO auth SET
            uuid = %s
            username = %s 
            password = %s
            ;
        """,
        (user.uuid, user.username, user.password)
    )


@json_write
def users_write(filename, _user, users):
    rows = []
    for user in users:
        rows.append({
            "uuid" : user.uuid,
            "username": user.username,
            "password": user.password,
        })

    return write_data_to_truncated_file(filename, rows)
    
    