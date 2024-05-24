import os
import argparse
import configparser


class UserSettings:
    """Base class for managing user settings."""

    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize UserSettings with command-line arguments.

        Args:
            cli_args (argparse.Namespace): Command-line arguments parsed by argparse.
        """
        self.cli_args = cli_args
        self.conn = getattr(cli_args, 'sqlite_db', None)  # SQLite database connection
        self.commit = getattr(cli_args, 'commit', False)  # Whether to commit changes to database

    def get_config_object(self, config_file: str) -> configparser.ConfigParser:
        """
        Get a ConfigParser object from the specified configuration file.

        Args:
            config_file (str): Path to the configuration file.

        Returns:
            configparser.ConfigParser: ConfigParser object initialized with the file contents.

        Raises:
            FileNotFoundError: If the specified config_file does not exist.
        """
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f"Could not locate config file:\n{config_file}")
        cp = configparser.ConfigParser()
        cp.read(config_file)
        return cp


class ImportParserUserSettings(UserSettings):
    """Class for managing user settings specific to import operations."""

    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize ImportParserUserSettings with command-line arguments.

        Args:
            cli_args (argparse.Namespace): Command-line arguments parsed by argparse.
        """
        super().__init__(cli_args)
        self.csv_file = cli_args.csv_file  # Path to the CSV file
        self.account_alias = cli_args.account_alias  # Account alias for importing bank activity

class MakeImportReadyParserUserSettings(UserSettings):
    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize MakeImportReadyUserSettings with command-line arguments.

        Args:
            cli_args (argparse.Namespace): Command-line arguments parsed by argparse.
        """
        super().__init__(cli_args)
        self.raw_csv_file = cli_args.raw_csv_file  # Path to the raw CSV file
        self.conversion_config = self.get_config_object(cli_args.conversion_config)

class RunQueryParserUserSettings(UserSettings):
    """Class for managing user settings related to query operations."""

    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize RunQueryUserSettings with command-line arguments.

        Args:
            cli_args (argparse.Namespace): Command-line arguments parsed by argparse.
        """
        super().__init__(cli_args)
        self.queries_config_path = cli_args.queries_config  # Path to the queries configuration file
        self.queries_config = self.get_config_object(self.queries_config_path)  # ConfigParser object for queries configuration file
        self.query_calls = cli_args.query_calls  # Lis of query calls to execute
        self.save_results = cli_args.save_results
        self.rows = cli_args.rows

class TrendsParserUserSettings(UserSettings):
    """Class for managing user settings related to query operations."""

    def __init__(self, cli_args: argparse.Namespace) -> None:
        """
        Initialize TrendsUserSettings with command-line arguments.

        Args:
            cli_args (argparse.Namespace): Command-line arguments parsed by argparse.
        """
        super().__init__(cli_args)
        self.trends_config_path = cli_args.trends_config  # Path to the trends configuration file
        self.trends_config = self.get_config_object(self.trends_config_path)