import hashlib
import argparse
from datetime import datetime
from distutils.util import strtobool

import pandas

from src.interface_funcs import ConfigSectionIncompleteError
from .user_settings import ImportParserUserSettings

select_transaction_ids_from_bank_activity_table = "SELECT transaction_id FROM bank_activity;"
select_all_from_bank_activity_table = "SELECT * FROM bank_activity;"
insert_into_bank_activity_table = """INSERT INTO bank_activity (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

def format_date(date_str: str, raw_format: str, new_format: str) -> str:
    """
    Format a date string from one format to another.

    Args:
        date_str (str): The date string to be formatted.
        raw_format (str): The format of the input date string.
        new_format (str): The desired format of the output date string.

    Returns:
        str: The formatted date string.
    """
    # Convert the date string to a datetime object using the raw format
    date_obj = datetime.strptime(date_str, raw_format)
    
    # Format the datetime object using the new format and return the result
    return date_obj.strftime(new_format)

def format_amount(amount) -> float:
    """
    Formats an amount string, int, or float value.

    Args:
        amount (str int, or float): The amount to be formatted.

    Returns:
        float: The formatted amount.
    """
    if type(amount) == str:
        # Remove any dollar sign from the amount string
        amount = amount.replace("$", "")
        
        # If the amount is in parentheses, it represents a negative value
        if amount[0] == "(" and amount[-1] == ")":
            # Convert the negative amount string to a float by removing parentheses and appending a negative sign
            amount = "-" + amount[1:-1]
        
    # Convert to a float and return it
    return float(amount)
    

def print_bank_activity_dataframe(df:pandas.DataFrame) -> None:
    """
    Prints the number of transactions and displays details such as posting 
    date, amount, description, and account alias in a formatted table.

    Args:
        df (pandas.DataFrame): DataFrame containing transaction data.

    Returns:
        None
    """
    new_transactions_count = len(df.index)
    if new_transactions_count:
        print(f"{len(df.index)} transaction(s):")
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
            amount = format_amount(row["Amount"])
            amount = "{: >15}".format(amount)
            description = row["Description"]
            description = "{: <38}".format(description[:40])
            account_alias = row["Account Alias"]
            account_alias = "{: <14}".format(account_alias)
            print(f"| {posting_date}|{amount}| {description} | {account_alias}|")
        print(f"+{small_column}+{small_column}+{large_column}+{small_column}+")
    else:
        print("No transactions")

class ImportParserController:
    """
    Controller class for managing transaction data processing.

    This class orchestrates the processing of transaction data from CSV files.
    It interacts with the ImportParserUserSettings, DataBaseInterface, and CSVHandler classes to perform various tasks.

    Args:
        args (argparse.Namespace): Namespace object containing command-line arguments.

    Attributes:
        _user_settings (ImportParserUserSettings): Instance of ImportParserUserSettings class containing user settings and configurations.
        csv_file (list): List of CSV file paths to be processed.
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
        self._user_settings = ImportParserUserSettings(args)
        self.csv_file = self._user_settings.csv_file
        self._db_interface = DataBaseInterface(self._user_settings)
        self._existing_transaction_ids = self._db_interface.get_existing_transaction_ids()
        self._csv_handler = CSVHandler(self._user_settings, self._existing_transaction_ids)

    def start_process(self) -> None:
        """
        Start the transaction data processing workflow.

        This method performs the following steps on the CSV file passed:
        - Extracts new settled transactions DataFrame from the CSV file using the CSVHandler.
        - Inserts the DataFrame into the bank activity table using the DataBaseInterface.
        - Prints a summary of the new transactions.

        Returns:
            None
        """
        new_transactions_df = self._csv_handler.get_new_settled_transactions_df(self.csv_file)
        self._db_interface.insert_df_into_bank_activity_table(new_transactions_df)
        print_bank_activity_dataframe(new_transactions_df)


class DataBaseInterface:
    """
    Class to interface with the database.

    Attributes:
        _user_settings (ImportParserUserSettings): User settings object.
        _conn: Connection to the database.
        _commit (bool): Flag indicating whether changes should be committed to the database.

    Methods:
        get_existing_transaction_ids() -> list: Retrieve existing transaction IDs from the database.
        insert_df_into_bank_activity_table(df: pandas.DataFrame) -> None: Insert DataFrame into the bank activity table.
    """
    def __init__(self, user_settings: ImportParserUserSettings) -> None:
        """
        Initialize DataBaseInterface with user settings.

        Args:
            user_settings (ImportParserUserSettings): User settings object.
        """
        self._user_settings = user_settings
        self._conn = self._user_settings.conn
        self._commit = self._user_settings.commit

    def get_existing_transaction_ids(self) -> list:
        """
        Retrieve existing transaction IDs from the database.

        Returns:
            list: List of existing transaction IDs.
        """
        records = self._conn.execute(select_transaction_ids_from_bank_activity_table).fetchall()
        return [record[0] for record in records]

    def insert_df_into_bank_activity_table(self, df:pandas.DataFrame) -> None:
        """
        Insert DataFrame into the bank activity table.

        Args:
            df (pandas.DataFrame): DataFrame containing transaction data.

        Returns:
            None
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
            amount = format_amount(row["Amount"])
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
                self._conn.execute(insert_into_bank_activity_table, values)

        # Commit changes to the database if required
        if self._commit:
            self._conn.commit()


class CSVHandler:
    """
    Class to handle CSV file operations.

    Attributes:
        _user_settings (ImportParserUserSettings): User settings object.
        _csv_file (list): List of CSV files.
        _config (dict): Configuration settings.
        _account_alias (str): Account alias.
        _chase_column_config_name_map (dict): Mapping of column names between Chase format and original format.
        _chase_column_names (list): List of column names in Chase format.
        existing_transaction_ids (list): List of existing transaction IDs.

    Methods:
        _get_chase_column_config_name_map(): Get mapping of column names between Chase format and original format.
        _get_chase_column_names(): Get list of column names in Chase format.
        get_new_settled_transactions_df(csv_file: str) -> pandas.DataFrame: Get DataFrame of new settled transactions from CSV file.
        _create_dataframe_from_foreign_csv(csv_file: str): Create DataFrame from a foreign CSV file.
        _get_converters(csv_file: str): Get converters for reading CSV file.
        _convert_dataframe_to_chase_format(df: pandas.DataFrame): Convert DataFrame to Chase format.
        _create_dataframe_from_chase_csv(csv_file: str): Create DataFrame from a Chase CSV file.
        _add_required_columns_to_df(df: pandas.DataFrame) -> pandas.DataFrame: Add required columns to DataFrame.
    """
    def __init__(self, user_settings:ImportParserUserSettings, existing_transaction_ids:list) -> None:
        """
        Initialize CSVHandler with user settings and existing transaction IDs.

        Args:
            user_settings (ImportParserUserSettings): User settings object.
            existing_transaction_ids (list): List of existing transaction IDs.
        """
        self._user_settings = user_settings
        self._csv_file = self._user_settings.csv_file
        self._import_config = self._user_settings.import_config
        self._account_alias = self._user_settings.account_alias
        self._chase_column_config_name_map = self._get_chase_column_config_name_map()
        self._chase_column_names = self._get_chase_column_names()
        self.existing_transaction_ids = existing_transaction_ids

    def _get_chase_column_config_name_map(self) -> dict:
        """
        Get mapping of column names between Chase format and original format.

        Returns:
            dict: Mapping of column names.
        """
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
        """
        Get list of column names in Chase format.

        Returns:
            list: List of column names.
        """
        return [self._chase_column_config_name_map[k]
                for k in self._chase_column_config_name_map.keys()]

    def get_new_settled_transactions_df(self, csv_file:str) -> pandas.DataFrame:
        """
        Get DataFrame of new settled transactions from CSV file.

        Args:
            csv_file (str): Path to CSV file.

        Returns:
            pandas.DataFrame: DataFrame of new settled transactions.
        """
        # Determine if a config was provided
        if self._import_config:
            # Create DataFrame from a foreign CSV file
            csv_trans_df = self._create_dataframe_from_foreign_csv(csv_file)
        else:
            # Create DataFrame from a Chase CSV file
            csv_trans_df = self._create_dataframe_from_chase_csv(csv_file)

        # Filter out rows with empty balance
        csv_trans_df = csv_trans_df[csv_trans_df['Balance'] != ' ']

        # Exclude transactions already present in the bank activity table
        return csv_trans_df[~csv_trans_df["Transaction ID"].isin(self.existing_transaction_ids)]

    def _create_dataframe_from_foreign_csv(self, csv_file:str) -> pandas.DataFrame:
        """
        Create DataFrame from a foreign CSV file.

        Args:
            csv_file (str): Path to CSV file.

        Returns:
            pandas.DataFrame: DataFrame created from the CSV file.
        """
        try:
            # Extract whether the CSV file has a header from configuration
            config_value = self._import_config["HEADER"].get("has_header")
            csv_has_header_row = strtobool(config_value.strip())
        except (KeyError, AttributeError, ValueError) as e:
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

    def _get_converters(self, csv_file:str) -> dict:
        """
        Get converters for reading CSV file.

        Args:
            csv_file (str): Path to CSV file.

        Returns:
            dict: Dictionary of converters.
        """
        # Read the CSV file to a temporary DataFrame to determine the number of columns
        temp_df = pandas.read_csv(csv_file, delimiter=",", header=None, skiprows=[0])

        # Convert all columns to string datatype
        return {i: str for i in range(temp_df.shape[1])}

    def _convert_dataframe_to_chase_format(self, df:pandas.DataFrame) -> pandas.DataFrame:
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
            # Loop through the expected keys in the GENERAL section of the configuration
            for key in self._chase_column_config_name_map.keys():
                # Get the value associated with the key and strip any leading or trailing whitespace
                value = self._import_config["GENERAL"][key].strip()
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

    def _create_dataframe_from_chase_csv(self, csv_file:str) -> pandas.DataFrame:
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

        The "Transaction ID" is the row's unique identifier. It is a calculated hash of the values of other columns:
            Details
            Postind Date
            Descsription
            Amount
            Type
            Balance
            Check or Slip Num
            Account Alias

        Args:
            df (pandas.DataFrame): DataFrame to be processed.

        Returns:
            pandas.DataFrame: Processed DataFrame with newly added columns: "Transaction ID" and "Account Alias".
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