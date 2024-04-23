import sqlite3
from pathlib import Path
from datetime import datetime

def db_connection(path):
    def create_bank_activity_table(conn):
        query = """
            CREATE TABLE
                bank_activity(ID INTEGER PRIMARY KEY, Account_Alias, Transaction_ID, Details, 
                    Posting_Date, Description,  Amount, 
                    Type, Balance, Check_or_Slip_num, Reconciled,
                    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
        """
        conn.execute(query)

    def check_bank_activity_table_exists(conn):
        query = """
            SELECT 
                    Account_Alias, Transaction_ID, Details, 
                    Posting_Date, Description, Amount, Type, 
                    Balance, Check_or_Slip_num, Reconciled, 
                    Timestamp
            FROM
                    bank_activity;
        """
        conn.execute(query)

    file = Path(path)
    filepath = str(file.absolute()).replace("\\","/")

    new_db = False
    if not file.is_file():
        new_db = True

    if file.suffix == "db":
        msg = (f"File extenstion is not db:\n{filepath}")
        raise WrongFileExtension(msg)

    con = sqlite3.connect(path)

    if new_db:
        create_bank_activity_table(con)
        print(f"Created new DB:\n{filepath}")

    else:
        try:
            check_bank_activity_table_exists(con)
            print(f"Connected to existing DB:\n{filepath}")
        except sqlite3.OperationalError as e:
            raise TransactionsTableDoesNotExist(e)

    return con

def pathlib_path(filepath):
    msg = (f"File was not found:\n{filepath}")
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(msg)
    return filepath

class WrongFileExtension(Exception):
    """"Custom exception"""

class TransactionsTableDoesNotExist(Exception):
    """"Custom exception"""

class ConfigSectionIncompleteError(Exception):
    """Custom exception"""