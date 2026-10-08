# simulator.py

from .models import MapConfig, Hub, Connection, Route, Drone

class Simulator:
    def __init__(self, config: MapConfig, routes: list[Route]) -> None:
        self.config = config
        self.routes = routes
        self.drones: list[Drone] = []
        self.turn = 0

    def create_drones(self) -> None:
        drone_id: int = 0
        for route in self.routes:
            for _ in range(route.nb_drones):
                drone_id += 1
                new_drone = Drone(id=drone_id, route=route, position=0)
                self.drones.append(new_drone)
        # for drone in self.drones:
        #     print(f"Drone {drone.id}: "
        #           f"route cost {drone.route.cost}, "
        #           f"position {drone.route.hubs[drone.position].name}")

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

    def is_hub_free(self, hub: Hub) -> bool:
        if hub.role in (HubRole.START, HubRole.END):
            return True
        return self.hub_occupancy(hub) < hub.max_capacity
        
    def is_connection_free(self, connection: Connection) -> bool:
        return self.connection_occupancy(connection) < connection.max_capacity
        

    def can_move(sefl, drone: Drone) -> bool:
        if not self.is_hub_free(next_hub):
            return False
        if not self.is_connection_free(connection):
            return False
        return True

    def move(self):
        for drone in self.drones:
            print(f"D{drone.id}-"
                  f"{drone.route.hubs[drone.position].name} ", end="")
        print()
        # how far is the drone from the end
        drones_to_move = sorted(
            self.drones,
            key=lambda drone: len(drone.route.hubs) - 1 - drone.position
        )
        
        for drone in drones_to_move:
            if drone.connection is not None:
                # finish transit
            else:
                # try normal movement

        for drone in drones_to_move:
            print(f"D{drone.id}-"
                  f"{drone.route.hubs[drone.position].name} ", end="")
        print()
