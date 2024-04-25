from unittest import TestCase, skip
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

from src.user_settings import ImportParserUserSettings

class TestImportParserUserSettings(TestCase):

    @patch('src.user_settings.hasattr')
    def test__init__(self, hasattr_mock):
        hasattr_mock.side_effect = [True, True, False]
        cli_args = MagicMock()
        cli_args.sqlite_db = MagicMock()
        cli_args.csv_file = "/path/to/file.csv"
        cli_args.account_alias = "My Bank"
        cli_args.commit = False
    
        user_settings = ImportParserUserSettings(cli_args)

        self.assertEqual(user_settings.conn, cli_args.sqlite_db)
        self.assertEqual(user_settings.csv_file, cli_args.csv_file)
        self.assertEqual(user_settings.account_alias, cli_args.account_alias)
        self.assertEqual(user_settings.commit, cli_args.commit)
        self.assertEqual(user_settings.import_config, None)

    @patch('src.user_settings.os.path.isfile')
    @patch('src.user_settings.ConfigParser')
    def test__init__with_import_config(self, ConfigParser_mock, isfile_mock):
        isfile_mock.return_value = True
        cli_args = MagicMock()
        cli_args.csv_file = "/path/to/file.csv"
        cli_args.account_alias = "My Bank"
        cli_args.commit = False
    
        user_settings = ImportParserUserSettings(cli_args)

        self.assertEqual(user_settings.conn, cli_args.sqlite_db)
        self.assertEqual(user_settings.csv_file, cli_args.csv_file)
        self.assertEqual(user_settings.account_alias, cli_args.account_alias)
        self.assertEqual(user_settings.commit, cli_args.commit)
        self.assertEqual(user_settings.import_config, ConfigParser_mock.return_value)

    @patch('src.user_settings.os.path.isfile')
    def test__init__import_config_file_not_found(self, isfile_mock):
        isfile_mock.return_value = False
        cli_args = MagicMock()
    
        with self.assertRaises(FileNotFoundError) as context:
            ImportParserUserSettings(cli_args)