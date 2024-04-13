import hashlib
import pandas as pd
from datetime import datetime
from distutils.util import strtobool
from configparser import NoSectionError, NoOptionError

from src.interface.interface_funcs import ConfigSectionIncompleteError
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
        self.new_csv_files = \
            self.user_settings.new_csv_files
        self.commit = self.user_settings.commit
        self.config = self.user_settings.config
        self.chase_column_config_name_map = self.get_chase_column_config_name_map()
        self.chase_column_names = self.get_chase_column_names()

    def get_chase_column_config_name_map(self):
        return {
            "details" : "Details",
            "posting_date" : "Posting Date",
            "description" : "Description",
            "amount" : "Amount",
            "type" : "Type",
            "balance" : "Balance",
            "check_or_slip_number" : "Check or Slip #",
            "extra_1" : "Extra 1"
        }

    def get_chase_column_names(self):
        return [self.chase_column_config_name_map[k]
                for k in self.chase_column_config_name_map.keys()]

    def start_process(self):
        self.ingest_new_transactions_csv()

    def ingest_new_transactions_csv(self):
        for csv_file in self.new_csv_files:
            new_transactions_df = self.get_new_transactions_df(csv_file)
            self.insert_df_into_bank_transactions_table(new_transactions_df)

    def get_new_transactions_df(self, csv_file):
        if self.config:
            csv_trans_df = self.create_dataframe_from_foreign_csv(csv_file, self.user_settings.account_alias)
        else:
            csv_trans_df = self.create_dataframe_from_chase_csv(csv_file, self.user_settings.account_alias)

        csv_trans_df = csv_trans_df[csv_trans_df['Balance'] != ' ']
        cursor = \
            self.conn.execute(select_transaction_ids_from_transactions_table).fetchall()
        transaction_ids_from_bank_transactions_table = [record[0] for record in cursor]
        return \
            csv_trans_df[~csv_trans_df["Transaction ID"].isin(\
                transaction_ids_from_bank_transactions_table)]

    def create_dataframe_from_foreign_csv(self, csv_file, account_alias):
        try:
            header = strtobool(self.config["HEADER"].get("has_header").strip())
        except AttributeError as e:
            message = (f"{e}.\nTroubleshooting help: Ensure the HEADER section contains the proper definitions"
                       f" in the config file. Refer to the configs provided in src/test_files/ for help.")
            raise ConfigSectionIncompleteError(message)
        temp_df = pd.read_csv(csv_file, delimiter=",", header=None, skiprows=[0])
        converters = {i: str for i in range(temp_df.shape[1])}
        if header:
            df = pd.read_csv(csv_file, delimiter=",", header=None, converters=converters, skiprows=[0])
        else:
            df = pd.read_csv(csv_file, delimiter=",", header=None, converters=converters)
        df = self.convert_dataframe_to_chase_format(df)
        return self.create_ingesitble_df(df, account_alias)

    def convert_dataframe_to_chase_format(self, df):
        # Create list of blank values the same size of the df
        count_row = df.shape[0]
        empty_values = ["" for _ in range(count_row)]

        # Create Chase columns with blank values
        for name in self.chase_column_names:
            df.insert(df.shape[1], name, empty_values, True)

        # Replace the Chase blank values using existing columns 
        try:
            for key in self.config["GENERAL"]:
                value = self.config["GENERAL"][key].strip()
                if value:
                    index = int(value)
                    df[self.chase_column_config_name_map[key]] = df[index]
        except KeyError as e:
            message = (f"{e}.\nTroubleshooting help: Ensure the GENERAL section contains the proper definitions"
                       f" in the config file. Refer to the configs provided in src/test_files/ for help.")
            raise ConfigSectionIncompleteError(message)

        # Drop columns that you don't need
        df = df.loc[:, df.columns.intersection(self.chase_column_names)]
        return df

    def create_dataframe_from_chase_csv(self, csv_file, account_alias):
        converters = {"Balance": str}
        df = pd.read_csv(csv_file, delimiter=",", skiprows=[0], header=None, names=self.chase_column_names, \
                         converters=converters)
        return self.create_ingesitble_df(df, account_alias)

    def create_ingesitble_df(self, df, account_alias):
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
