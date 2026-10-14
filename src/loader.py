# src/loader.py

class Loader:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def load_map(self) -> list[tuple[int, str, list[str]]]:
        map_config: list[tuple[int, str, list[str]]] = []
        try:
            with open(self.filename, 'r') as f:
                for l_nb, line in enumerate(f, start=1):
                    line = line.strip()
                    # ignore empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    name, attrs = line.split(':', 1)  # maxsplit=1
                    # splits at space ' ' (default), attr will be list
                    name, attrs = name.strip(), attrs.strip().split()
                    trio: tuple[int, str, list[str]] = (l_nb, name, attrs)
                    map_config.append(trio)
                    # print(map_config)
        except FileNotFoundError:
            raise FileNotFoundError(f"Map file {self.filename} not found.")
        except ValueError as e:  # e.g. missing ":"
            raise ValueError(f"line {l_nb}, invalid map format: {e}")
        return map_config
