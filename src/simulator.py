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
        print(assigned)
        drone_id: int = 0  # 5 drones
        while drone_id < self.config.nb_drones:  # last one entering without id
            for i, route in enumerate(self.routes):  # assigns 
                # will assign 1 drone for each route [1][1], then [2][2], then [3][2]
                if assigned[i] < route.nb_drones:
                    drone_id += 1
                    new_drone = Drone(id=drone_id, route=route, position=0)
                    self.drones.append(new_drone)
                    assigned[i] += 1
                    if drone_id == self.config.nb_drones:
                        break

    def hub_occupancy(self, hub: Hub) -> int:
        drones_on_hub: int = 0
        for drone in self.drones:
            if (
                drone.connection is None
                and drone.route.hubs[drone.position] == hub
            ):
                drones_on_hub += 1
        return drones_on_hub

    def connection_occupancy(self, connection: Connection) -> int:
        drones_on_connection: int = 0
        for drone in self.drones:
            if drone.connection == connection:
                drones_on_connection += 1
        return drones_on_connection

    def hub_is_free(self, hub: Hub) -> bool:
        if hub.role in (HubRole.START, HubRole.END):
            return True
        return self.hub_occupancy(hub) < hub.max_capacity

    def connection_is_free(self, connection: Connection) -> bool:
        return self.connection_occupancy(connection) < connection.max_capacity

    def can_move(self, drone: Drone) -> bool:
        if not self.is_hub_free(next_hub):
            return False
        if not self.is_connection_free(connection):
            return False
        return True

    # def all_finished(self) -> bool:
    #     for drone in self.drones:
    #         if drone.position != len(drone.route.hubs) -1:
    #             return False
    #     return True

    def all_finished(self) -> bool:
        # return True if, for all drones,
        # if drone's position equals the index of the last hub
        return all(
            drone.position == len(drone.route.hubs) - 1
            for drone in self.drones
        )

    def print_output_line(self) -> None:
        for drone in self.drones:
            print(f"D{drone.id}-"
                  f"{drone.route.hubs[drone.position].name} ", end="")
        print()

    def move(self):
        # how far is the drone from the end
        drones_to_move: list[Drone] = sorted(
            self.drones,
            key=lambda drone: len(drone.route.hubs) - 1 - drone.position
        )
        for drone in drones_to_move:
            # next_connection: Connection
            if drone.position == len(drone.route.hubs) - 1:
                continue
            next_hub: Hub = drone.route.hubs[drone.position + 1]
            if (self.hub_is_free(next_hub)
                    and next_hub.zone != ZoneType.BLOCKED
                    and drone.position != len(drone.route.hubs) - 1):
                drone.position += 1

    def run(self) -> None:
        self.create_drones()

        while not self.all_finished():
            self.move()
            self.print_output_line()

        # for drone in drones_to_move:
        #     if drone.connection is not None:
        #         # finish transit
        #     else:
        #         # try normal movement

        # for drone in drones_to_move:
        #     print(f"D{drone.id}-"
        #           f"{drone.route.hubs[drone.position].name} ", end="")
        # print()
