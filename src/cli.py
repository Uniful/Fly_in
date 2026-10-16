# cli.py

import argparse
from pathlib import Path


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="fly_in",
        description="Fly-In pathfinding program",
        epilog="Example: uv run python -m src maps/<level>/<mapfile.txt>",
    )

    parser.add_argument(
        "mapfile",  # positional argument
        type=Path,  # arg myfile.txt is converted into Path("myfile.txt")
        nargs="?",  # This positional argument can appear zero or one time
        default=Path("maps/easy/01_linear_path.txt"),
        help="Path to the map graph file"
    )

    parser.add_argument(  # DELETE !!!!!!!!!!!!
        "--info",
        action="store_true",
        help="Display zone and connection capacity usage for each turn",
    )

    args = parser.parse_args()
    # print(type(args.input))  # prints: <class 'pathlib.PosixPath'>
    # print(args.input.name)  # prints file name: function_calling_tests.json
    # print(args.input.parent)  # prints parent directory name: data/input
    # with open(args.input) as f:
    # with args.input.open("r") as f:

    return args
