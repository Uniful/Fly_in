# simulator.py
"""Simulate turn-by-turn drone movement through the Fly-In network."""

from .models import MapConfig, ZoneType, HubRole, Hub, Connection, Route, Drone
from .colors import Colors


class Simulator:
    """
    Simulate drone movement along assigned routes.

    The simulator plans all movements using future positions before
    committing a turn. It enforces hub and connection capacities,
    handles two-turn movement toward restricted zones, and produces
    visual terminal output.

    Parameters
    ----------
    config : MapConfig
        Parsed map configuration.
    routes : list[Route]
        Routes with drones assigned by the planner.
    show_info : bool, optional
        Whether to display hub and connection capacity usage.
    """
    def __init__(self,
                 config: MapConfig,
                 routes: list[Route],
                 show_info: bool = False) -> None:
        """
        Initialize the simulator.

        Parameters
        ----------
        config : MapConfig
            Parsed map configuration.
        routes : list[Route]
            Routes available to the drones.
        show_info : bool, optional
            Enable capacity information output.

        Returns
        -------
        None
        """
        self.config = config
        self.routes = routes
        self.drones: list[Drone] = []
        self.show_info = show_info

    def create_drones(self) -> None:
        """
        Create drones and assign them to their planned routes.

        Drone identifiers are distributed across the routes according to
        the number of drones previously assigned to each route by the
        planner.

        Returns
        -------
        None
        """
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
        """
        Count drones planned to occupy a hub after the current turn.

        Parameters
        ----------
        hub : Hub
            Hub whose future occupancy is requested.

        Returns
        -------
        int
            Number of drones whose planned future state is on the hub.
        """
        drones_on_hub: int = 0
        for drone in self.drones:
            if (
                drone.future_connection is None
                and drone.route.hubs[drone.future_position] == hub
            ):
                drones_on_hub += 1
        return drones_on_hub

    def connection_occupancy(self, connection: Connection) -> int:
        """
        Count drones planned to remain on a connection after the turn.

        This is mainly used for drones travelling toward restricted zones,
        where crossing the connection requires more than one turn.

        Parameters
        ----------
        connection : Connection
            Connection whose future occupancy is requested.

        Returns
        -------
        int
            Number of drones whose future connection is the given connection.
        """
        drones_on_connection: int = 0
        for drone in self.drones:
            if drone.future_connection == connection:
                drones_on_connection += 1
        return drones_on_connection

    def hub_is_free(self, hub: Hub) -> bool:
        """
        Check whether a hub can accept another drone.

        Start and end hubs are treated as having unlimited occupancy.

        Parameters
        ----------
        hub : Hub
            Hub to check.

        Returns
        -------
        bool
            True if another drone may enter the hub, otherwise False.
        """
        if hub.role in (HubRole.START, HubRole.END):
            return True
        return self.hub_occupancy(hub) < hub.max_capacity

    # def connection_is_free(self, c: Connection) -> bool:
    #     return self.connection_occupancy(c) < c.max_capacity

    def hub_usage(self) -> None:
        """
        Update the current occupancy stored in every hub.

        Existing occupancy values are reset before counting drones whose
        committed state is currently on a hub.

        Returns
        -------
        None
        """
        # reset occupancy
        for hub in self.config.hubs:
            hub.occupancy = 0
        # count current drones in hubs
        for drone in self.drones:
            if drone.connection is None:
                hub = drone.route.hubs[drone.position]
                hub.occupancy += 1

    def connection_usage(
            self, moves: list[tuple[Drone, bool]]) -> None:
        """
        Update connection capacity usage for the current turn.

        Normal one-turn traversals and drones ending the turn on restricted
        connections are counted. A drone leaving a restricted connection is
        not counted because that connection is freed during the same turn.

        Parameters
        ----------
        moves : list[tuple[Drone, bool]]
            Approved movements for the turn. The boolean is True when the
            drone ends the turn on a restricted connection and False when
            it arrives at a hub.

        Returns
        -------
        None
        """
        # reset occupancy
        for connection in self.config.connections:
            connection.occupancy = 0
        # count current drones on connection:
        for drone, entering_connection in moves:
            if entering_connection:
                # drone finishes this turn ON the restricted connection
                c = drone.route.connections[drone.position]
                c.occupancy += 1
            else:
                hub = drone.route.hubs[drone.position]
                # Normal 1-turn connection traversal
                if hub.zone != ZoneType.RESTRICTED:
                    c = drone.route.connections[drone.position - 1]
                    c.occupancy += 1

    def all_finished(self) -> bool:
        """
        Check whether all drones have reached their destination hubs.

        Returns
        -------
        bool
            True if every drone is at the final hub of its route.
        """
        # return True if, for all drones,
        # if drone's position equals the index of the last hub
        return all(
            drone.position == len(drone.route.hubs) - 1
            for drone in self.drones
        )

    def print_output_line(self,
                          n_turns: int,
                          moves: list[tuple[Drone, bool]]) -> None:
        """
        Print the drone movements performed during one simulation turn.

        Zone arrivals are displayed using the configured zone color, while
        movements on restricted connections use the default terminal color.

        Parameters
        ----------
        n_turns : int
            Current simulation turn number.
        moves : list[tuple[Drone, bool]]
            Drone movements approved for the current turn.

        Returns
        -------
        None
        """
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

    def free_slots_next_turn(self, hub: Hub) -> int:
        """
        Estimate how many places will be available in a hub next turn.

        The method considers drones expected to occupy the hub after the
        current turn and estimates how many of them can leave during the
        following turn. This is used before allowing drones to enter a
        restricted connection.
        occupants = drones that will be on hub
        leaving = how many can leave next turn
        staying = occupants - leaving
        free = capacity - staying

        Parameters
        ----------
        hub : Hub
            Destination hub whose future capacity is evaluated.

        Returns
        -------
        int
            Estimated number of available places in the hub next turn.
        """
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
        """
        Plan all drone movements for the next simulation turn.

        Current drone states are first copied into future states. Drones are
        then considered according to movement priority, while hub capacity,
        connection capacity, blocked zones, restricted movement, and future
        restricted-zone reservations are taken into account.

        No current drone state is committed by this method.

        Returns
        -------
        list[tuple[Drone, bool]]
            Approved movements. Each tuple contains the drone and a boolean
            indicating whether it ends the turn on a restricted connection.
        """
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
                    # else:
                    #     print(f"D{d.id} stays at "
                    #           f"{d.route.hubs[d.position].name}")
        return moves

    def move(self, moves: list[tuple[Drone, bool]]) -> None:
        """
        Commit the movements planned for the current turn.

        Each moving drone's future position and connection become its
        current state. Hub occupancy and connection usage are then updated.

        Parameters
        ----------
        moves : list[tuple[Drone, bool]]
            Movements approved by `move_plan`.

        Returns
        -------
        None
        """
        for d, _ in moves:
            d.position = d.future_position
            d.connection = d.future_connection
        self.hub_usage()
        self.connection_usage(moves)

    def print_capacity_info(self) -> None:
        """
        Print hub occupancy and connection usage information.

        The information reflects the committed drone positions and
        connection capacity used during the current simulation turn.

        Returns
        -------
        None
        """
        for hub in self.config.hubs:
            print(
                f"Zone {hub.name}: "
                f"{hub.occupancy}/{hub.max_capacity} drones"
            )
        for connection in self.config.connections:
            print(
                f"Connection {connection.name()}: "
                f"{connection.occupancy}/{connection.max_capacity} "
                "capacity used"
            )
        print()

    def run(self) -> None:
        """
        Run the simulation until every drone reaches the end hub.

        Drones are created first. Each turn then consists of planning the
        movements, committing them, printing the movement output, and
        optionally displaying capacity information.

        Returns
        -------
        None
        """
        self.create_drones()
        n_turns: int = 0

        while not self.all_finished():
            moves: list[tuple[Drone, bool]] = self.move_plan()
            self.move(moves)
            n_turns += 1
            self.print_output_line(n_turns, moves)
            if self.show_info:
                self.print_capacity_info()
