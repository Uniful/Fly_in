'''
adding __main__.py module to any Python package
to make that package directly executable
'''

import argparse
from .cli import parse_arguments
from .loader import Loader
from .models import MapConfig, Route
from .parser import Parser
from .graph import Graph
from .planner import Planner
from .simulator import Simulator


def main() -> None:
    args: argparse.Namespace = parse_arguments()
    print(args.mapfile)

    line_config: list[tuple[int, str, list[str]]] = []
    try:
        loader = Loader(args.mapfile)
        line_config = loader.load_map()
        parser = Parser(line_config)
        map_config: MapConfig = parser.parse_map()
        graph = Graph(map_config)
        # print(graph.adjacency)
        routes: list[Route] = []
        while True:
            try:
                new_route = graph.run()
            except ValueError:
                break
            routes.append(new_route)
        print()
        for route in routes:
            print([hub.name for hub in route.hubs])
            print([f"{c.end1.name}-{c.end2.name}" for c in route.connections])
            print(f"route cost: {route.cost}")
            print()
        plan = Planner(routes, map_config.nb_drones)
        plan.assign_drones()  # how many drones to each of the routes
        simulator = Simulator(map_config, routes)
        simulator.run()
        # see that all are arrived to the end hub:
        # for hub in map_config.hubs:
        #     print(simulator.hub_occupancy(hub))

    except Exception as e:
        print(f"Error: {e}")
        return
    # for lin in line_config:
    #     print(lin)
    # print()

    # for l_nb, typ, attrs in line_config:
    #     print(l_nb, typ, ":", attrs)

    # map_config: MapConfig = parse_map(line_config)


if __name__ == "__main__":
    main()
