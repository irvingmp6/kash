import hashlib
import pandas as pd
from datetime import datetime

from .user_settings import UserSettings

select_transaction_ids_from_transactions_table = "SELECT transaction_id FROM bank_transactions;"
select_all_from_transactions_table = "SELECT * FROM bank_transactions;"
insert_into_bank_transactions_table = """
    INSERT INTO bank_transactions (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

def format_date(date_str, raw_format, new_format):
    date_obj = datetime.strptime(date_str, raw_format)
    return date_obj.strftime(new_format)

class Controller:
    def __init__(self, args):
        self.user_settings = UserSettings(args)
        self.conn = self.user_settings.conn
        self.new_transactions_csv_list = \
            self.user_settings.new_transactions_csv_list
        self.commit = self.user_settings.commit

    def start_process(self):
        if self.new_transactions_csv_list:
            self.ingest_new_transactions_csv()

    def ingest_new_transactions_csv(self):
        for csv_file in self.new_transactions_csv_list:
            new_transactions_df = self.get_new_transactions_df(csv_file)
            self.insert_df_into_bank_transactions_table(new_transactions_df)

    def get_new_transactions_df(self, csv_file):
        csv_trans_df = self.create_dataframe_from_chase_csv(csv_file)
        csv_trans_df = csv_trans_df[csv_trans_df['Balance'] != ' ']
        cursor = \
            self.conn.execute(select_transaction_ids_from_transactions_table).fetchall()
        transaction_ids_from_bank_transactions_table = [record[0] for record in cursor]
        return \
            csv_trans_df[~csv_trans_df["Transaction ID"].isin(\
                transaction_ids_from_bank_transactions_table)]

    def create_dataframe_from_chase_csv(self, csv_file, account_alias="Chase 9365"):
        names = ["Details","Posting Date","Description","Amount","Type","Balance","Check or Slip #","Extra 1"]
        converters = {"Balance": str}
        df = pd.read_csv(csv_file, delimiter=",", skiprows=[0], header=None, names=names, \
                         converters=converters)
        transaction_ids = []
        account_aliases = []
        for _, row in df.iterrows():
            details = row["Details"]
            posting_date = row["Posting Date"]
            description = row["Description"]
            amount = str(row["Amount"])
            type_ = row["Type"]
            balance = row["Balance"]
            check_or_slip_num = str(row["Check or Slip #"])
            hashable = "".join([details, posting_date, description, amount, type_, balance, \
                                check_or_slip_num, account_alias])
            transaction_id = hashlib.sha256(hashable.encode()).hexdigest()
            transaction_ids.append(transaction_id)
            account_aliases.append(account_alias)
        df.insert(0, "Transaction ID", transaction_ids, True)
        df.insert(1, "Account Alias", account_aliases, True)
        return df

    def insert_df_into_bank_transactions_table(self, df):
        df = df.reset_index()
        for _, row in df.iterrows():
            account_alias = row["Account Alias"]
            transaction_id = row['Transaction ID']
            details = row["Details"]
            posting_date = row["Posting Date"]
            formatted_posting_date = format_date(posting_date, "%m/%d/%Y", "%Y-%m-%d")
            description = row["Description"]
            amount = row["Amount"]
            type_ = row["Type"]
            balance = row["Balance"]
            check_or_slip_num = row["Check or Slip #"]
            reconciled = 'N'
            values = (account_alias, transaction_id, details, formatted_posting_date, \
                      description, 
                      amount, type_, balance, check_or_slip_num, reconciled)
            if self.commit:
                self.conn.execute(insert_into_bank_transactions_table, values)
        print(f"[+] Adding {len(df.index)} new transactions:")
        print(df["Transaction ID"])
        if self.commit:
            self.conn.commit()