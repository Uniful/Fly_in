# simulator.py

from .models import MapConfig, ZoneType, HubRole, Hub, Connection, Route, Drone
from .colors import Colors


class Simulator:
    def __init__(self,
                 config: MapConfig,
                 routes: list[Route],
                 show_info: bool = False) -> None:
        self.config = config
        self.routes = routes
        self.drones: list[Drone] = []
        self.show_info = show_info

    def create_drones(self) -> None:
        assigned: list[int] = [0] * len(self.routes)  # [0, 0] if 2 routes
        # print(assigned)
        drone_id: int = 0  # 5 drones
        while drone_id < self.config.nb_drones:  # last one entering without id
            for i, route in enumerate(self.routes):
                # will assign 1 drone for each route:
                # [1][1], then [2][2], then [3][2]
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

    # def connection_is_free(self, c: Connection) -> bool:
    #     return self.connection_occupancy(c) < c.max_capacity

    def all_finished(self) -> bool:
        # return True if, for all drones,
        # if drone's position equals the index of the last hub
        return all(
            drone.position == len(drone.route.hubs) - 1
            for drone in self.drones
        )

    def print_output_line(self,
                          n_turns: int,
                          moves: list[tuple[Drone, bool]]) -> None:
        print(f"{n_turns}: ", end="")
        for drone, entering_connection in moves:
            if entering_connection:
                # hub = drone.route.hubs[drone.position + 1]
                color_code = Colors.DEFAULT
                print(f"{color_code}"
                      f"D{drone.id}-"
                      f"{drone.route.connections[drone.position].name()} "
                      f"{Colors.RESET}", end="")
            else:
                hub = drone.route.hubs[drone.position]
                color_code = Colors.get(hub.color)
                print(f"{color_code}"
                      f"D{drone.id}-"
                      f"{hub.name} "
                      f"{Colors.RESET}", end="")
        print()

    # def print_output_line(self, n_turns: int) -> None:
    #     print(f"{n_turns}: ", end="")
    #     for d in self.drones:
    #         if d.arrived:
    #             continue
    #         if d.connection == None:
    #             if d.position == 0:
    #                 continue
    #             print(f"D{d.id}-"
    #                   f"{d.route.hubs[d.position].name} ", end="")
    #         else:
    #             print(f"D{d.id}-"
    #                   f"{d.route.connections[d.position].name()} ", end="")
    #     print()

    def free_slots_next_turn(self, hub: Hub) -> int:
        '''
        occupants = drones that will be on hub
        leaving = how many can leave next turn
        staying = occupants - leaving
        free = capacity - staying
        '''
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
            if (next_hub.role == HubRole.END
                    or self.hub_is_free(next_hub)):
                leaving += 1
                connection_uses[name] = used + 1
        staying = len(occupants) - leaving

        # protect against a negative result
        # capacity calculations should not return negative available places
        return max(0, hub.max_capacity - staying)

    def move_plan(self) -> list[tuple[Drone, bool]]:
        # reset future state to current state at the beginning of each turn
        for drone in self.drones:
            drone.future_position = drone.position
            drone.future_connection = drone.connection
        # key for sorted:
        # -drone.position: higher position first,
        # drone.connection is None: False comes before True,
        #   so drones already on a connection come first
        # drone.id: lower ID first when everything else is equal
        drones_to_move: list[Drone] = sorted(
            self.drones,
            key=lambda drone: (-drone.position,
                               drone.connection is None,
                               drone.id))
        # places promised in restricted hubs for the next turn
        reserved_arrivals: dict[str, int] = {}
        # normal one-turn uses of connections during this turn
        connection_uses: dict[str, int] = {}
        moves: list[tuple[Drone, bool]] = []
        for d in drones_to_move:
            # if drone already reached END
            if d.position == len(d.route.hubs) - 1:
                # to exclude arrived drone from tracking/printing:
                d.arrived = True
                continue
            next_connection: Connection = d.route.connections[d.position]
            next_hub: Hub = d.route.hubs[d.position + 1]
            connection_name = next_connection.name()
            # connection occupancy after already planned moves
            # +
            # normal crossings already approved during this turn
            used = (
                self.connection_occupancy(next_connection)
                + connection_uses.get(connection_name, 0)
            )
            # NORMAL MOVEMENT
            if next_hub.zone != ZoneType.RESTRICTED:
                if (next_hub.zone != ZoneType.BLOCKED
                        and used < next_connection.max_capacity
                        and self.hub_is_free(next_hub)):
                    d.future_position += 1
                    moves.append((d, False))
                    connection_uses[connection_name] = (
                        connection_uses.get(connection_name, 0) + 1
                    )
            # RESTRICTED MOVEMENT - next hub.zone is restricted
            else:
                # if drone sits on connection, just check if next hub is free:
                if d.connection is not None:
                    if self.hub_is_free(next_hub):  # must be free!!!
                        d.future_position += 1  # move to the next hub
                        d.future_connection = None  # free the connection
                        moves.append((d, False))
                    else:
                        print(f"D{d.id} more than 1 turn on a connection")
                else:  # drone not yet at the connection
                    reserved = reserved_arrivals.get(next_hub.name, 0)
                    free_next_turn = self.free_slots_next_turn(next_hub)
                    if (used < next_connection.max_capacity
                            and reserved < free_next_turn):
                        d.future_connection = next_connection
                        moves.append((d, True))
                        reserved_arrivals[next_hub.name] = reserved + 1
                    else:
                        print(f"D{d.id} stays at "
                              f"{d.route.hubs[d.position].name}")
        return moves

    def move(self, moves: list[tuple[Drone, bool]]) -> None:
        for d, _ in moves:
            d.position = d.future_position
            d.connection = d.future_connection
            # if entering_connection == True:
            #     d.connection = d.future_connection
            # else:
            #     d.position = d.future_position

    def print_capacity_info(
        self,
        n_turns: int,
        moves: list[tuple[Drone, bool]],
    ) -> None:
        hub_usage: dict[str, int] = {}
        connection_usage: dict[str, int] = {}

        # Current hub occupancy after the move
        for drone in self.drones:
            if drone.connection is None:
                hub = drone.route.hubs[drone.position]
                hub_usage[hub.name] = hub_usage.get(hub.name, 0) + 1

        # Connections used during this turn
        for drone, entering_connection in moves:
            if entering_connection:
                connection = drone.route.connections[drone.position]
            else:
                connection = drone.route.connections[drone.position - 1]

            name = connection.name()
            connection_usage[name] = connection_usage.get(name, 0) + 1

        print(f"{n_turns}: capacity usage")

        for route in self.routes:
            for hub in route.hubs:
                if hub.role == HubRole.REGULAR:
                    usage = hub_usage.get(hub.name, 0)
                    print(
                        f"Zone {hub.name}: "
                        f"{usage}/{hub.max_capacity} drones"
                    )

            for connection in route.connections:
                usage = connection_usage.get(connection.name(), 0)
                print(
                    f"Connection {connection.name()}: "
                    f"{usage}/{connection.max_capacity} capacity used"
                )

    def run(self) -> None:
        self.create_drones()
        n_turns: int = 0

        while not self.all_finished():
            moves: list[tuple[Drone, bool]] = self.move_plan()
            self.move(moves)
            n_turns += 1
            # self.print_output_line(n_turns)
            self.print_output_line(n_turns, moves)
            if self.show_info:
                self.print_capacity_info(n_turns, moves)
