import hashlib
import argparse
from datetime import datetime
from distutils.util import strtobool

import pandas

from src.interface_funcs import DuplicateAliasError, BadQueryStructureError, UnknownAliasError
from .user_settings import UserSettings, ImportParserUserSettings, GetQueryUserSettings

# SQL queries
select_transaction_ids_from_bank_activity_table = "SELECT transaction_id FROM bank_activity;"
select_all_from_bank_activity_table = "SELECT * FROM bank_activity;"
insert_into_bank_activity_table = """INSERT INTO bank_activity (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

def format_date(date_str: str, raw_format: str, new_format: str) -> str:
    """
    Format date string from one format to another.

    Args:
        date_str (str): Input date string.
        raw_format (str): Format of the input date string.
        new_format (str): Desired format of the output date string.

    Returns:
        str: Formatted date string in the new format.
    """
    date_obj = datetime.strptime(date_str, raw_format)
    return date_obj.strftime(new_format)

def format_amount(amount) -> float:
    """
    Convert amount to a float value.

    Args:
        amount: Input amount (either str, int, or float).

    Returns:
        float: Converted amount value.
    """
    if isinstance(amount, str):
        amount = amount.replace("$", "")
        if amount[0] == "(" and amount[-1] == ")":
            amount = "-" + amount[1:-1]
    return float(amount)

def print_bank_activity_dataframe(df: pandas.DataFrame) -> None:
    """
    Print formatted bank activity DataFrame.

    Args:
        df (pandas.DataFrame): DataFrame containing bank activity data.
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

class Controller:
    """
    Base class for controllers.
    """
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize Controller with user settings.

        Args:
            cli_args (argparse.Namespace): Command-line arguments.
        """
        self._user_settings = UserSettings(cli_args)
        self._db_interface = DataBaseInterface(self._user_settings)

    def start_process(self) -> None:
        """
        Placeholder method for starting a process.

        This method should be overridden by subclasses.
        """
        raise NotImplementedError

class ImportParserController(Controller):
    """
    Controller for import operations.
    """
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize ImportParserController with user settings.

        Args:
            cli_args (argparse.Namespace): Command-line arguments.
        """
        super().__init__(cli_args)
        self._user_settings = ImportParserUserSettings(cli_args)

    def start_process(self) -> None:
        """
        Start the import process.

        This method retrieves new transactions from a CSV file and inserts them into the bank activity table.
        """
        csv_file = self._user_settings.csv_file
        existing_transaction_ids = self._db_interface.get_existing_transaction_ids()
        csv_handler = CSVHandler(self._user_settings, existing_transaction_ids)
        new_transactions_df = csv_handler.get_new_settled_transactions_df(csv_file)
        self._db_interface.insert_df_into_bank_activity_table(new_transactions_df)
        print_bank_activity_dataframe(new_transactions_df)

class GetQueryParserController(Controller):
    """
    Controller for query operations.
    """
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize GetQueryParserController with user settings.

        Args:
            cli_args (argparse.Namespace): Command-line arguments.
        """
        super().__init__(cli_args)
        self._user_settings = GetQueryUserSettings(cli_args)
        self.queries_config = self._user_settings.queries_config
        self.call_query_map = self._create_query_alias_map()
        self.queries = self._get_queries()

    def start_process(self) -> None:
        """
        Start the query process.

        This method executes predefined queries based on user input.
        """
        try:
            max_rows_to_display = self._get_max_rows_to_display()
        except ValueError as ve:
            raise ValueError(f"{ve} is not an acceptable value in [GENERAL] max_rows_to_display")

        pandas.set_option('display.max_rows', max_rows_to_display)
        self._execute_queries(max_rows_to_display)

    def _get_max_rows_to_display(self) -> int:
        """
        Retrieve the maximum number of rows to display from configuration.

        Returns:
            int: Maximum number of rows to display.
        """
        max_rows_to_display = self.queries_config.get("GENERAL", "max_rows_to_display", fallback=None)
        return int(max_rows_to_display)

    def _execute_queries(self, max_rows_to_display: int) -> None:
        """
        Execute and display the results of predefined queries.

        Args:
            max_rows_to_display (int): Maximum number of rows to display.
        """
        for query_call, query in self.queries:
            df = pandas.DataFrame(self._db_interface.execute_query(query))
            self._display_query_results(query_call, df, max_rows_to_display)
            if self._user_settings.save_results:
                self._save_query_results(query_call, df, max_rows_to_display)

    def _display_query_results(self, query_call: str, df: pandas.DataFrame, max_rows_to_display: int) -> None:
        """
        Display the results of a query with formatting.

        Args:
            query_call (str): Query alias.
            df (pandas.DataFrame): DataFrame containing query results.
            max_rows_to_display (int): Maximum number of rows to display.
        """
        print(f'\n"{query_call}" results:')
        for row_idx, row in df.head(max_rows_to_display).iterrows():
            # Display border
            if row_idx == 0:
                table_border = self._create_border(row)
                print(table_border)

            # Display row
            self._display_row(row)

            # Display boder
            if row_idx == max_rows_to_display-1:
                print(table_border)

    def _create_border(self, row: pandas.Series) -> str:
        """
        Create a formatted border string for a given row of data.

        Args:
            row (pandas.Series): Row of data.

        Returns:
            str: Formatted border string.
        """
        max_length = 30  # Maximum length of each column value in characters
        border_parts = ["-" * len("{: >15} ".format(str(row[col_idx])[:max_length])) for col_idx in range(len(row))]
        border_string = "+" + "+".join(border_parts) + "+"
        return border_string

    def _display_row(self, row: pandas.Series) -> None:
        """
        Display a formatted row of data.

        Args:
            row (pandas.Series): Row of data from the DataFrame.
        """
        formatted_columns = [self._format_value(str(row[col_idx])[:30]) for col_idx in range(len(row))]
        formatted_output = "|" + "|".join(formatted_columns) + "|"
        print(formatted_output)

    def _format_value(self, value: str) -> str:
        """
        Format a value to a fixed length.

        Args:
            value (str): Input value.

        Returns:
            str: Formatted value.
        """
        return "{: >15} ".format(value)

    def _save_query_results(self, query_call: str, df: pandas.DataFrame, max_rows_to_display: int) -> None:
        """
        Save query results to a CSV file.

        Args:
            query_call (str): Query alias.
            df (pandas.DataFrame): DataFrame containing query results.
            max_rows_to_display (int): Maximum number of rows to save.
        """
        csv_file_name = f"{query_call}_results.csv"
        df.head(max_rows_to_display).to_csv(csv_file_name)

    def _get_queries(self) -> list:
        """
        Retrieve and validate user queries.

        Returns:
            list: List of validated queries.
        """
        return [(query_call, self._validate_query(query_call)) for query_call in self._user_settings.query_calls]

    def _validate_query(self, query:str) -> str:
        """
        Validate user query.

        Args:
            query (str): User-provided query.

        Raises:
            UnknownAliasError: If the query alias is unknown.
            BadQueryStructureError: If the query structure is invalid.

        Returns:
            str: Validated query.
        """
        try:
            query = self.call_query_map[query]
            if "UPDATE" in query.upper() or "DELETE" in query.upper() or "DROP" in query.upper():
                raise BadQueryStructureError(f"The query contains illegal words: {query}")
        except KeyError:
            raise UnknownAliasError(f"{query}: alias does not exist")
        return query.strip('"""')

    def _create_query_alias_map(self) -> dict:
        """
        Create a map of query aliases to their corresponding SQL queries.

        Raises:
            KeyError: If an alias is defined to a key that doesn't exist in QUERIES.

        Returns:
            dict: Mapping of query aliases to SQL queries.
        """
        query_alias_map = {}
        for key in self.queries_config["ALIASES"]:
            for value in self.queries_config["ALIASES"][key].strip().split(","):
                alias = value.strip()
                if alias not in query_alias_map.keys():
                    try:
                        query_alias_map[alias] = self.queries_config.get("QUERIES", key, raw=True)
                    except KeyError:
                        raise KeyError(f"Alias defined to a key that doesn't exist in QUERIES in: {self._user_settings.queries_config_path}")
                else:
                    raise DuplicateAliasError(f"{alias}: Alias is used multiple times in [ALIASES]: {self._user_settings.queries_config_path}")
        return query_alias_map

class DataBaseInterface:
    """
    Interface for interacting with the database.
    """
    def __init__(self, user_settings: UserSettings):
        """
        Initialize DataBaseInterface with user settings.

        Args:
            user_settings (UserSettings): User settings instance.
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

    def insert_df_into_bank_activity_table(self, df: pandas.DataFrame) -> None:
        """
        Insert DataFrame into the bank activity table.

        Args:
            df (pandas.DataFrame): DataFrame to be inserted.
        """
        df = df.reset_index()
        for _, row in df.iterrows():
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
            reconciled = 'N'
            values = (account_alias, transaction_id, details, formatted_posting_date,
                      description, amount, type_, balance, check_or_slip_num, reconciled)
            if self._commit:
                self._conn.execute(insert_into_bank_activity_table, values)
        if self._commit:
            self._conn.commit()

    def execute_query(self, query: str, args: list = None):
        """
        Execute SQL query.

        Args:
            query (str): SQL query string.
            args (list, optional): Query arguments.

        Returns:
            list: Query results.
        """
        if args:
            print(query)
            return self._conn.execute(query, args).fetchall()
        return self._conn.execute(query).fetchall()


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