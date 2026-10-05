# src/loader.py

def load_map(filename: str) -> list[tuple[int, str, list[str]]]:
    map_config: list[tuple[int, str, list[str]]] = []
    try:
        with open(filename, 'r') as f:
            for l_nb, line in enumerate(f, start=1):
                line = line.strip()
                # ignore empty lines and comments
                if not line or line.startswith('#'):
                    continue
                name, attrs = line.split(':', 1)  # maybe here to split value again and make it a list
                name, attrs = name.strip(), attrs.strip().split()  # splits at space ' ' (default)
                trio: tuple = (l_nb, name, attrs)
                map_config.append(trio)
                # print(map_config)
    except FileNotFoundError:
        raise FileNotFoundError(f"Map file {filename} not found.")
    except ValueError as e:  # e.g. missing ":"
        raise ValueError(f"line {l_nb}, invalid map format: {e}")
    except Exception as e:
        raise Exception(f"line {l_nb}: A non-pydantic error occured: {e}")
    return map_config
