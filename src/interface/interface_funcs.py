import sqlite3
from pathlib import Path
from datetime import datetime

def pathlib_csv_path(path):
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
    def create_bank_transactions_table(conn):
        query = """
            CREATE TABLE
                bank_transactions(ID INTEGER PRIMARY KEY, Account_Alias, Transaction_ID, Details, 
                    Posting_Date, Description,  Amount, 
                    Type, Balance, Check_or_Slip_num,
                    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
        """
        conn.execute(query)

    def create_reconcilables_table(conn):
        query = """
            CREATE TABLE
                reconcilables(Reconcilable_ID TEXT PRIMARY KEY, Expense_Alias, Bank_Transaction_Description_Pattern, 
                              Extra_Condition, Recurrence, Amount, Type, Sub_Type, Upcoming_Date, Active 
                              GUID, Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
        """
        conn.execute(query)

    def create_reconciled_archive_table(conn):
        query = """
            CREATE TABLE 
                reconciled(ID INTEGER PRIMARY KEY, Reconcilable_ID, Expense_Alias, Bank_Transaction_Description_Pattern, Extra_Condition, 
                          Recurrence, Amount, Type, Sub_Type, Upcoming_Date, Active
                          GUID, Date_Reconciled, bank_transactions_Transaction_ID, 
                          Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
        """
        conn.execute(query)

    def check_transactions_table_exists(conn):
        query = """
            SELECT 
                    Account_Alias, Transaction_ID, Details, 
                    Posting_Date, Description, Amount, 
                    Type, Balance, Check_or_Slip_num, Timestamp
            FROM
                    bank_transactions;
        """
        conn.execute(query)

    def check_reconcilable_table_exists(conn):
        query = """
            SELECT 
                    Reconcilable_ID, Expense_Alias, Bank_Transaction_Description_Pattern, 
                    Extra_Condition, Recurrence, Amount, Type, Sub_Type, 
                    Upcoming_Date, Timestamp, Active
            FROM
                    reconcilables;
        """
        conn.execute(query)

    def check_reconciled_archive_table_exists(conn):
        query = """
            SELECT 
                    ID, Reconcilable_ID, Expense_Alias, Bank_Transaction_Description_Pattern, 
                    Extra_Condition, Recurrence, Amount, Type, Sub_Type, 
                    Upcoming_Date, Timestamp, bank_transactions_Transaction_ID
            FROM
                    reconciled;
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
        create_bank_transactions_table(con)
        create_reconcilables_table(con)
        create_reconciled_archive_table(con)
        print(f"Created new DB:\n{filepath}")

    else:
        try:
            check_transactions_table_exists(con)
            check_reconcilable_table_exists(con)
            check_reconciled_archive_table_exists(con)
            print(f"Connected to existing DB:\n{filepath}")
        except sqlite3.OperationalError as e:
            raise TransactionsTableDoesNotExist(e)

    return con

def get_day_from_date(date_str, date_format):
    date = datetime.strptime(date_str, date_format)
    return int(date.strftime("%d"))

def is_capital_one_liz(amount, date_str, date_format):
    """"Condition":Amount has to be <=-60 and >=-80 AND 
    day of date has to be between 4 and 7 including ends
    """
    day = get_day_from_date(date_str, date_format)
    if amount >= -80 and amount >= -60 and day >= 4 and day <= 7:
        return True
    return False

def is_capital_one_irving(amount, date_str, date_format):
    """""Condition: Amount has to be <=-70 and >=-105 AND 
    day of date has to be between 4 and 11 including ends
    """
    day = get_day_from_date(date_str, date_format)
    if amount >= -105 and amount >= -70 and day >= 4 and day <= 11:
        return True
    return False

def is_capital_one_quicksilver(amount, date_str, date_format):
    """""Condition: both is_capital_one_A() and is_capital_one_B() return False
    """
    return not is_capital_one_irving(amount, date_str, date_format) and \
        not is_capital_one_liz(amount, date_str, date_format)

def is_chase_amazon(amount, date_str, date_format):
    """Condition: day is greater than 10"""
    return get_day_from_date(date_str, date_format) > 10

def is_chase_irving(amount, date_str, date_format):
    """Condition: is_chase_amazon returns False and amount > 60"""
    return not is_chase_amazon(amount, date_str, date_format) and amount > 60

def is_chase_liz(amount, date_str, date_format):
    """Condition: is_chase_irving returns False"""
    return not is_chase_irving(amount, date_str, date_format)

def is_conns_A(amount, date_str, date_format):
    """Condition: day is less than 12"""
    return get_day_from_date(date_str, date_format) < 12

def is_conns_B(amount, date_str, date_format):
    """Condition: is_conns_A returns False"""
    return not is_conns_A(amount, date_str, date_format)

class WrongFileExtension(Exception):
    """"Custom exception"""

class TransactionsTableDoesNotExist(Exception):
    """"Custom exception"""