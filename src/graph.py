# graph.py

from .models import MapConfig, Connection, Hub, HubRole, ZoneType, Route

class Graph:
    def __init__(self, config: MapConfig) -> None:
        self.hubs: list[Hub] = config.hubs
        self.connections: list[Connection] = config.connections
        self.adjacency: dict[str, list[Connection]] = {}
        self.start: Hub | None = None
        self.end: Hub | None = None
        for hub in config.hubs:
            if hub.role == HubRole.START:
                self.start = hub
            elif hub.role == HubRole.END:
                self.end = hub
            hub_connections: list[Connection] = []
            for connection in config.connections:
                if (hub.name == connection.end1.name
                or hub.name == connection.end2.name):
                    hub_connections.append(connection)
            # A: [start-A, A-B]
            self.adjacency[hub.name] = hub_connections

    def neighbours(self, hub: str) -> list[Hub]:  # hub: "A"
        if hub not in self.adjacency:
            raise ValueError(f"Hub '{hub}' does not exist")
        neighbours_list: list[Hub] = []
        for connection in self.adjacency[hub]:  # connection list for "A"
            if hub == connection.end1.name:
                neighbours_list.append(connection.end2)
            elif hub == connection.end2.name:
                neighbours_list.append(connection.end1)
        return neighbours_list

    def init_distances(self) -> dict[str, float]:
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
        if zone in (ZoneType.NORMAL, ZoneType.PRIORITY):
            return 1
        elif zone == ZoneType.RESTRICTED:
            return 2
        else:  # BLOCKED
            return None

    def get_hub(self, name: str) -> Hub:
        for hub in self.hubs:
            if name == hub.name:
                return hub
        raise ValueError(f"Hub '{name}' does not exist")

    def get_connection(self, hub1: str, hub2: str) -> Connection:
        for connection in self.connections:
            if (
            (hub1 == connection.end1.name and hub2 == connection.end2.name)
            or
            (hub1 == connection.end2.name and hub2 == connection.end1.name)):
                return connection
        raise ValueError(f"Connection '{hub1}'-'{hub2}' does not exist")

    def reconstruct_path(self, 
            previous: dict[str, str | None]) -> list[str]:
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
        if self.start is None or self.end is None:
            raise ValueError("Graph has no start or end hub")
        current: Hub = self.end
        start_end_hubs: list[Hub] = [current]
        while current != self.start:
            before: str = previous.get(current.name)  # starting current end.name
            if before is None:
                raise ValueError("No path from start to end")
            before_hub: Hub = self.get_hub(before)
            if before_hub.remaining_capacity >= 1 and before_hub != self.start and before_hub != self.end:
                before_hub.remaining_capacity -= 1
                print(f"hub r backwards: {before_hub.remaining_capacity}")
            start_end_hubs.append(before_hub)
            current = before_hub
        start_end_hubs.reverse()
        return start_end_hubs

    # from dijkstra Hub path to Connection list
    def reconstruct_connections(self,
            path_hubs: list[Hub]) -> list[Connection]:
        start_end_connections: list[Connection] = []
        for i in range(len(path_hubs) - 1):
            hub1 = path_hubs[i]
            hub2 = path_hubs[i + 1]
            connection = self.get_connection(hub1.name, hub2.name)
            if connection.remaining_capacity >= 1:
                print(f"connection r before: {connection.remaining_capacity}")
                connection.remaining_capacity -= 1
                print(f"connection r: {connection.remaining_capacity}")
                print(f"{connection.end1.name}-{connection.end2.name}")
                print()
            start_end_connections.append(connection)
        return start_end_connections

    def run(self) -> Route:
        '''
        find the shortest path from start to end considering distances
        start = current
        '''
        if self.start is None or self.end is None:
            raise ValueError("Graph has no start or end hub")
        current: str = self.start.name  # just take a name of Hub
        # start: 0.0, the rest: float("inf")
        distances: dict[str, float] = self.init_distances()
        previous: dict[str, str | None] = {self.start.name: None}
        visited: set[str] = set()
        while True:
            # for Hub in list of its neighbouring hubs, check capacity
            for neighbour in self.neighbours(current):
                if (neighbour.role == HubRole.REGULAR
                        and neighbour.remaining_capacity < 1):
                    continue
                connection = self.get_connection(current, neighbour.name)
                if connection.remaining_capacity < 1:
                    continue

                movement_cost = self.get_cost(neighbour.zone)
                if movement_cost is None:  # hub.zone is blocked
                    continue
                new_distance = distances[current] + movement_cost
                # update distance from start if cheaper  # b: 1.0
                if new_distance < distances[neighbour.name]:
                    distances[neighbour.name] = new_distance
                    previous[neighbour.name] = current

            visited.add(current)
            # when end is reached
            if current == self.end.name:
                break
            # choose the next lowest from distances
            lowest: float = float("inf")
            next_hub: str | None = None
            for hub_name, cost in distances.items():
                if hub_name in visited:
                    continue
                if cost < lowest:
                    lowest = cost
                    next_hub = hub_name
            # no hub was left, all visited, hub stayed empty:
            if next_hub is None:
                break
            current = next_hub
            # print(distances)
            # print(visited)
            # print(next_hub)
        # print(previous)
        path=self.reconstruct_path(previous)
        print(path)
        path_hubs=self.reconstruct_hubs(previous)
        path_connections=self.reconstruct_connections(path_hubs)
        return Route(
            hubs=path_hubs,
            connections=path_connections,
            cost=int(distances[self.end.name]),
        )

        
        
            
