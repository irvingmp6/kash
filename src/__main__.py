import argparse
import textwrap

from _version import __version__

from src.controller import ImportParserController
from src.controller import GetQueryParserController
from src.interface_text import get_help_menu
from src.interface_funcs import db_connection
from src.interface_funcs import ConfigSectionIncompleteError
from src.interface_funcs import DuplicateAliasError
from src.interface_funcs import QueryNotDefinedError
from src.interface_funcs import BadQueryStructureError
from src.interface_funcs import UnknownAliasError

def get_cli_args():
    help_menu = get_help_menu()
    cli = argparse.ArgumentParser(
        prog='kash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_menu['desc'])
    )
    subparsers = cli.add_subparsers(help=help_menu['subparsers'])

    # Import Subparser
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

    # Import Raw Subparser
    import_raw_parser = subparsers.add_parser(
        'import-raw',
        help=help_menu['import']['desc']
    )
    import_raw_parser.set_defaults(func=start_import_process)
    import_raw_parser.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
        help=textwrap.dedent(help_menu['import']['sqlite_db'])
    )
    import_raw_parser.add_argument(
        'import_config',
        metavar='<CONFIG>',
        help=textwrap.dedent(help_menu['import-raw']['import_config'])
    )
    import_raw_parser.add_argument(
        'csv_file',
        metavar='<CSV FILE>',
        default=None,
        help=textwrap.dedent(help_menu['import']['csv_file'])
        )
    import_raw_parser.add_argument(
        '--account-alias', '-a',
        type=str,
        default='',
        help=textwrap.dedent(help_menu['import']['account_alias'])
    )
    import_raw_parser.add_argument(
        '--commit', '-c',
        action='store_true',
        default=False,
        help=textwrap.dedent(help_menu['import']['commit'])
    )

    get_parser = subparsers.add_parser(
        'get'
        )
    get_parser.set_defaults(func=start_get_process)
    get_parser.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
    )
    get_parser.add_argument(
        'queries_config',
        metavar='<CONFIG>',
    )
    get_parser.add_argument(
        'query_calls',
        nargs='+',
        metavar='<QUERY ALIAS>',
    )

    return cli.parse_args()

def start_import_process(cli_args: argparse.Namespace):
    controller = ImportParserController(cli_args)
    controller.start_process()

def start_get_process(cli_args: argparse.Namespace):
    controller = GetQueryParserController(cli_args)
    controller.start_process()


def main():
    cli_args = None

    try:
        cli_args = get_cli_args()
        if hasattr(cli_args, 'func'):
            cli_args.func(cli_args)
        else:
            print('Not enough arguments passed. Fore usage details run "kash --help"')

    except (FileNotFoundError, ConfigSectionIncompleteError,
            DuplicateAliasError, QueryNotDefinedError,
            BadQueryStructureError, UnknownAliasError) as e:
        print(f"Error: {e}")

    finally:
        if hasattr(cli_args, "sqlite_db"):
            cli_args.sqlite_db.close()

if __name__ == "__main__":
    main()