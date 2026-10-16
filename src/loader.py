# src/loader.py
"""Load and preprocess Fly-In map file"""

from pathlib import Path


class Loader:
    """
    Load configuration lines from a Fly-In map file.

    Parameters
    ----------
    filename : Path
        Path to the map file to load.
    """
    def __init__(self, filename: Path) -> None:
        """
        Initialize the map loader.

        Parameters
        ----------
        filename : Path
            Path to the map file.
        """
        self.filename = filename

    def load_map(self) -> list[tuple[int, str, list[str]]]:
        """
        Read and preprocess the map configuration.

        Comments and empty lines are ignored. Each valid line is split
        into its configuration type and list of attributes while keeping
        the original line number.

        Returns
        -------
        list[tuple[int, str, list[str]]]
            Parsed configuration lines as tuples containing the line
            number, configuration type, and attributes.

        Raises
        ------
        FileNotFoundError
            If the map file cannot be found.
        ValueError
            If a configuration line has an invalid format.
        """
        map_config: list[tuple[int, str, list[str]]] = []
        try:
            with open(self.filename, 'r') as f:
                for l_nb, line in enumerate(f, start=1):
                    line = line.split("#")[0].strip()
                    # ignore empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    name, attrs_block = line.split(':', 1)  # maxsplit=1
                    # splits at space ' ' (default), attr will be list
                    name = name.strip()
                    attrs: list[str] = attrs_block.strip().split()
                    trio: tuple[int, str, list[str]] = (l_nb, name, attrs)
                    map_config.append(trio)
                    # print(map_config)
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file {self.filename} not found.")
        except ValueError as e:  # e.g. missing ":"
            raise ValueError(f"line {l_nb}, invalid map format: {e}")
        return map_config
