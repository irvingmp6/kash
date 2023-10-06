import hashlib
import pathlib
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

from src.interface import interface_funcs

from .user_settings import UserSettings

select_transaction_ids_from_transactions_table = "SELECT transaction_id FROM bank_transactions;"
select_all_from_transactions_table = "SELECT * FROM bank_transactions;"
insert_into_bank_transactions_table = """
    INSERT INTO bank_transactions (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""
deactivate_active_records_in_reconcilables_table = """
UPDATE reconcilables
SET active = 'N'
WHERE active = 'Y';
"""
activate_records_in_reconcilables_table = """
UPDATE reconcilables
SET active = 'Y'
WHERE reconcilable_id in {};
"""
select_reconcilable_id_from_reconcilables_tabe = """SELECT reconcilable_id FROM reconcilables;"""
select_active_reconcilables = """SELECT 
Name, Bank_Transaction_Description_Pattern, Extra_Condition, Amount, Upcoming_Date, Recurrence, reconcilable_id, type, sub_type, upcoming_date 
FROM reconcilables WHERE active = 'Y';"""

select_transactions_from_month_to_date = """SELECT * FROM bank_transactions WHERE reconciled != 'Y' and posting_date >= "{}";"""
insert_into_reconcilables_table = """
    INSERT INTO reconcilables (reconcilable_id, Name, Bank_Transaction_Description_Pattern, Extra_Condition, Recurrence, Amount, Type, Sub_Type, Upcoming_Date, Active)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""
insert_into_archive_table = """
    INSERT INTO archive(Reconcilable_ID, Name, Bank_Transaction_Description_Pattern, Extra_Condition, Recurrence, Amount, Type, Sub_Type, Upcoming_Date, bank_transactions_Transaction_ID)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""
update_reconcilable_date = """
    UPDATE reconcilables
    SET upcoming_date = '{}'
    WHERE reconcilable_id == '{}';
"""
update_reconciled_flag_in_bank_transactions_tables = """
    UPDATE bank_transactions
    SET reconciled = 'Y'
    WHERE transaction_id == '{}';
"""

def format_date(date_str, raw_format, new_format):
    date_obj = datetime.strptime(date_str, raw_format)
    return date_obj.strftime(new_format)

def get_month_start_from_date(date_str, date_format):
    date_obj = datetime.strptime(date_str, date_format)
    return date_obj.strftime("%Y-%m-01")

def calculate_new_upcoming_date(date_str, recurrence):
    delta = relativedelta(months=1)
    if recurrence == "B":
        delta = relativedelta(days=14)
    elif recurrence == "A":
        delta = relativedelta(years=1)
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date_obj = date_obj + delta - relativedelta(days=3)
    return new_date_obj.strftime("%Y-%m-%d")


class Controller:
    def __init__(self, args):
        self.user_settings = UserSettings(args)
        self.conn = self.user_settings.conn
        self.new_transactions_csv_list = \
            self.user_settings.new_transactions_csv_list
        self.update_financials = self.user_settings.update_financials
        self.reconcile = self.user_settings.reconcile

    def start_process(self):
        if self.new_transactions_csv_list:
            self.ingest_new_transactions_csv()
        if self.update_financials:
            self.update_reconcileable_table()
        if self.reconcile:
            self.start_reconcililation()
        
        # cur = self.conn.execute("SELECT * FROM bank_transactions;") # TODO: Used for Dev purposes; Remove or uncommentif in prod
        # print(cur.fetchall()) # TODO: Used for Dev purposes; Remove or uncommentif in prod
        # df = pd.read_sql_query("SELECT * FROM bank_transactions", self.conn) # TODO: Used for Dev purposes; Remove or uncommentif in prod
        # print(df) # TODO: Used for Dev purposes; Remove or uncommentif in prod
        # df.to_csv("transactions.csv", sep=',') # TODO: Used for Dev purposes; Remove or uncommentif in prod


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
            self.conn.execute(insert_into_bank_transactions_table, values)
        self.conn.commit()
        print(f"[+] {len(df.index)} new transactions added:")
        print(df["Transaction ID"])
    
    def update_reconcileable_table(self):
        self.deactivate_current_active_records()
        incoming_reconcilables_df = self.create_incoming_reconcilable_df()

        # Create new DF containing only new reconcilables
        cursor = self.conn.execute(select_reconcilable_id_from_reconcilables_tabe).fetchall()
        reconcilable_ids_from_db = [record[0] for record in cursor]
        new_reconcilables_df = \
            incoming_reconcilables_df[~incoming_reconcilables_df["Reconcilable ID"].isin(\
                reconcilable_ids_from_db)]        
        self.insert_df_into_reconcilables_table(new_reconcilables_df)
        self.activate_incoming_reconcilables_records(incoming_reconcilables_df)
    
    def deactivate_current_active_records(self):
        self.conn.execute(deactivate_active_records_in_reconcilables_table)
        self.conn.commit()

    def create_incoming_reconcilable_df(self):
        csv_file = pathlib.Path(__file__).parent.parent.joinpath("config").joinpath("reconcileables.csv")
        converters = {"Extra Condition": str}
        incoming_reconcilables_df = \
            pd.read_csv(csv_file, delimiter=",", header=0, converters=converters)
        reconcilable_ids = []
        for _, row in incoming_reconcilables_df.iterrows():
            name = row["Name"]
            pattern = row["Bank Transaction Description Pattern"]
            extra_description = row["Extra Condition"]
            recurrence = row["Recurrence"]
            amount = str(row["Amount"])
            type_ = row["Type"]
            sub_type = row["Sub Type"]
            upcoming_date = row["Upcoming Date"]
            hashable = "".join([name, pattern, extra_description, recurrence, amount, 
                                type_, sub_type, upcoming_date])
            reconcilable_id = hashlib.sha256(hashable.encode()).hexdigest()
            reconcilable_ids.append(reconcilable_id)
        incoming_reconcilables_df.insert(0, "Reconcilable ID", reconcilable_ids, True)
        return incoming_reconcilables_df

    def insert_df_into_reconcilables_table(self, df):
        df = df.reset_index()
        for _, row in df.iterrows():
            reconcilable_id = row["Reconcilable ID"]
            name = row["Name"]
            pattern = row["Bank Transaction Description Pattern"]
            extra_description = row["Extra Condition"]
            recurrence = row["Recurrence"]
            amount = row["Amount"]
            type_ = row["Type"]
            sub_type = row["Sub Type"]
            upcoming_date = row["Upcoming Date"]
            formatted_upcoming_date = format_date(upcoming_date, "%m/%d/%Y", "%Y-%m-%d")
            active = 'N'
            values = (reconcilable_id, name, pattern, extra_description, recurrence, amount,\
                       type_, sub_type, formatted_upcoming_date, active)
            self.conn.execute(insert_into_reconcilables_table, values)
        self.conn.commit()
        print(f"[+] {len(df.index)} new reconcilables added:")
        print(df["Reconcilable ID"])
    
    def activate_incoming_reconcilables_records(self, df):
        reconcilable_ids = str(tuple([id_ for id_ in df["Reconcilable ID"]]))
        self.conn.execute(\
            activate_records_in_reconcilables_table.format(reconcilable_ids))
        self.conn.commit()

    def start_reconcililation(self):
        reconcilables = self.create_reconcilables_list()
        for reconcilable in reconcilables:
            self.reconcile_item(reconcilable)
    
    def create_reconcilables_list(self):
        cursor = self.conn.execute(select_active_reconcilables)
        return [{"Name": record[0], "Bank Transaction Description Pattern": record[1],
                 "Extra Condition": record[2], "Amount": record[3], "Upcoming Date": record[4],
                 "Recurrence": record[5], "Reconcilable ID": record[6], "Type": record[7], 
                 "Sub Type": record[8], "Upcoming Date": record[9]} 
            for record in cursor.fetchall()]

    def reconcile_item(self, reconcilable):
        related_bank_transactions = self.find_related_bank_transactions(reconcilable)
        self.archive_related_bank_transactions(reconcilable, related_bank_transactions)
        self.update_reconcileables_table(reconcilable, related_bank_transactions)
        self.update_bank_transactions_table(related_bank_transactions)

    def find_related_bank_transactions(self, reconcilable):
        extra_conditions = reconcilable["Extra Condition"]
        has_extra_conditions = extra_conditions.strip() != ""
        month_start = get_month_start_from_date(reconcilable["Upcoming Date"], "%Y-%m-%d")
        regex_pattern = rf"{reconcilable['Bank Transaction Description Pattern']}"
        df = pd.read_sql_query(\
            select_transactions_from_month_to_date.format(month_start), self.conn)
        related_bank_transactions = df[df["Description"].str.match(regex_pattern)]
        if has_extra_conditions:
            related_bank_transactions = self.create_df_with_single_row_if_meets_conditions(related_bank_transactions, extra_conditions)
        return related_bank_transactions

    def create_df_with_single_row_if_meets_conditions(self, df, extra_conditions):
        meets_conditions = getattr(interface_funcs, extra_conditions)
        for _, row in df.iterrows():
            transaction_id = row["Transaction_ID"]
            amount = row["Amount"]
            posting_date = row["Posting_Date"]
            if meets_conditions(amount, posting_date):
                return df[df["Transaction_ID"].str.match(transaction_id)]
        return df.iloc[0:0]

    def archive_related_bank_transactions(self, reconcilable, related_bank_transactions):
        for _, row in related_bank_transactions.iterrows():
            reconcilable_id = reconcilable["Reconcilable ID"]
            name = reconcilable["Name"]
            bank_transaction_description_pattern = \
                reconcilable["Bank Transaction Description Pattern"]
            extra_condition = reconcilable["Extra Condition"]
            recurrence = reconcilable["Recurrence"]
            amount = reconcilable["Amount"]
            type_ = reconcilable["Type"]
            sub_type = reconcilable["Sub Type"]
            upcoming_date = reconcilable["Upcoming Date"]
            bank_transactions_transaction_id = row[2]
            values = (reconcilable_id, name, bank_transaction_description_pattern, 
                      extra_condition, recurrence, amount, type_, sub_type, 
                      upcoming_date, bank_transactions_transaction_id)
            # self.conn.execute(insert_into_archive_table, values)
            # self.conn.commit()

    def update_reconcileables_table(self, reconcilable, related_bank_transactions):
        reconcilable_id = reconcilable["Reconcilable ID"]
        last_posted_date = related_bank_transactions["Posting_Date"].max()
        new_upcoming_date = reconcilable["Upcoming Date"]
        if isinstance(last_posted_date, str):
            new_upcoming_date = calculate_new_upcoming_date(last_posted_date, reconcilable["Recurrence"])
        print(f'{reconcilable["Name"]} || last posted: {last_posted_date} || expected Date: {reconcilable["Upcoming Date"]} || recurrence: {reconcilable["Recurrence"]} || new Date: {new_upcoming_date}')
        # self.conn.execute(update_reconcilable_date.format(new_upcoming_date, reconcilable_id))
        # self.conn.commit()
    
    def update_bank_transactions_table(self, related_bank_transactions):
        for _, row in related_bank_transactions.iterrows():
            transaction_id = f"{row[2]}"
            # self.conn.execute(update_reconciled_flag_in_bank_transactions_tables.format(transaction_id))
            # self.conn.commit()