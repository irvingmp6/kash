from pathlib import Path
import sqlite3


class WrongFileExtension(Exception):
    """"Custom exception"""

class TransactionsTableDoesNotExist(Exception):
    """"Custom exception"""

def pathlib_path(path):
    file = Path(path)
    filepath = str(file.absolute()).replace("\\","/")

    msg = (f"File was not found:\n{filepath}")
    if not file.is_file():
        raise FileNotFoundError(msg)

    if file.suffix == "csv":
        msg = (f"File extenstion is not csv:\n{filepath}")
        raise WrongFileExtension(msg)

    return file

def db_connection(path):
    def create_transactions_table(con):
        query = """
            CREATE TABLE 
                transactions(Transaction_ID, Details, 
                    Posting_Date, Description, 
                    Amount, Type, Balance, 
                    Check_or_Slip_num)
        """
        cur = con.execute(query)
   
    def check_transactions_table_exists(con):
        query = """
            SELECT 
                    Transaction_ID, Details, Posting_Date, 
                    Description, Amount, Type,Balance, Check_or_Slip_num
            FROM
                    transactions
        """
        con.execute(query)
        con.commit()
  
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
        create_transactions_table(con)
        print(f"Created new DB:\n{filepath}")

    else:
        try:
            check_transactions_table_exists(con)
            print(f"Connected to existing DB:\n{filepath}")
        except sqlite3.OperationalError as e:
            raise TransactionsTableDoesNotExist(e)

    return con