import argparse
import textwrap

from _version import __version__

from src.controllers.controller import Controller
from src.interface.interface_text import get_help_menu
from src.interface.interface_funcs import db_connection
from src.interface.interface_funcs import pathlib_csv_path
from src.interface.interface_funcs import WrongFileExtension

def get_args():
    help_menu = get_help_menu()
    cli = argparse.ArgumentParser(
        prog='kash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_menu['desc'])
    )
    cli.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
        help=textwrap.dedent(help_menu['sqlite_db'])
    )
    cli.add_argument(
        '--import_csv', '-i',
        nargs='+',
        default=None,
        type=pathlib_csv_path,
        help=textwrap.dedent(help_menu['import_csv'])
        )
    cli.add_argument(
        '--commit', '-c',
        action='store_true',
        default=False,
        help=textwrap.dedent(help_menu['commit'])
    )
    return cli.parse_args()

def main():
    args = None

    try:
        args = get_args()
        controller = Controller(args)
        controller.start_process()

    except (WrongFileExtension, FileNotFoundError) as e:
        print(f"Error: {e}")

    finally:
        if args:
            args.sqlite_db.close()

if __name__ == "__main__":
    main()