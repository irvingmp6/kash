import os
from configparser import ConfigParser


class UserSettings:
    def __init__(self, cli_args):
        self.cli_args = cli_args
        self.conn = self.cli_args.sqlite_db if hasattr(self.cli_args, 'sqlite_db') else None
        self.commit = self.cli_args.commit if hasattr(self.cli_args, 'commit') else None

class ImportParserUserSettings(UserSettings):
    def __init__(self, cli_args):
        super(ImportParserUserSettings, self).__init__(cli_args)
        self.csv_file = self.cli_args.csv_file
        self.account_alias = self.cli_args.account_alias
        self.import_config = self.get_import_config() if hasattr(self.cli_args, 'import_config') else None

    def get_import_config(self):
        import_config_filepath = self.cli_args.import_config
        if not os.path.isfile(import_config_filepath):
            raise FileNotFoundError(f"Could not locate config file:\n{import_config_filepath}")
        cp = ConfigParser()
        cp.read(import_config_filepath)
        return cp

class GetQueryUserSettings(UserSettings):
    def __init__(self, cli_args):
        super(ImportParserUserSettings, self).__init__(cli_args)
        self.queries_config = self.cli_args.queries_config