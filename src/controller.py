import hashlib
import argparse
import pandas
from datetime import datetime
from distutils.util import strtobool

from src.interface_funcs import ConfigSectionIncompleteError
from .user_settings import UserSettings

select_transaction_ids_from_transactions_table = "SELECT transaction_id FROM bank_transactions;"
select_all_from_transactions_table = "SELECT * FROM bank_transactions;"
insert_into_bank_transactions_table = """INSERT INTO bank_transactions (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

def format_date(date_str, raw_format:str, new_format:str) -> str:
    date_obj = datetime.strptime(date_str, raw_format)
    return date_obj.strftime(new_format)


class Controller:
    """
    Controller class for managing transaction data processing.

    This class orchestrates the processing of transaction data from CSV files.
    It interacts with the UserSettings, DataBaseInterface, and CSVHandler classes to perform various tasks.

    Args:
        args (argparse.Namespace): Namespace object containing command-line arguments.

    Attributes:
        _user_settings (UserSettings): Instance of UserSettings class containing user settings and configurations.
        csv_files (list): List of CSV file paths to be processed.
        _db_interface (DataBaseInterface): Instance of DataBaseInterface class for database interaction.
        _existing_transaction_ids (list): List of existing transaction IDs in the database.
        _csv_handler (CSVHandler): Instance of CSVHandler class for CSV file handling and data extraction.

    Methods:
        __init__(self, args:argparse.Namespace): Initializes the Controller instance.
        start_process(self) -> None: Initiates the transaction data processing workflow.
    """

    def __init__(self, args:argparse.Namespace) -> None:
        """
        Initialize Controller instance.

        Args:
            args (argparse.Namespace): Namespace object containing command-line arguments.
        """
        self._user_settings = UserSettings(args)
        self.csv_files = self._user_settings.csv_files
        self._db_interface = DataBaseInterface(self._user_settings)
        self._existing_transaction_ids = self._db_interface.get_existing_transaction_ids()
        self._csv_handler = CSVHandler(self._user_settings, self._existing_transaction_ids)

    def start_process(self) -> None:
        """
        Start the transaction data processing workflow.

        This method iterates over each CSV file in the list of CSV files and performs the following steps:
        - Extracts new settled transactions DataFrame from the CSV file using the CSVHandler.
        - Inserts the DataFrame into the bank transactions table using the DataBaseInterface.
        - Prints a summary of the new transactions.

        Returns:
            None
        """
        for csv_file in self.csv_files:
            new_transactions_df = self._csv_handler.get_new_settled_transactions_df(csv_file)
            self._db_interface.insert_df_into_bank_transactions_table(new_transactions_df)
            Controller.print_summary(new_transactions_df)

    @staticmethod
    def print_summary(df:pandas.DataFrame) -> None:
        """
        Prints a summary of transactions to be added based on the provided DataFrame.
        It prints the number of new transactions and displays details such as posting 
        date, amount, description, and account alias in a formatted table.

        Args:
            df (pandas.DataFrame): DataFrame containing transaction data.

        Returns:
            None
        """
        new_transactions_count = len(df.index)
        if new_transactions_count:
            print(f"{len(df.index)} new transaction(s):")
            posting_date_header = "{: ^15}".format("POSTING DATE")
            amount_header = "{: ^15}".format("AMOUNT")
            description_header = "{: ^42}".format("DESCRIPTION")
            account_alias_header = "{: ^15}".format("ACOUNT ALIAS")
            small_column = "{:-^15}".format("")
            large_column = "{:-^42}".format("")
            print(f"+{small_column}+{small_column}+{large_column}+{small_column}+")
            print(f"|{posting_date_header}|{amount_header}|{description_header}|{account_alias_header}|")
            print(f"+{small_column}+{small_column}+{large_column}+{small_column}+")
            for _, row in df.iterrows():
                posting_date = row["Posting Date"]
                posting_date = "{: <14}".format(posting_date)
                amount = str(row["Amount"])
                amount = "{: >15}".format(amount)
                description = row["Description"]
                description = "{: <38}".format(description[:40])
                account_alias = row["Account Alias"]
                account_alias = "{: <14}".format(account_alias)
                print(f"| {posting_date}|{amount}| {description} | {account_alias}|")
            print(f"+{small_column}+{small_column}+{large_column}+{small_column}+")
        else:
            print("No new transactions")


class DataBaseInterface:
    def __init__(self, user_settings: UserSettings) -> None:
        self._user_settings = user_settings
        self._conn = self._user_settings.conn
        self._commit = self._user_settings.commit

    def get_existing_transaction_ids(self) -> list:
        records = self._conn.execute(select_transaction_ids_from_transactions_table).fetchall()
        return [record[0] for record in records]

    def insert_df_into_bank_transactions_table(self, df:pandas.DataFrame) -> None:
        """
        Insert DataFrame into the bank transactions table.

        Args:
            df (pandas.DataFrame): DataFrame containing transaction data.

        This method iterates over each row in the DataFrame, retrieves 
        transaction information, formats the data, and inserts it into 
        the bank transactions table. If `commit` is set to True, changes 
        are committed to the database.
        """
        # Reset index of the DataFrame
        df = df.reset_index()

        # Iterate over each row in the DataFrame
        for _, row in df.iterrows():
            # Extract transaction details from the row
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

            # Reconciled is used for tracking purposes. 
            # 'N' means you have NOT confirmed this transaction against your expected credits and purchases. 
            # 'Y' means you have confirmed this credit/purchase against your expected credits and purchases.
            # Ideally, all your transactions should be 'Y' at the end of your personal finance analysis.
            # Setting it to 'N' by default allows you the opportunity to analyze your historical spending and income.
            # Currently, this program does not have a way to convert this flag to 'Y'.
            # You'll have to manually change the flag in the database.
            reconciled = 'N'

            # Create a tuple of values to be inserted into the database
            values = (account_alias, transaction_id, details, formatted_posting_date,
                    description, amount, type_, balance, check_or_slip_num, reconciled)

            # Execute SQL query to insert values into the database
            if self._commit:
                self._conn.execute(insert_into_bank_transactions_table, values)

        # Print a summary transactions to be added
        self._print_summary(df)

        # Commit changes to the database if required
        if self._commit:
            self._conn.commit()


class CSVHandler:
    def __init__(self, user_settings:UserSettings, existing_transaction_ids:list) -> None:
        self._user_settings = user_settings
        self._new_csv_files = self._user_settings.new_csv_files
        self._config = self._user_settings.config
        self._account_alias = self._user_settings.account_alias
        self._chase_column_config_name_map = self._get_chase_column_config_name_map()
        self._chase_column_names = self._get_chase_column_names()
        self.existing_transaction_ids = existing_transaction_ids

    def _get_chase_column_config_name_map(self) -> dict:
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

    def _get_chase_column_names(self) -> list:
        return [self._chase_column_config_name_map[k]
                for k in self._chase_column_config_name_map.keys()]

    def get_new_settled_transactions_df(self, csv_file:str) -> pandas.DataFrame:
        # Determine if a config was provided
        if self._config:
            # Create DataFrame from a foreign CSV file
            csv_trans_df = self._create_dataframe_from_foreign_csv(csv_file)
        else:
            # Create DataFrame from a Chase CSV file
            csv_trans_df = self._create_dataframe_from_chase_csv(csv_file)

        # Filter out rows with empty balance
        csv_trans_df = csv_trans_df[csv_trans_df['Balance'] != ' ']

        # Exclude transactions already present in the bank transactions table
        return csv_trans_df[~csv_trans_df["Transaction ID"].isin(self.existing_transaction_ids)]

    def _create_dataframe_from_foreign_csv(self, csv_file:str):
        """
        Create DataFrame from a foreign CSV file.

        Args:
            csv_file (str): Path to CSV file.
            account_alias (str): Account alias.

        Returns:
            pandas.DataFrame: DataFrame created from the CSV file.
        """
        try:
            # Extract whether the CSV file has a header from configuration
            config_value = self._config["HEADER"].get("has_header")
            csv_has_header_row = strtobool(config_value.strip())
        except AttributeError as e:
            # Handle missing or incorrect configuration for the has_
            message = (f"{e}.\nTroubleshooting help: Ensure the has_ section contains the proper definitions"
                    f" in the config file. Refer to the configs provided in src/test_files/ for help.")
            raise ConfigSectionIncompleteError(message)
        
        converters = self._get_converters(csv_file)
        
        # Read the CSV file to DataFrame, considering header existence
        if csv_has_header_row:
            df = pandas.read_csv(csv_file, delimiter=",", header=None, converters=converters, skiprows=[0])
        else:
            df = pandas.read_csv(csv_file, delimiter=",", header=None, converters=converters)
        
        # Convert DataFrame to Chase format
        df = self._convert_dataframe_to_chase_format(df)
        
        # Create ingestible DataFrame
        return self._add_required_columns_to_df(df)
    
    def _get_converters(self, csv_file:str):
        """
        This method reads the CSV file into a temporary DataFrame 
        to determine the number of columns. It then creates a dictionary 
        of converters, where each column index is mapped to a 
        conversion type of str.

        Args:
            csv_file (str): Path to the CSV file.

        Returns:
            dict: A dictionary mapping column indices to str.
        """
        # Read the CSV file to a temporary DataFrame to determine the number of columns
        temp_df = pandas.read_csv(csv_file, delimiter=",", header=None, skiprows=[0])

        # Convert all columns to string datatype
        return {i: str for i in range(temp_df.shape[1])}

    def _convert_dataframe_to_chase_format(self, df:pandas.DataFrame):
        """
        Convert DataFrame to Chase format.

        Args:
            df (pandas.DataFrame): DataFrame to be converted.

        Returns:
            pandas.DataFrame: DataFrame converted to Chase format.
        """
        # Calculate the number of rows in the DataFrame
        count_row = df.shape[0]

        # Create a list of empty strings with the same length as the DataFrame
        empty_values = ["" for _ in range(count_row)]

        # Insert empty columns with Chase column names to the DataFrame
        for name in self._chase_column_names:
            df.insert(df.shape[1], name, empty_values, True)

        try:
            # Loop through the keys in the GENERAL section of the configuration
            for key in self._config["GENERAL"]:
                # Get the value associated with the key and strip any leading or trailing whitespace
                value = self._config["GENERAL"][key].strip()
                # Check if the value is not empty
                if value:
                    # Convert the value to an integer, representing the index of the original DataFrame
                    index = int(value)
                    # Map the column in the Chase format to the corresponding column in the original DataFrame
                    df[self._chase_column_config_name_map[key]] = df[index]

        except (ValueError, KeyError) as e:
            # Handle missing or incorrect configuration for the GENERAL section
            message = (f"{e}.\nTroubleshooting help: Ensure the GENERAL section contains the proper definitions"
                    f" in the config file. Refer to the configs provided in src/test_files/ for help.")
            raise ConfigSectionIncompleteError(message)

        # Retain only the columns in the DataFrame that match Chase column names
        df = df.loc[:, df.columns.intersection(self._chase_column_names)]
        return df

    def _create_dataframe_from_chase_csv(self, csv_file:str):
        """
        Create DataFrame from a Chase CSV file.

        Args:
            csv_file (str): Path to CSV file.

        Returns:
            pandas.DataFrame: DataFrame created from the CSV file.
        """
        # Specify converters to handle datatype conversions
        converters = {"Balance": str}

        # Read CSV file into DataFrame, skipping the first row (header) and specifying column names
        df = pandas.read_csv(csv_file, delimiter=",", skiprows=[0], header=None, names=self._chase_column_names, \
                        converters=converters)

        # Add required columns to DataFrame
        return self._add_required_columns_to_df(df)

    def _add_required_columns_to_df(self, df:pandas.DataFrame) -> pandas.DataFrame:
        """
        Adds columns "Transaction ID" and "Account Alias" to DataFrame.

        Transaction ID is a calculated hash from concatenating the columns:
            Details
            Posting Date
            Description
            Amount
            Type
            Balance
            Check or Slip #
            Account Alias

        Args:
            df (pandas.DataFrame): DataFrame to be processed.
            account_alias (str): Account alias.

        Returns:
            pandas.DataFrame: Processed DataFrame with newly added columns: "Transaction ID" and "Account Alias"
        """
        # Initialize lists to store transaction IDs and account aliases
        transaction_ids = []
        account_aliases = []

        # Iterate over each row in the DataFrame
        for _, row in df.iterrows():
            # Extract relevant columns for generating transaction ID
            details = row["Details"]
            posting_date = row["Posting Date"]
            description = row["Description"]
            amount = str(row["Amount"])
            type_ = row["Type"]
            balance = row["Balance"]
            check_or_slip_num = str(row["Check or Slip #"])

            # Concatenate columns to create a hashable string
            hashable = "".join([details, posting_date, description, amount, type_, balance, \
                                check_or_slip_num, self._account_alias])


            # Generate transaction ID using SHA-256 hash function
            transaction_id = hashlib.sha256(hashable.encode()).hexdigest()

            # Append transaction ID and account alias to respective lists
            transaction_ids.append(transaction_id)
            account_aliases.append(self._account_alias)

        # Insert transaction ID and account alias columns into DataFrame
        df.insert(0, "Transaction ID", transaction_ids, True)
        df.insert(1, "Account Alias", account_aliases, True)
        return df