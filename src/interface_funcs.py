import sqlite3
from pathlib import Path


def create_bank_activity_table(conn: sqlite3.Connection) -> None:
    """
    Create the bank activity table in the SQLite database.

    Args:
        conn (sqlite3.Connection): SQLite database connection.

    Returns:
        None
    """
    query = """
        CREATE TABLE
            bank_activity(
                ID INTEGER PRIMARY KEY,
                Account_Alias,
                Transaction_ID,
                Details,
                Posting_Date,
                Description,
                Amount,
                Type,
                Balance,
                Check_or_Slip_num,
                Reconciled,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );"""
    conn.execute(query)


def check_bank_activity_table_exists(conn: sqlite3.Connection) -> None:
    """
    Check if the bank activity table exists in the SQLite database.

    Args:
        conn (sqlite3.Connection): SQLite database connection.

    Returns:
        None
    """
    query = """
        SELECT
            Account_Alias,
            Transaction_ID,
            Details,
            Posting_Date,
            Description,
            Amount,
            Type,
            Balance,
            Check_or_Slip_num,
            Reconciled,
            Timestamp
        FROM
            bank_activity;"""
    conn.execute(query)

def create_pending_transactions_table(conn: sqlite3.Connection) -> None:
    """
    Create the pending transactions table in the SQLite database.

    Args:
        conn (sqlite3.Connection): SQLite database connection.

    Returns:
        None
    """
    query = """
        CREATE TABLE
            pending_transactions(
                ID INTEGER PRIMARY KEY,
                Account_Alias,
                Transaction_ID,
                Details,
                Posting_Date,
                Description,
                Amount,
                Type,
                Balance,
                Check_or_Slip_num,
                Reconciled,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );"""
    conn.execute(query)

def db_connection(path: str) -> sqlite3.Connection:
    """
    Connect to an SQLite database, creating it if it doesn't exist, and return the connection.

    Args:
        path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Connection to the SQLite database.

    Raises:
        WrongFileExtension: If the file extension is not ".db".
        SQLOperationalError: If the query could not be executed correctly.
    """
    file = Path(path)
    filepath = str(file.absolute()).replace("\\", "/")

    new_db = not file.is_file()

    if file.suffix != ".db":
        msg = f"File extension is not '.db':\n{filepath}"
        raise WrongFileExtension(msg)

    con = sqlite3.connect(path)

    try:
        if new_db:
            create_bank_activity_table(con)
            create_pending_transactions_table(con)
            print(f"Created new DB:\n{filepath}")
        else:
            check_bank_activity_table_exists(con)
    except Exception as e:
        raise SQLOperationalError(e)

    return con


def pathlib_path(filepath: str) -> str:
    """
    Check if a file exists and return its path.

    Args:
        filepath (str): Path to the file.

    Returns:
        str: Path to the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    msg = f"File was not found:\n{filepath}"
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(msg)
    return filepath


class WrongFileExtension(Exception):
    """Exception raised when the file extension is incorrect."""
    pass


class SQLOperationalError(Exception):
    """Exception raised when the query could not be executed correctly."""
    pass


class ConfigSectionIncompleteError(Exception):
    """Exception raised when a configuration section is incomplete."""
    pass


class DuplicateAliasError(Exception):
    """Exception raised when a duplicate alias is encountered."""
    pass


class QueryNotDefinedError(Exception):
    """Exception raised when a query is not defined."""
    pass


class BadQueryStructureError(Exception):
    """Exception raised for queries with bad structure."""
    pass


class UnknownAliasError(Exception):
    """Exception raised for unknown aliases."""
    pass