import os
import pyodbc
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def get_connection() -> pyodbc.Connection:
    conn_str = os.environ["IAB_DB_CONNECTION_STRING"]
    return pyodbc.connect(conn_str)


def query(sql: str, params: tuple = ()) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
