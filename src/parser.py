# parser.py

from .models import Hub, Connection, MapConfig, HubRole
from pydantic import ValidationError


# start_hub: start 0 0 [zone=priority color=cyan max_drones=3]
class Parser:
    def __init__(self, lines: list[tuple[int, str, list[str]]]) -> None:
        self.lines = lines
        self.hubs: list[Hub] = []
        self.connections: list[Connection] = []

    def parse_map(self) -> MapConfig:
        if not self.lines:
            raise ValueError("Map file is empty")
        l_nb, typ, attrs = self.lines[0]  # the first entry should be nb_drones
        if typ != "nb_drones":  # checking the 1st lines[0] for nb_drone int
            raise ValueError(f"line {l_nb}: nb_drones to be 1st config line")
        if len(attrs) != 1:  # only one info allowed in nb_drones: int
            raise ValueError(f"line {l_nb}: Usage: nb_drones: <int>")
        # nb will be converted with pydantic model validatation
        nb_drones: str = attrs[0]
        print(f"nb of drones: {nb_drones}")
        for l_nb, typ, attrs in self.lines[1:]:
            match typ:
                case "nb_drones":
                    raise ValueError(f"line {l_nb}: nb_drones already defined")
                case "hub" | "start_hub" | "end_hub":
                    hub = self.hub_config(l_nb, typ, attrs)
                    if self.hub_exists(hub):
                        raise ValueError(f"line {l_nb}: hub duplicate")
                    # print(hub)
                    self.hubs.append(hub)
                case "connection":
                    # print("connection")
                    connection = self.connect_config(l_nb, attrs)
                    # print(connection)
                    if self.connection_exists(connection):
                        raise ValueError(f"line {l_nb}: duplicate connection")
                    self.connections.append(connection)
                case _:
                    raise ValueError(f"line {l_nb}: unrecognised data: {typ}")
        return MapConfig(
            nb_drones=nb_drones,
            hubs=self.hubs,
            connections=self.connections,
        )

    def hub_config(self, l_nb: int, typ: str, attrs: list[str]) -> Hub:
        metadata: dict[str, str] = {}  # dict to be fed in Hub object model
        if len(attrs) < 3:
            raise ValueError(f"line {l_nb}: hub needs name, x, y coordinates")
        match typ:
            case "start_hub":
                role = HubRole.START
            case "end_hub":
                role = HubRole.END
            case "hub":
                role = HubRole.REGULAR
        name = attrs[0]
        if "-" in name or " " in name:
            raise ValueError(f"line {l_nb}: hubname can't contain '-' or ' '")
        if len(attrs) > 3:
            if not attrs[3].startswith("[") or not attrs[-1].endswith("]"):
                raise ValueError(f"line {l_nb}: metadata must be inside of []")
            metadata_parts: list[str] = attrs[3:]  # separate list for metadata
            metadata_parts[0] = metadata_parts[0].removeprefix("[")
            metadata_parts[-1] = metadata_parts[-1].removesuffix("]")
            # print(metadata_parts)

            for part in metadata_parts:
                if "=" not in part:
                    raise ValueError(f"line {l_nb}: invalid metadata {part}")
                meta, spec = part.split('=', 1)  # color=gray -> color gray
                if not meta or not spec:  # missing data before/after =
                    raise ValueError(f"line {l_nb}: invalid metadata {part}")
                # print(meta)
                match meta:
                    case "color" | "max_drones" | "zone":
                        metadata[meta] = spec
                    case _:
                        raise ValueError(f"line {l_nb}: unknown metadata")
        if role in (HubRole.START, HubRole.END):
            metadata.pop("max_drones", None)  # 1 by default, will be ignored
        try:
            return Hub(
                l_nb=l_nb,
                role=role,
                name=attrs[0],
                x=attrs[1],
                y=attrs[2],
                **metadata,
            )
        except ValidationError as e:
            raise ValueError(f"line {l_nb}: {e}") from e

    def hub_exists(self, hub: Hub) -> bool:
        for already in self.hubs:
            if already.name == hub.name:
                return True
        return False

    def connect_config(self, l_nb: int, attrs: list[str]) -> Connection:
        # print(attrs)
        # dict to be fed in Connection object model:
        metadata: dict[str, str] = {}
        if len(attrs) < 1 or len(attrs) > 2 or attrs[0].count("-") != 1:
            raise ValueError(
                f"line {l_nb}: "
                "usage example: "
                "connection: end1hub-end2hub [max_link_capacity=2]"
            )
        end1: Hub | None = None
        end2: Hub | None = None
        end1_name, end2_name = attrs[0].split("-", 1)
        if not end1_name or not end2_name:
            raise ValueError(f"line {l_nb}: invalid connection '{attrs[0]}'")
        for hub in self.hubs:  # if hub used for connection exists in hubs list
            if hub.name == end1_name:
                end1 = hub
            if hub.name == end2_name:
                end2 = hub
        if end1 is None or end2 is None:
            raise ValueError(f"line {l_nb}: conection refers to undefined hub")
        if end1_name == end2_name:
            raise ValueError(f"line {l_nb}: stagnating connection")
        if len(attrs) == 2:
            if not attrs[1].startswith("[") or not attrs[1].endswith("]"):
                raise ValueError(f"line {l_nb}: metadata must be in []")
            max_str: str = attrs[1].removeprefix("[").removesuffix("]")
            if "=" not in max_str:
                raise ValueError(f"line {l_nb}: invalid metadata '{max_str}'")
            key, value = max_str.split("=", 1)
            if key != "max_link_capacity" or not value:
                raise ValueError(f"line {l_nb}: invalid metadata '{max_str}'")
            metadata[key] = value
            # print(metadata)
        try:
            return Connection(
                l_nb=l_nb,
                end1=end1,
                end2=end2,
                **metadata,
            )
        except ValidationError as e:
            raise ValueError(f"line: {l_nb}: {e}") from e

    def connection_exists(self, connection: Connection) -> bool:
        for already in self.connections:
            same_connection: bool = (
                already.end1 == connection.end1
                and already.end2 == connection.end2
            )
            opposite_connection: bool = (
                already.end1 == connection.end2
                and already.end2 == connection.end1
            )
            if same_connection or opposite_connection:
                return True
        return False
