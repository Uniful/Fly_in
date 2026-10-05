'''
adding __main__.py module to any Python package
to make that package directly executable
'''

from .cli import parse_arguments
from .loader import load_map
from .parser import parse_map
from .graph import Graph


def main() -> None:
    args: argparse.Namespace = parse_arguments()
    print(args.mapfile)

    line_config: list[tuple[int, str, list[str]]] = []
    try:
        line_config = (load_map(args.mapfile))
        map_config: MapConfig = parse_map(line_config)
        graph = Graph(map_config)
        # print(graph.adjacency)
        routes: list[Route] = []
        excluded: set = set()
        route = graph.run(excluded)
        routes.append(route)
        print()
        excluded = {"path_a", "path_aa"}
        route = graph.run(excluded)
        routes.append(route)
        for route in routes:
            print([hub.name for hub in route.hubs])
            print([f"{c.end1.name}-{c.end2.name}" for c in route.connections])
            print(route.cost)
    except (FileNotFoundError, ValueError, Exception) as e:
        print(f"Error: {e}")
        return
    # for dick in line_config:
    #     print(dick)
    # print()

    # for l_nb, typ, attrs in line_config:
    #     print(l_nb, typ, ":", attrs)

    # map_config: MapConfig = parse_map(line_config)

if __name__ == "__main__":
    main()