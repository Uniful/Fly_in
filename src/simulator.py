# simulator.py

from .models import MapConfig, ZoneType, HubRole, Hub, Connection, Route, Drone


class Simulator:
    def __init__(self, config: MapConfig, routes: list[Route]) -> None:
        self.config = config
        self.routes = routes
        self.drones: list[Drone] = []
        self.turn = 0

    def create_drones(self) -> None:
        assigned: list[int] = [0] * len(self.routes)  # [0, 0] if 2 routes
        # print(assigned)
        drone_id: int = 0  # 5 drones
        while drone_id < self.config.nb_drones:  # last one entering without id
            for i, route in enumerate(self.routes):  # assigns 
                # will assign 1 drone for each route [1][1], then [2][2], then [3][2]
                if assigned[i] < route.nb_drones:
                    drone_id += 1
                    new_drone = Drone(id=drone_id, route=route)
                    self.drones.append(new_drone)
                    assigned[i] += 1
                    if drone_id == self.config.nb_drones:
                        break

    def hub_occupancy(self, hub: Hub) -> int:
        drones_on_hub: int = 0
        for drone in self.drones:
            if (
                drone.future_connection is None
                and drone.route.hubs[drone.future_position] == hub
            ):
                drones_on_hub += 1
        return drones_on_hub

    def connection_occupancy(self, connection: Connection) -> int:
        drones_on_connection: int = 0
        for drone in self.drones:
            if drone.future_connection == connection:
                drones_on_connection += 1
        return drones_on_connection

    def hub_is_free(self, hub: Hub) -> bool:
        if hub.role in (HubRole.START, HubRole.END):
            return True
        return self.hub_occupancy(hub) < hub.max_capacity

    def connection_is_free(self, connection: Connection) -> bool:
        return self.connection_occupancy(connection) < connection.max_capacity

    def can_move(self, drone: Drone, connection: Connection, next_hub: Hub) -> bool:
        if not self.hub_is_free(next_hub):
            return False
        if not self.connection_is_free(connection):
            return False
        return True

    def all_finished(self) -> bool:
        # return True if, for all drones,
        # if drone's position equals the index of the last hub
        return all(
            drone.position == len(drone.route.hubs) - 1
            for drone in self.drones
        )

    def print_output_line(self, n_turns: int) -> None:
        print(f"{n_turns}: ", end="")
        for drone in self.drones:
            if drone.position == 0 or drone.arrived:
                continue
            if drone.connection == None:
                print(f"D{drone.id}:"
                      f"{drone.route.hubs[drone.position].name} ", end="")
            else:
                print(f"D{drone.id}:"
                      f"{drone.route.connections[drone.position].name()} ", end="")
        print()

    def free_slots_next_turn(self, hub: Hub) -> int:
        # START and END are unlimited
        if hub.role in (HubRole.START, HubRole.END):
            return self.config.nb_drones
        occupants: list[Drone] = []

        # who will be on this hub at the end of CURRENT turn?
        for drone in self.drones:
            if (
                drone.future_connection is None
                and drone.route.hubs[drone.future_position] == hub
            ):
                occupants.append(drone)

        leaving = 0
        connection_uses: dict[str, int] = {}

        # check how many of these drones could leave NEXT turn
        for drone in occupants:
            if drone.future_position == len(drone.route.hubs) - 1:
                continue

            connection = drone.route.connections[drone.future_position]
            next_hub = drone.route.hubs[drone.future_position + 1]

            if next_hub.zone == ZoneType.BLOCKED:
                continue

            name = connection.name()
            used = connection_uses.get(name, 0)

            if used >= connection.max_capacity:
                continue

            # for now: END is always available,
            # otherwise require destination capacity
            if (
                next_hub.role == HubRole.END
                or self.hub_is_free(next_hub)
            ):
                leaving += 1
                connection_uses[name] = used + 1

        staying = len(occupants) - leaving

        return hub.max_capacity - staying

    def move_plan(self) -> list[tuple[Drone, bool]]:
        for drone in self.drones:
            drone.future_position = drone.position
            drone.future_connection = drone.connection
        # how far is the drone from the end
        drones_to_move: list[Drone] = sorted(
            self.drones,
            key=lambda drone: len(drone.route.hubs) - 1 - drone.position
        )
        reserved_arrivals: dict[str, int] = {}
        connection_uses: dict[str, int] = {}
        moves: list[tuple[Drone, bool]] = []
        for drone in drones_to_move:
            # if hub at the the end:
            if drone.position == len(drone.route.hubs) - 1:
                # to exclude arrived drone from tracking/printing:
                drone.arrived = True
                continue
            next_connection: Connection = drone.route.connections[drone.position]
            next_hub: Hub = drone.route.hubs[drone.position + 1]
            if next_hub.zone != ZoneType.RESTRICTED:
                connection_name = next_connection.name()
                used = (
                    self.connection_occupancy(next_connection)
                    + connection_uses.get(connection_name, 0)
                )
                if (next_hub.zone != ZoneType.BLOCKED
                    and used < next_connection.max_capacity
                    and self.connection_is_free(next_connection)
                    and self.hub_is_free(next_hub)):
                    drone.future_position += 1
                    moves.append((drone, False))
                    connection_uses[connection_name] = (
                        connection_uses.get(connection_name, 0) + 1
                    )
            else:  # next hub.zone is RESTRICTED
                # if drone sits on connection, just check if next hub is free:
                if drone.connection is not None:
                    if self.hub_is_free(next_hub):  # must be free!!!
                        drone.future_position += 1  # move to the next hub
                        drone.future_connection = None  # free the connection
                        moves.append((drone, False))
                    else:
                        print(f"drone {drone.id} more than one turn on the connection")
                else:  # drone not yet at the connection
                    reserved = reserved_arrivals.get(next_hub.name, 0)
                    free_next_turn = self.free_slots_next_turn(next_hub)

                    if (self.connection_is_free(next_connection)
                        and reserved < free_next_turn):
                        drone.future_connection = next_connection
                        moves.append((drone, True))
                        reserved_arrivals[next_hub.name] = reserved + 1
                    else:
                        print(f"D{drone.id} stays at {drone.route.hubs[drone.position].name}")
        return moves

    def move(self, drones_allowed_to_move: list[tuple[Drone, bool]]) -> None:
        for drone, _ in drones_allowed_to_move:
            drone.position = drone.future_position
            drone.connection = drone.future_connection
            # if entering_connection == True:
            #     drone.connection = drone.future_connection
            # else:
            #     drone.position = drone.future_position

    def run(self) -> None:
        self.create_drones()
        n_turns: int = 0

        while not self.all_finished():
            drones_allowed_to_move: dict = self.move_plan()
            self.move(drones_allowed_to_move)
            n_turns += 1
            self.print_output_line(n_turns)

