# planner.py
"""Assign drones to available routes according to estimated route cost."""

from .models import Route


class Planner:
    """
    Distribute drones among the available routes.

    Drones are assigned greedily by comparing each route's path cost
    with the number of drones already assigned to it.

    Parameters
    ----------
    routes : list[Route]
        Available routes from the start hub to the end hub.
    nb_drones : int
        Total number of drones to distribute.
    """
    def __init__(self, routes: list[Route], nb_drones: int) -> None:
        """
        Initialize the route planner.

        Parameters
        ----------
        routes : list[Route]
            Available routes for drone assignment.
        nb_drones : int
            Number of drones to assign.
        """
        self.routes = routes
        self.nb_drones = nb_drones

    def assign_drones(self) -> None:
        """
        Assign all drones to routes using a greedy cost estimate.

        For each drone, the estimated route cost is calculated as the
        route movement cost plus the number of drones already assigned
        to that route. The drone is assigned to the route with the
        lowest estimate.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If no routes are available for drone assignment.
        """
        if not self.routes:
            raise ValueError("No routes available for drone assignment")
        for _ in range(self.nb_drones):
            estimated_cost: float = float("inf")
            best_route: Route = self.routes[0]
            for route in self.routes:
                estimating = route.cost + route.nb_drones
                if estimating < estimated_cost:
                    estimated_cost = estimating
                    best_route = route
            best_route.nb_drones += 1
        for i, route in enumerate(self.routes, start=1):
            print(f"nb of drones assigned to route {i}: {route.nb_drones}")
        print()
