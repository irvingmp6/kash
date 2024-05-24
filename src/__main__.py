import argparse
import textwrap
from importlib.metadata import version as get_version

from src.controller import (
    ImportParserController, 
    MakeImportReadyParserController, 
    RunQueryParserController
)
from src.interface_text import get_help_menu
from src.interface_funcs import (
    db_connection,
    ConfigSectionIncompleteError,
    DuplicateAliasError,
    QueryNotDefinedError,
    BadQueryStructureError,
    UnknownAliasError,
)

version = get_version = ".".join(get_version("Kash").split("."))

def get_cli_args() -> argparse.Namespace:
    """
    Parse command-line arguments using argparse.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    help_menu = get_help_menu()

    # Create CLI Parser
    cli = argparse.ArgumentParser(
        prog='kash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_menu['desc'])
    )

    cli.add_argument(
        '--version', action='version',
        version='%(prog)s {version}'.format(version=version)
    )

    subparsers = cli.add_subparsers(help=help_menu['subparsers'])

    # Create Import Subparser
    import_parser = subparsers.add_parser(
        'import',
        help=help_menu['import']['desc']
    )
    import_parser.set_defaults(func=start_import_process)
    import_parser.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
        help=textwrap.dedent(help_menu['import']['sqlite_db'])
    )
    import_parser.add_argument(
        'csv_file',
        metavar='<CSV FILE>',
        default=None,
        help=textwrap.dedent(help_menu['import']['csv_file'])
    )
    import_parser.add_argument(
        '--account-alias', '-a',
        type=str,
        default='',
        help=textwrap.dedent(help_menu['import']['account_alias'])
    )
    import_parser.add_argument(
        '--commit', '-c',
        action='store_true',
        default=False,
        help=textwrap.dedent(help_menu['import']['commit'])
    )

    # Create Make Import Ready Subparser
    make_import_ready_parser = subparsers.add_parser(
        'make-import-ready',
        help="Reformats downloaded CSV file to make it"
    )
    make_import_ready_parser.set_defaults(func=start_make_import_ready_process)
    make_import_ready_parser.add_argument(
        'conversion_config',
        metavar='<CONVERSION CONFIG FILEPATH>',
    )
    make_import_ready_parser.add_argument(
        'raw_csv_file',
        metavar='<RAW CSV FILEPATH>',
    )

    # Create Run Query Subparser
    run_query_parser = subparsers.add_parser(
        'run-query',
        help="Runs query alias and displays rows"
    )
    run_query_parser.set_defaults(func=start_run_query_process)
    run_query_parser.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
    )
    run_query_parser.add_argument(
        'queries_config',
        metavar='<CONFIG>',
    )
    run_query_parser.add_argument(
        'query_calls',
        nargs='+',
        metavar='<QUERY ALIAS>',
    )
    run_query_parser.add_argument(
        '--rows',
        default=1,
        type=int,
    )
    run_query_parser.add_argument(
        '--save-results',
        default=False,
        action='store_true',
    )

    return cli.parse_args()

def start_import_process(cli_args: argparse.Namespace) -> None:
    """
    Start the import process based on CLI arguments.

    Args:
        cli_args (argparse.Namespace): Parsed command-line arguments.
    """
    controller = ImportParserController(cli_args)
    controller.start_process()

def start_make_import_ready_process(cli_args: argparse.Namespace) -> None:
    """
    Start the make import ready process based on CLI arguments

    Args:
        cli_args (argparse.Namespace): Parsed command-line arguments.
    """
    controller = MakeImportReadyParserController(cli_args)
    controller.start_process()

def start_run_query_process(cli_args: argparse.Namespace) -> None:
    """
    Start the run query process based on CLI arguments.

    Args:
        cli_args (argparse.Namespace): Parsed command-line arguments.
    """
    controller = RunQueryParserController(cli_args)
    controller.start_process()

def main() -> None:
    """
    Main function to execute the command-line interface.

    Calls one of two functions:
        - start_import_process()
        - start_get_process()
    
    Handles custom raised exceptions by printing the error message with helpful troubleshooting tips instead of a stack trace.
    However, uncaught exceptions will be raised, allowing for easier bug tracking.
    """
    cli_args = None

    try:
        cli_args = get_cli_args()
        if hasattr(cli_args, 'func'):

            # Call mapped function
            cli_args.func(cli_args)
        else:
            print('Not enough arguments passed. For usage details, run "kash --help"')

    # Handle custom errors
    except (FileNotFoundError, ConfigSectionIncompleteError,
            DuplicateAliasError, QueryNotDefinedError,
            BadQueryStructureError, UnknownAliasError) as e:
        print(f"Error: {e}")

    finally:
        if hasattr(cli_args, "sqlite_db"):
            cli_args.sqlite_db.close()

if __name__ == "__main__":
    main()