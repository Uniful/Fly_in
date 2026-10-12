# planner.py

from .models import Route


class Planner:
    def __init__(self, routes: list[Route], nb_drones: int) -> None:
        self.routes = routes
        self.nb_drones = nb_drones

    def assign_drones(self) -> None:
        for _ in range(self.nb_drones):
            estimated_cost: float = float("inf")
            best_route: Route = self.routes[0]
            for i, route in enumerate(self.routes):
                estimating = route.cost + route.nb_drones
                if estimating < estimated_cost:
                    estimated_cost = estimating
                    best_route = route
            best_route.nb_drones += 1
        for i, route in enumerate(self.routes, start=1):
            print(f"nb of drones assigned to route {i}: {route.nb_drones}")
        print()
