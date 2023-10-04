import os
import argparse
import sqlite3

query = """

SELECT 
        count(*)
FROM
    bank_transactions
WHERE
    account_alias = 'Chase 9365'
;

"""

def get_args():
    cli = argparse.ArgumentParser()
    cli.add_argument('sqlite_db')
    return cli.parse_args()

def main():
        args = get_args()
        path = args.sqlite_db
        if os.path.isfile(path):      
            conn = sqlite3.connect(path)
            cursor = conn.execute(query)
            print(cursor.fetchall())
            conn.close()
        else:
             print(f"Path does not exist:\n{path}")


if __name__ == "__main__":
    main()