from configparser import ConfigParser
from io import BytesIO
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import pandas as pd
from pandas.testing import assert_frame_equal

from src.controllers.controller import Controller


class TestControllerHappyPathChaseCSV(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        cls.user_settings = MagicMock()
        cls.user_settings.conn = MagicMock()
        cls.user_settings.new_csv_files = ["Chase_bank_activity_1.csv", "Chase_bank_activity_2.csv"]
        cls.user_settings.commit = False
        cls.user_settings.config = None
        cls.unprocessed_df_data = {
            "Details": ["DEBIT"],
            "Posting Date": ["2/01/2024"],
            "Description": ["SPAM BAR HAM"],
            "Amount": ["-7.77"],
            "Type": ["DEBIT_CARD"],
            "Balance": ["6.66"],
            "Check or Slip #": [""],
            "Extra_1": [""],
        }
        cls.unprocessed_df = pd.DataFrame(data=cls.unprocessed_df_data)
        cls.processed_df_data = {
            "Details": ["DEBIT"],
            "Posting Date": ["2/01/2024"],
            "Description": ["SPAM BAR HAM"],
            "Amount": ["-7.77"],
            "Type": ["DEBIT_CARD"],
            "Balance": ["6.66"],
            "Check or Slip #": [""],
            "Extra_1": [""],
            "Account Alias": ["Chase Bank"],
            "Transaction ID": ["DEF234"]
        }
        cls.processed_df = pd.DataFrame(data=cls.processed_df_data)

    @classmethod
    def tearDownClass(cls):
        pass

    @patch('src.controllers.controller.UserSettings')
    def test_Controller__init__(self, UserSettings_mock):
        args = MagicMock()
        UserSettings_mock.return_value = MagicMock()
        user_settings = UserSettings_mock.return_value

        controller = Controller(args)
        self.assertEqual(controller._user_settings, user_settings)
        self.assertEqual(controller._conn, user_settings.conn)
        self.assertEqual(controller._new_csv_files, user_settings.new_csv_files)
        self.assertEqual(controller._commit, user_settings.commit)
        self.assertEqual(controller._config, user_settings.config)
        chase_column_names = ["Details", "Posting Date", "Description", 
                              "Amount", "Type", "Balance", "Check or Slip #", 
                              "Extra 1"]
        self.assertEqual(controller._chase_column_names, chase_column_names)

    def test_start_process(self):
        self_mock = MagicMock()
        self_mock.user_settings = self.user_settings

        Controller.start_process(self_mock)

        self_mock._ingest_new_transactions_csv.assert_called_once_with()

    @patch('src.controllers.controller.Controller._insert_df_into_bank_transactions_table')
    @patch('src.controllers.controller.Controller._get_new_settled_transactions_df')
    def test__ingest_new_transactions_csv(self, 
                                        _get_new_settled_transactions_df_mock, 
                                        _insert_df_into_bank_transactions_table_mock):
        self_mock = MagicMock()
        self_mock._new_csv_files = ["Chase_bank_activity_1.csv", 
                                   "Chase_bank_activity_2.csv"]
        self_mock._get_new_settled_transactions_df.side_effect = ["foo", "bar"]

        Controller._ingest_new_transactions_csv(self_mock)

        result = self_mock._get_new_settled_transactions_df.call_args_list
        _get_new_settled_transactions_df_expected_calls = [call(self_mock._new_csv_files[0]), 
                                          call(self_mock._new_csv_files[1])]
        self.assertEqual(result, _get_new_settled_transactions_df_expected_calls)
        insert_df_into_bank_transactions_table_expected_calls = [call("foo"), call("bar")]
        result = self_mock._insert_df_into_bank_transactions_table.call_args_list
        self.assertEqual(result, insert_df_into_bank_transactions_table_expected_calls)

    @patch('src.controllers.controller.Controller._create_dataframe_from_chase_csv')
    @patch('src.controllers.controller.Controller._create_dataframe_from_foreign_csv')
    def test__get_new_settled_transactions_df(self, \
                                    _create_dataframe_from_foreign_csv_mock, \
                                    _create_dataframe_from_chase_csv):
        self_mock = MagicMock()
        self_mock._account_alias = "Chase Bank"
        self_mock._config = None
        csv_file = "Chase_bank_activity.csv"
        chase_csv_data = {
            "Details": ["DEBIT","DEBIT","DEBIT","DEBIT"],
            "Posting Date": ["2/01/2024","2/01/2024","2/01/2024","2/01/2024"],
            "Description": ["FOO BAR BAZ","SPAM HAM EGGS","FOO SPAM BAR","SPAM BAR HAM"],
            "Amount": ["-1.11","-3.33","-5.55","-7.77"],
            "Type": ["DEBIT_CARD","DEBIT_CARD","DEBIT_CARD","DEBIT_CARD"],
            "Balance": [" "," ","4.44","6.66"],
            "Check or Slip #": ["","","",""],
            "Extra_1": ["","","",""],
            "Account Alias": ["Chase Bank","Chase Bank","Chase Bank","Chase Bank"],
            "Transaction ID": ["GHI345","JKL456","ABC123","DEF234"]
        }
        chase_csv_df = pd.DataFrame(data=chase_csv_data)
        self_mock._create_dataframe_from_chase_csv.return_value = chase_csv_df
        self_mock._conn.execute.return_value.fetchall.return_value = [["ABC123"]]

        result = Controller._get_new_settled_transactions_df(self_mock, csv_file)

        self_mock._create_dataframe_from_foreign_csv.assert_not_called()
        actual_calls = self_mock._create_dataframe_from_chase_csv.call_args_list
        _create_dataframe_from_chase_csv_expected_calls = [call(csv_file)]
        self.assertEqual(actual_calls, _create_dataframe_from_chase_csv_expected_calls)
        data = {
            "Details": ["DEBIT"],
            "Posting Date": ["2/01/2024"],
            "Description": ["SPAM BAR HAM"],
            "Amount": ["-7.77"],
            "Type": ["DEBIT_CARD"],
            "Balance": ["6.66"],
            "Check or Slip #": [""],
            "Extra_1": [""],
            "Account Alias": ["Chase Bank"],
            "Transaction ID": ["DEF234"]
        }
        processed_df = pd.DataFrame(data=data)
        assert_frame_equal(result.reset_index(drop=True), processed_df.reset_index(drop=True))
    
    @patch('src.controllers.controller.pandas')
    @patch('src.controllers.controller.Controller._add_required_columns_to_df')
    def test__create_dataframe_from_chase_csv(self, 
                                              _add_required_columns_to_df_mock, 
                                              pandas_mock):
        self_mock = MagicMock()
        _add_required_columns_to_df_mock.result_value = "result"
        csv_file = "Chase_bank_activity.csv"
        account_alias = "Chase Bank"

        result = Controller._create_dataframe_from_chase_csv(self_mock, csv_file)

        pandas_mock.read_csv.called_once_with(csv_file, delmiter=",", skipows=[0], 
                                              header=None, names=["Details", "Posting Date", 
                                                                  "Description", "Amount", "Type", 
                                                                  "Balance", "Check or Slip #", "Extra 1"],
                                              converters={"Balance": str})
        _add_required_columns_to_df_mock.called_once_with(pandas_mock.read_csv.return_value)
        self.assertEqual(result, self_mock._add_required_columns_to_df.return_value)

    @patch('src.controllers.controller.hashlib')
    def test__add_required_columns_to_df(self, hashlib_mock):
        hashlib_mock.sha256.return_value.hexdigest.return_value = "DEF234"
        self_mock = MagicMock()
        self_mock._account_alias = "Chase Bank"
        df = self.unprocessed_df

        result = Controller._add_required_columns_to_df(self_mock, df)
        expected_df = self.processed_df
        assert_frame_equal(result.sort_index(axis=1), expected_df.sort_index(axis=1))
    
    # @patch('src.controllers.controller.print')
    # def test__insert_df_into_bank_transactions_table_commit_is_False(self, print_mock):
    def test__insert_df_into_bank_transactions_table_commit_is_False(self):
        self_mock = MagicMock()
        self_mock._commit = True
        self_mock._conn = MagicMock()
        df = self.processed_df

        Controller._insert_df_into_bank_transactions_table(self_mock, df)

    # def test__insert_df_into_bank_transactions_table_commit_is_True(self):
    #     self_mock = MagicMock()
    #     self_mock._commit = True
    #     self_mock._conn = MagicMock()


class TestControllerHappyPathNonChaseCSV(TestCase):
    pass


class TesatControllerBadConfigGeneralSectioonMissingKey(TestCase):
    pass


class TesatControllerBadConfigHeaderSectioonMissingKey(TestCase):
    pass