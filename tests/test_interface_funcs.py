from unittest import TestCase, skip
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call
from sqlite3 import OperationalError

from src.interface_funcs import db_connection
from src.interface_funcs import pathlib_path
from src.interface_funcs import create_bank_activity_table
from src.interface_funcs import check_bank_activity_table_exists
from src.interface_funcs import WrongFileExtension
from src.interface_funcs import SQLOperationalError


class TestInterfaceFuncs(TestCase):

    def test_create_bank_activity_table(self):
        query = """
        CREATE TABLE
            bank_activity(ID INTEGER PRIMARY KEY, Account_Alias, Transaction_ID, Details, 
                Posting_Date, Description,  Amount, 
                Type, Balance, Check_or_Slip_num, Reconciled,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);"""
        conn_mock = MagicMock()
        create_bank_activity_table(conn_mock)
        conn_mock.execute.assert_called_once_with(query)


    def test_check_bank_activity_table_exists(self):
        query = """
        SELECT 
                Account_Alias, Transaction_ID, Details, 
                Posting_Date, Description, Amount, Type, 
                Balance, Check_or_Slip_num, Reconciled, 
                Timestamp
        FROM
                bank_activity;"""
        conn_mock = MagicMock()
        check_bank_activity_table_exists(conn_mock)
        conn_mock.execute.assert_called_once_with(query)

    @patch('src.interface_funcs.sqlite3')
    @patch('src.interface_funcs.print')
    @patch('src.interface_funcs.create_bank_activity_table')
    @patch('src.interface_funcs.check_bank_activity_table_exists')
    @patch('src.interface_funcs.Path.is_file')
    def test_db_connection(self, 
                           is_file_mock, 
                           check_bank_activity_table_exists_mock, 
                           create_bank_activity_table_mock,
                           print_mock,
                           sqlite3_mock):
        is_file_mock.return_value = True
        db_path = "path/to/database.db"
        result = db_connection(db_path)
        conn_mock = sqlite3_mock.connect.return_value

        sqlite3_mock.connect.assert_called_once_with(db_path)

        expected_result = conn_mock
        self.assertEqual(result, expected_result)

        check_bank_activity_table_exists_mock.assert_called_once_with(conn_mock)
        create_bank_activity_table_mock.assert_not_called()

    @patch('src.interface_funcs.sqlite3')
    @patch('src.interface_funcs.print')
    @patch('src.interface_funcs.create_bank_activity_table')
    @patch('src.interface_funcs.check_bank_activity_table_exists')
    @patch('src.interface_funcs.Path.is_file')
    def test_db_connection_wrong_extension(self, 
                           is_file_mock, 
                           check_bank_activity_table_exists_mock, 
                           create_bank_activity_table_mock,
                           print_mock,
                           sqlite3_mock):
        is_file_mock.return_value = True
        db_path = "path/to/database.txt"

        with self.assertRaises(WrongFileExtension) as context:
            db_connection(db_path)
            error_message = f"File extension is not '.db': {db_path}"
            self.assertTrue(error_message==context.msg)

    @patch('src.interface_funcs.sqlite3')
    @patch('src.interface_funcs.print')
    @patch('src.interface_funcs.create_bank_activity_table')
    @patch('src.interface_funcs.check_bank_activity_table_exists')
    @patch('src.interface_funcs.Path.is_file')
    def test_db_connection_create_new_db(self, 
                           is_file_mock, 
                           check_bank_activity_table_exists_mock, 
                           create_bank_activity_table_mock,
                           print_mock,
                           sqlite3_mock):
        is_file_mock.return_value = False
        db_path = "path/to/database.db"
        result = db_connection(db_path)
        conn_mock = sqlite3_mock.connect.return_value

        sqlite3_mock.connect.assert_called_once_with(db_path)

        expected_result = conn_mock
        self.assertEqual(result, expected_result)

        create_bank_activity_table_mock.assert_called_once_with(conn_mock)
        check_bank_activity_table_exists_mock.assert_not_called()

    @patch('src.interface_funcs.sqlite3')
    @patch('src.interface_funcs.print')
    @patch('src.interface_funcs.create_bank_activity_table')
    @patch('src.interface_funcs.check_bank_activity_table_exists')
    @patch('src.interface_funcs.Path.is_file')
    def test_db_connection_check_db_raise_SQLOperationalError(self, 
                           is_file_mock, 
                           check_bank_activity_table_exists_mock, 
                           create_bank_activity_table_mock,
                           print_mock,
                           sqlite3_mock):
        is_file_mock.return_value = True
        db_path = "path/to/database.db"
        check_bank_activity_table_exists_mock.side_effect = OperationalError
        
        with self.assertRaises(SQLOperationalError) as context:
            db_connection(db_path)


