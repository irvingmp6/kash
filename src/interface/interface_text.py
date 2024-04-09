def get_help_menu() -> dict:
    menu = {}
    menu['import_csv'] = """Imports new records from csv file(s)"""
    menu['commit'] = """Commits changes to database based on analysis"""
    menu['desc'] = """A command-line tool that forecasts financial climate based on bank transactions."""
    menu['sqlite_db'] = """Path to new or existing sqlite db"""
    return menu
