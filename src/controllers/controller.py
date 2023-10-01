import hashlib

import pandas as pd

from src.interface.user_settings import UserSettings

select_transaction_ids = "SELECT transaction_id FROM transactions;"
select_all_from_transactions = "SELECT * FROM transactions;"
insert_into_transaction_table = """
    INSERT INTO transactions (Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?);
"""

class Controller:
    def __init__(self, args):
        self.user_settings = UserSettings(args)
        self.conn = self.user_settings.conn
        self.new_transaction_csv_file = self.user_settings.new_transactions_csv

    def start_process(self):
        new_transactions_csv = self.user_settings.new_transactions_csv
        if new_transactions_csv:
            self.ingest_new_transactions_csv()
        cur = self.conn.execute("SELECT count(*) FROM transactions;") # TODO: Used for Dev purposes; Remove or uncommentif in prod
        print(cur.fetchall()) # TODO: Used for Dev purposes; Remove or uncommentif in prod

    def ingest_new_transactions_csv(self):
        new_transactions_df = self.get_new_transactions_df()
        self.insert_df_into_transaction_table(new_transactions_df)

    def get_new_transactions_df(self):
        csv_trans_df = self.create_dataframe_from_csv(self.new_transaction_csv_file)
        csv_trans_df = csv_trans_df[csv_trans_df['Balance'] != ' ']
        cursor = self.conn.execute(select_transaction_ids).fetchall()
        transaction_ids_from_db = [record[0] for record in cursor]
        return csv_trans_df[~csv_trans_df["Transaction ID"].isin(transaction_ids_from_db)]

    def create_dataframe_from_csv(self, csv_file, bank="Chase"):
        names = ["Details","Posting Date","Description","Amount","Type","Balance","Check or Slip #","Extra 1"]
        converters = {"Balance": str}
        df = pd.read_csv(csv_file, delimiter=",", skiprows=[0], header=None, names=names, converters=converters)
        transaction_ids = []
        for _, row in df.iterrows():
            details = row["Details"]
            posting_date = row["Posting Date"]
            description = row["Description"]
            amount = str(row["Amount"])
            type_ = row["Type"]
            balance = row["Balance"]
            check_or_slip_num = str(row["Check or Slip #"])
            hashable = "".join([details, posting_date, description, amount, type_,
                                balance, check_or_slip_num])
            transaction_id = hashlib.sha256(hashable.encode()).hexdigest()
            transaction_ids.append(transaction_id)
        df.insert(0, "Transaction ID", transaction_ids, True)
        return df

    def insert_df_into_transaction_table(self, df):
        df = df.reset_index()
        for _, row in df.iterrows():
            transaction_id = row['Transaction ID']
            details = row["Details"]
            posting_date = row["Posting Date"]
            description = row["Description"]
            amount = row["Amount"]
            type_ = row["Type"]
            balance = row["Balance"]
            check_or_slip_num = row["Check or Slip #"]
            values = (transaction_id, details, posting_date, description, 
                      amount, type_, balance, check_or_slip_num)
            self.conn.execute(insert_into_transaction_table, values)
        self.conn.commit()
