# parser.py
"""Parse and validate Fly-In map configuration data."""

from pydantic import ValidationError
from .models import Hub, Connection, MapConfig, HubRole


# start_hub: start 0 0 [zone=priority color=cyan max_drones=3]
class Parser:
    """
    Parse map configuration lines into Fly-In model objects.

    Parameters
    ----------
    lines : list[tuple[int, str, list[str]]]
        Preprocessed map lines containing the original line number,
        configuration type, and attributes.
    """
    def __init__(self, lines: list[tuple[int, str, list[str]]]) -> None:
        """
        Initialize the map parser.

        Parameters
        ----------
        lines : list[tuple[int, str, list[str]]]
            Preprocessed configuration lines.
        """
        self.lines = lines
        self.hubs: list[Hub] = []
        self.connections: list[Connection] = []

    def parse_map(self) -> MapConfig:
        """
        Parse all configuration lines and build the map configuration.

        Returns
        -------
        MapConfig
            Validated map containing the drone count, hubs, and connections.

        Raises
        ------
        ValueError
            If the map is empty, malformed, contains duplicate definitions,
            or contains unsupported configuration data.
        """
        if not self.lines:
            raise ValueError("Map file is empty")
        l_nb, typ, attrs = self.lines[0]  # the first entry should be nb_drones
        if typ != "nb_drones":  # checking the 1st lines[0] for nb_drone int
            raise ValueError(f"line {l_nb}: nb_drones to be 1st config line")
        if len(attrs) != 1:  # only one info allowed in nb_drones: int
            raise ValueError(f"line {l_nb}: Usage: nb_drones: <int>")
        # nb will be converted with pydantic model validatation
        try:
            nb_drones: int = int(attrs[0])
        except ValueError as e:
            raise ValueError(f"line {l_nb}: nb_drones must be integer") from e
        print(f"nb of drones: {nb_drones}")
        for l_nb, typ, attrs in self.lines[1:]:
            match typ:
                case "nb_drones":
                    raise ValueError(f"line {l_nb}: nb_drones already defined")
                case "hub" | "start_hub" | "end_hub":
                    if typ == "start_hub":
                        self.check_unique_role(HubRole.START, l_nb)
                    elif typ == "end_hub":
                        self.check_unique_role(HubRole.END, l_nb)
                    hub = self.hub_config(l_nb, typ, attrs)
                    if self.hub_exists(hub):
                        raise ValueError(f"line {l_nb}: duplicate hub name")
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
        """
        Create and validate a hub from its configuration attributes.

        Parameters
        ----------
        l_nb : int
            Original line number in the map file.
        typ : str
            Hub configuration type: hub, start_hub, or end_hub.
        attrs : list[str]
            Hub name, coordinates, and optional metadata.

        Returns
        -------
        Hub
            Validated hub model.

        Raises
        ------
        ValueError
            If the hub syntax, coordinates, name, metadata, or values
            are invalid.
        """
        metadata: dict[str, str] = {}  # dict to be fed in Hub object model
        if len(attrs) < 3:
            raise ValueError(f"line {l_nb}: hub needs name, x, y coordinates")

        # after name, x, y the next token must begin metadata
        if len(attrs) > 3 and not attrs[3].startswith("["):
            raise ValueError(
                f"line {l_nb}: invalid hub format: "
                "expected <name> <x> <y> [metadata]; ")

        # assign roles to hubs:
        role: HubRole
        match typ:
            case "start_hub":
                role = HubRole.START
            case "end_hub":
                role = HubRole.END
            case "hub":
                role = HubRole.REGULAR
            case _:
                raise ValueError(f"line {l_nb}: invalid hub type '{typ}'")

        # check the name format
        name = attrs[0]
        if "-" in name or " " in name:  # space will not be there anyway
            raise ValueError(f"line {l_nb}: hubname can't contain '-' or ' '")

        # check if x, y coordinates are integers:
        try:
            x: int = int(attrs[1])
            y: int = int(attrs[2])
        except ValueError as e:
            raise ValueError(
                f"line {l_nb}: hub coordinates must be integers") from e

            # check if metadata are enclosed in brackets []:
        if len(attrs) > 3:
            if not attrs[3].startswith("[") or not attrs[-1].endswith("]"):
                raise ValueError(f"line {l_nb}: metadata must be inside of []")

            # create separate list for metadata
            metadata_parts: list[str] = attrs[3:]
            metadata_parts[0] = metadata_parts[0].removeprefix("[")
            metadata_parts[-1] = metadata_parts[-1].removesuffix("]")
            # print(metadata_parts)

            # checking format of each metadata in the list:
            for part in metadata_parts:
                if "=" not in part:
                    raise ValueError(f"line {l_nb}: invalid metadata {part}")
                # color=gray -> color gray
                meta, spec = part.split('=', 1)
                # missing data before/after =
                if not meta or not spec:
                    raise ValueError(f"line {l_nb}: invalid metadata {part}")
                # print(meta)
                # add {meta: spec} to metadata dictionary
                match meta:
                    case "color" | "max_drones" | "zone":
                        metadata[meta] = spec
                    case _:
                        raise ValueError(f"line {l_nb}: unknown metadata")
        # remove "max_drones" from metadata dict if it exists;
        # if it doesn't exist, return None instead of raising an error
        # will become 1 by default, but later will be ignored
        if role in (HubRole.START, HubRole.END):
            metadata.pop("max_drones", None)

        hub_data: dict[str, object] = {
            "l_nb": l_nb,
            "role": role,
            "name": attrs[0],
            "x": x,
            "y": y,
            **metadata,
        }
        try:
            return Hub.model_validate(hub_data)
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0]
            value = error.get("input")
            raise ValueError(
                f"line {l_nb}: invalid {field} value '{value}'"
            ) from e

    def check_unique_role(self, role: HubRole, l_nb: int,) -> None:
        """
        Ensure that START or END has not already been defined.
        Checks in already created hubs for the first (next) (duplicate) hub
        whose role matches the role we are looking for; if none exists,
        return None take the first value produced by the generator.

        Parameters
        ----------
        role : HubRole
            Hub role to check for duplicates.
        l_nb : int
            Line number of the new hub definition.

        Raises
        ------
        ValueError
            If a hub with the same special role already exists.
        """
        existing = next((hub for hub in self.hubs if hub.role == role), None)
        if existing is not None:
            raise ValueError(
                f"line {l_nb}: multiple {role.value}_hub zones; "
                f"{role.value}_hub already defined as "
                f"'{existing.name}' on line {existing.l_nb}")

    def hub_exists(self, hub: Hub) -> bool:
        """
        Check whether a hub with the same name already exists.

        Parameters
        ----------
        hub : Hub
            Hub to compare with existing hubs.

        Returns
        -------
        bool
            True if a hub with the same name exists, otherwise False.
        """
        for already in self.hubs:
            if already.name == hub.name:
                return True
        return False

    def connect_config(self, l_nb: int, attrs: list[str]) -> Connection:
        """
        Create and validate a connection from its configuration attributes.

        Parameters
        ----------
        l_nb : int
            Original line number in the map file.
        attrs : list[str]
            Connection endpoints and optional capacity metadata.

        Returns
        -------
        Connection
            Validated connection model.

        Raises
        ------
        ValueError
            If the connection syntax, endpoints, metadata, or capacity
            are invalid.
        """
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

        # model_validate() takes raw input, let Pydantic validate/convert it
        connection_data: dict[str, object] = {
            "l_nb": l_nb,
            "end1": end1,
            "end2": end2,
            **metadata,
        }
        try:
            return Connection.model_validate(connection_data)
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0]
            value = error.get("input")
            raise ValueError(
                f"line {l_nb}: invalid {field} value '{value}'"
            ) from e

    def connection_exists(self, connection: Connection) -> bool:
        """
        Check whether the same bidirectional connection already exists.

        Parameters
        ----------
        connection : Connection
            Connection to compare with existing connections.

        Returns
        -------
        bool
            True if the same connection exists in either direction,
            otherwise False.
        """
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
