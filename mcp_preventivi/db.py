import os
from contextlib import closing

import pyodbc
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def get_connection() -> pyodbc.Connection:
    conn_str = os.environ.get("IAB_DB_CONNECTION_STRING")
    if not conn_str:
        raise ValueError(
            "IAB_DB_CONNECTION_STRING environment variable is not set. "
            "Copy mcp_preventivi/.env.example to mcp_preventivi/.env and fill in the connection string."
        )
    return pyodbc.connect(conn_str)


def query(sql: str, params: tuple = ()) -> list[dict]:
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql, params)
            if cursor.description is None:
                return []
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
