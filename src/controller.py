import argparse
import hashlib
import os
import re
from datetime import datetime

import pandas

from src.interface_funcs import (
    DuplicateAliasError, 
    IllegalStructureError, 
    UnknownAliasError, 
    ConfigSectionIncompleteError
)
from .user_settings import (
    UserSettings, 
    ImportParserUserSettings, 
    MakeImportReadyParserUserSettings, 
    RunQueryParserUserSettings,
    TrendsParserUserSettings
)

# SQL queries
SELECT_TRANSACTION_IDS_FROM_BANK_ACTIVITY_TABLE = \
    "SELECT transaction_id FROM bank_activity;"
INSERT_INTO_BANK_ACTIVITY_TABLE = \
    """INSERT INTO bank_activity (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
INSERT_INTO_PENDING_TRANSACTIONS_TABLE = \
    """INSERT INTO pending_transactions (Account_Alias, Transaction_ID, Details, Posting_Date, Description, Amount, Type, Balance, Check_or_Slip_num, Reconciled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""

# Chase column names to config keys map
CHASE_COLUMN_CONFIG_NAME_MAP = {
        "details" : "Details",
        "posting_date" : "Posting Date",
        "description" : "Description",
        "amount" : "Amount",
        "type" : "Type",
        "balance" : "Balance",
        "check_or_slip_number" : "Check or Slip #",
        "extra_1" : "Extra 1"
    }

CHASE_COLUMN_NAMES = \
    [CHASE_COLUMN_CONFIG_NAME_MAP[k] for k in CHASE_COLUMN_CONFIG_NAME_MAP.keys()]


def strtobool(value: str) -> bool:
  value = value.lower()
  if value in ("y", "yes", "on", "1", "true", "t"):
    return True
  return False


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
        print("No new settled transactions")


def clean_up_config_value(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) \
    or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return value

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
        records = self._conn.execute(SELECT_TRANSACTION_IDS_FROM_BANK_ACTIVITY_TABLE).fetchall()
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
                self._conn.execute(INSERT_INTO_BANK_ACTIVITY_TABLE, values)
        if self._commit:
            self._conn.commit()

    def insert_df_into_pending_transactions_table(self, df: pandas.DataFrame) -> None:
        """
        Insert DataFrame into the bank activity table.

        Args:
            df (pandas.DataFrame): DataFrame to be inserted.
        """
        if self._commit:
            self.delete_all_pending_transactions_table_records()    

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
                self._conn.execute(INSERT_INTO_PENDING_TRANSACTIONS_TABLE, values)
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

    def delete_all_pending_transactions_table_records(self) -> None:
        """
        deletes pending transactions table records.

        Args:
            None

        Returns:
            None
        """
        query = """
            DELETE
            FROM
                pending_transactions;"""
        self._conn.execute(query)


class CSVHandler:
    """
    Class to handle CSV file operations.

    Attributes:
        _user_settings (ImportParserUserSettings): User settings object.
        _csv_file (str): "Import-ready" CSV filepath
        _account_alias (str): Account alias.
        existing_transaction_ids (list): List of existing transaction IDs.

    Methods:
        get_new_settled_transactions_df(csv_file: str) -> pandas.DataFrame: Get DataFrame of new settled transactions from CSV file.
        _create_dataframe_from_foreign_csv(csv_file: str): Create DataFrame from a foreign CSV file.
        _get_converters(csv_file: str): Get converters for reading CSV file.
        _convert_dataframe_to_chase_format(df: pandas.DataFrame): Convert DataFrame to Chase format.
        _create_dataframe_from_import_ready_csv(csv_file: str): Create DataFrame from a Chase CSV file.
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
        self._account_alias = self._user_settings.account_alias
        self.existing_transaction_ids = existing_transaction_ids

    def get_new_settled_transactions_df(self) -> pandas.DataFrame:
        """
        Get DataFrame of new settled transactions from the imported CSV file.

        Args:
            None

        Returns:
            pandas.DataFrame: DataFrame of new settled transactions.
        """
        # Create DataFrame from a Chase CSV file
        csv_trans_df = self._create_dataframe_from_import_ready_csv(self._csv_file)

        # Filter out rows with empty balance
        csv_trans_df = csv_trans_df[csv_trans_df['Balance'] != ' ']

        # Exclude transactions already present in the bank activity table
        return csv_trans_df[~csv_trans_df["Transaction ID"].isin(self.existing_transaction_ids)]

    def get_new_pending_transactions_df(self) -> pandas.DataFrame:
        """
        Get DataFrame of new pending transactions from the imported CSV file.

        Args:
            None

        Returns:
            pandas.DataFrame: DataFrame of new settled transactions.
        """
        # Create DataFrame from a Chase CSV file
        csv_trans_df = self._create_dataframe_from_import_ready_csv(self._csv_file)

        # Return DataFrame with rows that contain empty balance
        return csv_trans_df[csv_trans_df['Balance'] == ' ']

    def _create_dataframe_from_import_ready_csv(self, import_ready_csv_file:str) -> pandas.DataFrame:
        """
        Create DataFrame from an "import-ready" CSV file.

        Args:
            import_ready_csv_file (str): Path to "import-ready" CSV file.

        Returns:
            pandas.DataFrame: DataFrame created from the CSV file.
        """
        # Specify converters to handle datatype conversions
        converters = {"Balance": str}

        # Read CSV file into DataFrame, skipping the first row (header) and specifying column names
        df = pandas.read_csv(import_ready_csv_file, delimiter=",", skiprows=[0], header=None, names=CHASE_COLUMN_NAMES, \
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
            details = str(row["Details"])
            posting_date = str(row["Posting Date"])
            description = str(row["Description"])
            amount = str(row["Amount"])
            type_ = str(row["Type"])
            balance = str(row["Balance"])
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
        existing_transaction_ids = self._db_interface.get_existing_transaction_ids()
        csv_handler = CSVHandler(self._user_settings, existing_transaction_ids)
        new_transactions_df = csv_handler.get_new_settled_transactions_df()
        self._db_interface.insert_df_into_bank_activity_table(new_transactions_df)
        print_bank_activity_dataframe(new_transactions_df)

        pending_transactions_df = csv_handler.get_new_pending_transactions_df()
        self._db_interface.insert_df_into_pending_transactions_table(pending_transactions_df)


class MakeImportReadyParserController(Controller):
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize ImportParserController with user settings.

        Args:
            cli_args (argparse.Namespace): Command-line arguments.
        """
        super().__init__(cli_args)
        self._user_settings = MakeImportReadyParserUserSettings(cli_args)
        self.raw_csv_file = self._user_settings.raw_csv_file
        self.conversion_config = self._user_settings.conversion_config

    def start_process(self) -> None:
        """
        Start the conversion process.
        """
        new_file_path = self._get_new_filepath()
        has_header_config_value = clean_up_config_value(self.conversion_config["HEADER"]["has_header"])
        if strtobool(has_header_config_value):
            raw_df = pandas.read_csv(self.raw_csv_file, header=None, skiprows=[0])
        else:
            raw_df = pandas.read_csv(self.raw_csv_file, header=None)
        converted_df = self._convert_dataframe_to_chase_format(raw_df)
        converted_df.to_csv(new_file_path, index=False)
        print(new_file_path)

    def _get_new_filepath(self):
        """  
        TODO: write docstring  
        """  
        path = os.path.dirname(self.raw_csv_file)
        basename = os.path.basename(self.raw_csv_file)
        filename, ext = os.path.splitext(basename)
        new_filename = filename + "_import_ready" + ext
        return os.path.join(path, new_filename).replace("\\", "/")

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
        for name in CHASE_COLUMN_NAMES:
            df.insert(df.shape[1], name, empty_values, True)

        try:
            # Loop through the expected keys in the GENERAL section of the configuration
            for key in CHASE_COLUMN_CONFIG_NAME_MAP.keys():
                # Get the value associated with the key and strip any leading or trailing whitespace
                value = clean_up_config_value(self.conversion_config["GENERAL"][key])
                # Check if the value is not empty
                if value:
                    # Convert the value to an integer, representing the index of the original DataFrame
                    index = int(value)
                    # Map the column in the Chase format to the corresponding column in the original DataFrame
                    df[CHASE_COLUMN_CONFIG_NAME_MAP[key]] = df[index]

        except (ValueError, KeyError) as e:
            # Handle missing or incorrect configuration for the GENERAL section
            message = (f"{e}.\nTroubleshooting help: Ensure the GENERAL section contains the proper definitions"
                    f" in the config file. Refer to the configs provided in src/test_files/ for help.")
            raise ConfigSectionIncompleteError(message)

        # Retain only the columns in the DataFrame that match Chase column names
        df = df.loc[:, df.columns.intersection(CHASE_COLUMN_NAMES)]
        return df


class RunQueryParserController(Controller):
    """
    Controller for query operations.
    """
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize RunQueryParserController with user settings.

        Args:
            cli_args (argparse.Namespace): Command-line arguments.
        """
        super().__init__(cli_args)
        self._user_settings = RunQueryParserUserSettings(cli_args)
        self.queries_config = self._user_settings.queries_config
        self.call_query_map = self._create_query_alias_map()
        self.queries = self._get_queries()

    def start_process(self) -> None:
        """
        Start the query process.

        This method executes predefined queries based on user input.
        """

        self._execute_queries()

    def _execute_queries(self) -> None:
        """
        Execute and display the results of predefined queries.
        """
        number_or_rows = self._user_settings.rows
        for query_call, query in self.queries:
            df = pandas.DataFrame(self._db_interface.execute_query(clean_up_config_value(query)))
            self._display_query_results(query_call, df, number_or_rows)
            if self._user_settings.save_results:
                self._save_query_results(query_call, df, number_or_rows)

    def _display_query_results(self, query_call: str, df: pandas.DataFrame, number_or_rows: int) -> None:
        """
        Display the results of a query with formatting.

        Args:
            query_call (str): Query alias.
            df (pandas.DataFrame): DataFrame containing query results.
            number_or_rows (int): Maximum number of rows to display.
        """
        data = False
        print(f'\n"{query_call}" results:')
        for row_idx, row in df.head(number_or_rows).iterrows():
            data = True
            # Display border
            if row_idx == 0:
                table_border = self._create_border(row)
                print(table_border)

            # Display row
            self._display_row(row)

        # Display boder
        if data:
            print(table_border)

    def _create_border(self, row: pandas.Series) -> str:
        """
        Create a formatted border string for a given row of data.

        Args:
            row (pandas.Series): Row of data.

        Returns:
            str: Formatted border string.
        """
        max_length = 50  # Maximum length of each column value in characters
        border_parts = ["-" * len("{: >15} ".format(str(row[col_idx])[:max_length])) for col_idx in range(len(row))]
        border_string = "+" + "+".join(border_parts) + "+"
        return border_string

    def _display_row(self, row: pandas.Series) -> None:
        """
        Display a formatted row of data.

        Args:
            row (pandas.Series): Row of data from the DataFrame.
        """
        formatted_columns = [self._format_value(str(row[col_idx])[:50]) for col_idx in range(len(row))]
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

    def _save_query_results(self, query_call: str, df: pandas.DataFrame, number_or_rows: int) -> None:
        """
        Save query results to a CSV file.

        Args:
            query_call (str): Query alias.
            df (pandas.DataFrame): DataFrame containing query results.
            number_or_rows (int): Maximum number of rows to save.
        """
        csv_file_name = f"{query_call}_results.csv"
        df.head(number_or_rows).to_csv(csv_file_name)

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
            IllegalStructureError: If the query structure is invalid.

        Returns:
            str: Validated query.
        """
        try:
            query = self.call_query_map[query]
            if "UPDATE" in query.upper() or "DELETE" in query.upper() or "DROP" in query.upper():
                raise IllegalStructureError(f"The query contains illegal words: {query}")
        except KeyError:
            raise UnknownAliasError(f"{query}: alias does not exist")
        return query

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
            for value in clean_up_config_value(self.queries_config["ALIASES"][key]).split(","):
                alias = clean_up_config_value(value)
                if alias not in query_alias_map.keys():
                    try:
                        query_alias_map[alias] = self.queries_config.get("QUERIES", key, raw=True)
                    except KeyError:
                        raise KeyError(f"Alias defined to a key that doesn't exist in QUERIES in: {self._user_settings.queries_config_path}")
                else:
                    raise DuplicateAliasError(f"{alias}: Alias is used multiple times in [ALIASES]: {self._user_settings.queries_config_path}")
        return query_alias_map

class TrendsParserController(Controller):
    """
    Controller for query operations.
    """
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize TrendsParserController with user settings.

        Args:
            cli_args (argparse.Namespace): Command-line arguments.
        """
        super().__init__(cli_args)
        self._user_settings = TrendsParserUserSettings(cli_args)
        self._trends_config = self._user_settings.trends_config
        
    def extract_purchase_date(self, description, posting_date):
        # Search for a date formatted as MM/DD in the description, starting from the right
        match = re.search(r'(\d{2}/\d{2})(?!.*\d{2}/\d{2})', description[::-1])
        if match:
            date_str = match.group(1)[::-1]  # Re-reverse to get the correct date string
            month, day = map(int, date_str.split('/'))
            # Use the year from the posting date
            year = posting_date.year
            return datetime(year, month, day)
        else:
            # If no date is found in the description, use the posting date
            return posting_date

    def add_purchase_date(self, df):

        # Convert the 'POSTING DATE' to datetime
        df['POSTING DATE'] = pandas.to_datetime(df['POSTING DATE'])

        # Apply the function to create the 'PURCHASE DATE' column
        df['PURCHASE DATE'] = df.apply(lambda row: self.extract_purchase_date(row['DESCRIPTION'], row['POSTING DATE']), axis=1)

        return df


    def start_process(self):
        query = clean_up_config_value(self._trends_config.get('QUERIES', 'expenses', raw=True))
        raw_column_names = [raw_value for raw_value in self._trends_config["COLUMN ORDER"]["expenses"].split(",")]
        columns = [clean_up_config_value(value) for value in raw_column_names]
        df = pandas.DataFrame(self._db_interface.execute_query(query), columns=columns)
        df = self.add_purchase_date(df)

        # Convert the 'POSTING DATE' to datetime
        df['PURCHASE DATE'] = pandas.to_datetime(df['PURCHASE DATE'])

        # Extract the day of the week from the 'PURCHASE DATE'
        df['DAY OF WEEK'] = df['PURCHASE DATE'].dt.day_name()

        # Define the order of days of the week starting from Sunday
        days_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

        # Group by 'DAY OF WEEK' and 'DESCRIPTION' to get the count of transactions
        expense_summary = df.groupby(['DAY OF WEEK', 'DESCRIPTION']).size().reset_index(name='COUNT')

        # Pivot the table to make 'DAY OF WEEK' the columns
        expense_pivot = expense_summary.pivot(index='DESCRIPTION', columns='DAY OF WEEK', values='COUNT').fillna(0)

        # Reorder the columns according to the defined days_order
        expense_pivot = expense_pivot[days_order]

        # Display the resulting table
        expense_pivot.to_csv('trends.csv')