# graph.py
"""Represent the Fly-In graph and find capacity-aware shortest routes."""

from .models import MapConfig, Connection, Hub, HubRole, ZoneType, Route


class Graph:
    """
    Represent the zone network and find routes through it.

    The graph uses an adjacency dictionary containing the connections
    associated with each hub. Routes are found using a Dijkstra-based
    shortest-path algorithm that also considers zone types, priority
    zones, and remaining hub and connection capacities.

    Parameters
    ----------
    config : MapConfig
        Validated map configuration containing hubs and connections.
    """
    def __init__(self, config: MapConfig) -> None:
        """
        Initialize the graph from a map configuration.

        Parameters
        ----------
        config : MapConfig
            Validated map configuration.
        """
        self.hubs: list[Hub] = config.hubs
        self.connections: list[Connection] = config.connections
        self.adjacency: dict[str, list[Connection]] = {}
        self.start: Hub | None = None
        self.end: Hub | None = None
        for hub in config.hubs:
            # create START/END hubs
            if hub.role == HubRole.START:
                self.start = hub
            elif hub.role == HubRole.END:
                self.end = hub
            # create ADJACENCY list of connections for each hub
            hub_connections: list[Connection] = []
            for connection in config.connections:
                if (hub.name == connection.end1.name
                        or hub.name == connection.end2.name):
                    hub_connections.append(connection)
            # A: [start-A, A-B]
            self.adjacency[hub.name] = hub_connections

    def neighbours(self, hub: str) -> list[Hub]:  # hub: "A"
        """
        Return all hubs directly connected to a given hub.

        Parameters
        ----------
        hub : str
            Name of the hub whose neighbours are requested.

        Returns
        -------
        list[Hub]
            Hubs connected to the given hub.

        Raises
        ------
        ValueError
            If the hub does not exist in the graph.
        """
        if hub not in self.adjacency:  # checking keys of dict
            raise ValueError(f"Hub '{hub}' does not exist")
        neighbours_list: list[Hub] = []
        for connection in self.adjacency[hub]:  # for connection in the list
            if hub == connection.end1.name:
                neighbours_list.append(connection.end2)  # append hub
            elif hub == connection.end2.name:
                neighbours_list.append(connection.end1)  # append hub
        return neighbours_list

    def init_distances(self) -> dict[str, float]:
        """
        Initialize Dijkstra distances for all hubs.

        The start hub receives a distance of zero and every other hub
        is initialized to infinity.

        Returns
        -------
        dict[str, float]
            Mapping of hub names to their initial distances.

        Raises
        ------
        ValueError
            If the graph has no start hub.
        """
        if self.start is None:
            raise ValueError("Graph has no start hub")
        distances: dict[str, float] = {}
        for hub in self.adjacency:
            if hub == self.start.name:
                distances[hub] = 0
            else:
                distances[hub] = float("inf")
        return distances

    def get_cost(self, zone: ZoneType) -> int | None:
        """
        Return the movement cost of entering a zone type.

        Parameters
        ----------
        zone : ZoneType
            Type of the destination zone.

        Returns
        -------
        int or None
            Movement cost in turns, or None if the zone is blocked.
        """
        if zone in (ZoneType.NORMAL, ZoneType.PRIORITY):
            return 1
        elif zone == ZoneType.RESTRICTED:
            return 2
        else:  # BLOCKED
            return None

    def get_hub(self, name: str) -> Hub:
        """
        Find a hub by name.

        Parameters
        ----------
        name : str
            Name of the requested hub.

        Returns
        -------
        Hub
            Hub with the requested name.

        Raises
        ------
        ValueError
            If no hub with the given name exists.
        """
        for hub in self.hubs:
            if name == hub.name:
                return hub
        raise ValueError(f"Hub '{name}' does not exist")

    def get_connection(self, hub1: str, hub2: str) -> Connection:
        """
        Find the bidirectional connection between two hubs.

        Parameters
        ----------
        hub1 : str
            Name of the first hub.
        hub2 : str
            Name of the second hub.

        Returns
        -------
        Connection
            Connection joining the two hubs.

        Raises
        ------
        ValueError
            If no connection exists between the hubs.
        """
        for connection in self.connections:
            if (
                (hub1 == connection.end1.name and hub2 == connection.end2.name)
                or
                (hub1 == connection.end2.name and hub2 == connection.end1.name)
            ):
                return connection
        raise ValueError(f"Connection '{hub1}'-'{hub2}' does not exist")

    def reconstruct_path(self,
                         previous: dict[str, str | None]) -> list[str]:
        """
        Reconstruct a shortest path as a list of hub names.

        Parameters
        ----------
        previous : dict[str, str | None]
            Mapping of each reached hub to its predecessor.

        Returns
        -------
        list[str]
            Hub names ordered from the start hub to the end hub.

        Raises
        ------
        ValueError
            If the graph has no start or end hub, or no complete path
            can be reconstructed.
        """
        if self.start is None or self.end is None:
            raise ValueError("Graph has no start or end hub")
        current: str = self.end.name
        start_end_path: list[str] = [current]
        while current != self.start.name:
            before = previous.get(current)  # starting current end.name
            if before is None:
                raise ValueError("No path from start to end")
            start_end_path.append(before)
            current = before
        # goal, path_b, juction, start
        start_end_path.reverse()
        # print(start_end_path)
        # start, junction, path_b, goal
        return start_end_path

    # change string-string path from dijkstra path to hubs
    def reconstruct_hubs(self,
                         previous: dict[str, str | None]) -> list[Hub]:
        """
        Reconstruct the route as Hub objects.

        Remaining capacity is decreased for each regular hub reserved
        by the reconstructed route. Start and end hub capacities are
        not reduced.

        Parameters
        ----------
        previous : dict[str, str | None]
            Mapping of each reached hub to its predecessor.

        Returns
        -------
        list[Hub]
            Hubs ordered from the start hub to the end hub.

        Raises
        ------
        ValueError
            If the graph has no start or end hub, or the path cannot
            be reconstructed.
        """
        if self.start is None or self.end is None:
            raise ValueError("Graph has no start or end hub")
        current: Hub = self.end
        start_end_hubs: list[Hub] = [current]
        while current != self.start:
            # starts current end.name:
            before: str | None = previous.get(current.name)
            if before is None:
                raise ValueError("No path from start to end")
            before_hub: Hub = self.get_hub(before)
            if (before_hub.remaining_capacity >= 1
                    and before_hub != self.start
                    and before_hub != self.end):
                before_hub.remaining_capacity -= 1
                # print(f"hub r backwards: {before_hub.remaining_capacity}")
            start_end_hubs.append(before_hub)
            current = before_hub
        start_end_hubs.reverse()
        return start_end_hubs

    # from dijkstra Hub path to Connection list
    def reconstruct_connections(self,
                                path_hubs: list[Hub]) -> list[Connection]:
        """
        Build the connection sequence for a reconstructed route.

        Remaining connection capacity is decreased for every connection
        reserved by the route.

        Parameters
        ----------
        path_hubs : list[Hub]
            Hubs forming the route from start to end.

        Returns
        -------
        list[Connection]
            Connections joining consecutive hubs in the route.
        """
        start_end_connections: list[Connection] = []
        for i in range(len(path_hubs) - 1):
            hub1 = path_hubs[i]
            hub2 = path_hubs[i + 1]
            connection = self.get_connection(hub1.name, hub2.name)
            if connection.remaining_capacity >= 1:
                connection.remaining_capacity -= 1
            start_end_connections.append(connection)
        return start_end_connections

    def run(self) -> Route | None:
        """
        Find the next available shortest route from start to end.
        start = current
        Dijkstra's algorithm is used with movement costs determined by
        destination zone type. Remaining hub and connection capacities
        are respected. When paths have the same cost, the path containing
        more priority zones is preferred.

        Returns
        -------
        Route or None
            The next available route, or None if no additional route
            can be found with the remaining capacities.

        Raises
        ------
        ValueError
            If the graph has no start or end hub.
        """
        if self.start is None or self.end is None:
            raise ValueError("Graph has no start or end hub")
        current: str = self.start.name  # just take a str name of Hub
        # start: 0.0, the rest: float("inf")
        distances: dict[str, float] = self.init_distances()
        priority_scores: dict[str, int] = {
            hub_name: 0 for hub_name in self.adjacency}
        previous: dict[str, str | None] = {self.start.name: None}
        visited: set[str] = set()
        # choose the next hub for the route
        while True:
            for neighbour in self.neighbours(current):
                # Hub/Connection capacity check (current, current-neighbour)
                if (neighbour.role == HubRole.REGULAR  # not checking start/end
                        and neighbour.remaining_capacity < 1):
                    continue
                connection = self.get_connection(current, neighbour.name)
                if connection.remaining_capacity < 1:
                    continue

                # calculate cost
                movement_cost = self.get_cost(neighbour.zone)
                if movement_cost is None:  # hub.zone is blocked
                    continue
                new_distance = distances[current] + movement_cost

                # increase priority score for current if zone.PRIORITY:
                new_priority: int = priority_scores[current]  # 0 initially
                if neighbour.zone == ZoneType.PRIORITY:
                    new_priority += 1

                # update "total distance from start" if cheaper  # b: 1.0
                # update "total priority score"  e.g. b: 2
                # set current to be previous if true
                if (new_distance < distances[neighbour.name]
                    or (new_distance == distances[neighbour.name]
                        and new_priority > priority_scores[neighbour.name])):
                    distances[neighbour.name] = new_distance
                    priority_scores[neighbour.name] = new_priority
                    previous[neighbour.name] = current
            visited.add(current)  # start hub added first

            # when end is reached
            if current == self.end.name:
                break

            # choose the next lowest from distances + prefer higher priority
            # 1st criterion: shortest n turns, 2nd: most priority hubs
            lowest_cost: float = float("inf")
            highest_priority: int = -1
            next_hub: str | None = None
            for hub_name, cost in distances.items():
                if hub_name in visited:
                    continue
                if cost == float("inf"):  # don't consider unreachable ones
                    continue
                if (cost < lowest_cost
                        or (cost == lowest_cost  # only those that were visited
                            # hub priority score initiated to 0 and 0 > -1
                            # don't consider unreachable nodes as candidates
                            and priority_scores[hub_name] > highest_priority)):
                    lowest_cost = cost
                    highest_priority = priority_scores[hub_name]
                    next_hub = hub_name
            # no hub was left, all visited, hub stayed empty:
            if next_hub is None:
                break
            current = next_hub
            # print(distances)
            # print(visited)
            # print(next_hub)

        # if the end is not included in the dict of route hubs:
        if self.end.name not in previous:
            return None
        # print(previous)
        self.reconstruct_path(previous)
        # path=self.reconstruct_path(previous)
        # print(path)
        path_hubs = self.reconstruct_hubs(previous)
        path_connections = self.reconstruct_connections(path_hubs)
        return Route(
            hubs=path_hubs,
            connections=path_connections,
            cost=int(distances[self.end.name]),
        )
