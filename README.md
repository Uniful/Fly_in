*This project has been created as part of the 42 curriculum by jaockova.*

# Fly-in

## Description

Fly-in is a Python simulation project that routes a fleet of drones through a graph of interconnected zones from a unique start zone to a unique end zone.

The objective is to deliver all drones in as few simulation turns as possible while respecting:

- zone capacities (`max_drones`);
- connection capacities (`max_link_capacity`);
- normal, restricted, priority, and blocked zones;
- two-turn movement toward restricted zones;
- simultaneous movement and same-turn capacity release;
- valid scheduling without collisions or deadlocks.

The project is fully object-oriented and does not use external graph libraries. The map is parsed into typed models, routes are found with a custom Dijkstra-based pathfinding algorithm, drones are distributed between available routes, and a turn-by-turn simulator performs the movements.

## Instructions

### Requirements

- Python 3.10 or later
- `uv`
- project dependencies from `pyproject.toml`

Install dependencies with:

```bash
make install
```

Run the program directly with:

```bash
uv run python -m src <mapfile>
```

Example:

```bash
uv run python -m src maps/easy/01_linear_path.txt
```

The optional `--info` flag displays zone and connection capacity usage during the simulation:

```bash
uv run python -m src maps/easy/01_linear_path.txt --info
```

The flag may appear before or after the map path:

```bash
uv run python -m src --info maps/easy/01_linear_path.txt
```

The Makefile also provides:

```bash
make run
make debug
make clean
make lint
```

`make lint` runs the required `flake8` and `mypy` checks.

## Map format

A map starts with the number of drones, followed by zone definitions and bidirectional connections.

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: a 1 0 [color=blue]
hub: b 2 0 [color=yellow]
end_hub: goal 3 0 [color=red]

connection: start-a
connection: a-b
connection: b-goal
```

Zone metadata may contain `zone`, `max_drones`, and `color`. Connection metadata may contain `max_link_capacity`.

The default zone capacity and connection capacity are `1`. Start and end zones have unlimited occupancy.

## Algorithm explanation

### Parsing and validation

`MapLoader` reads the file while preserving line numbers. `MapParser` validates the syntax and creates typed Pydantic models for hubs, connections, and the complete map configuration.

Validation includes duplicate names and connections, valid metadata, integer coordinates, positive capacities, valid zone types, and exactly one start and one end zone.

### Graph representation

The `Graph` class builds an adjacency structure from the parsed map. Each hub stores its properties and capacities, and each connection directly references its two endpoint hubs.

No external graph library is used.

### Pathfinding

Routes are found with a custom implementation of Dijkstra's shortest-path algorithm.

| Destination zone | Cost |
| --- | ---: |
| normal | 1 turn |
| priority | 1 turn |
| restricted | 2 turns |
| blocked | inaccessible |

Priority zones keep their real movement cost of one turn. When two candidate paths have the same total cost, a separate priority score is used as a tie-breaker so that the path containing more priority zones is preferred.

The pathfinder also checks remaining zone and connection capacities. After a route is found, its residual capacity is reduced, and Dijkstra is run again to discover additional usable routes.

If no valid route from start to end exists at all, the program reports the map as unsolvable instead of running indefinitely.

### Drone distribution

The `Planner` distributes drones over the available routes. For each drone it compares:

```text
route cost + number of drones already assigned to the route
```

The drone is assigned to the route with the smallest estimate. This balances shorter paths against congestion.

### Turn scheduling

The `Simulator` works in discrete turns.

Before committing a turn, it first calculates a future position and future connection for each drone. This separates movement planning from movement execution.

Drones further along their routes are considered first so that downstream capacity can be released before drones behind them advance. When drones have the same progress, drones already travelling on a restricted connection are handled first, followed by drone ID as a deterministic tie-breaker.

Normal movement takes one turn.

Movement toward a restricted zone takes two turns:

1. the drone enters the connection;
2. on the next turn it must leave the connection and arrive in the restricted zone.

The simulator reserves future arrivals so that a drone does not enter a restricted connection unless there will be space in the destination zone. A restricted connection is released on the same turn that its current drone leaves it, allowing another drone to start crossing it immediately if capacity permits.

Zone and connection capacities are checked while planning every turn.

## Visual representation

The simulation uses ANSI terminal colors based on each zone's optional `color` metadata. This makes drone movement easier to follow, especially on maps with multiple paths.

Drones arriving in a zone are displayed using that zone's configured color. Connection movements use a neutral terminal color so that they remain visually distinct.


## Example input and expected output

### Input

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: a 1 0 [color=blue]
hub: b 2 0 [color=yellow]
end_hub: goal 3 0 [color=red]

connection: start-a
connection: a-b
connection: b-goal
```

### Expected output

ANSI color codes are omitted here for readability.

```text
D1-a
D1-b D2-a
D1-goal D2-b
D2-goal
```

The two drones form a pipeline through the route and all capacity rules remain satisfied.

With `--info`, additional capacity information is displayed for each turn.

## Project structure

```text
fly_in/
├── maps/
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── colors.py
│   ├── graph.py
│   ├── loader.py
│   ├── models.py
│   ├── parser.py
│   ├── planner.py
│   └── simulator.py
├── .gitignore
├── .python-version
├── Makefile
├── pyproject.toml
├── README.md
└── uv.lock
```

## Resources

- E. W. Dijkstra, *A note on two problems in connexion with graphs*, Numerische Mathematik, 1959.
- https://docs.astral.sh/uv/getting-started/
- https://github.com/evaristoc/fly-in-school-42
- https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- Python documentation: https://docs.python.org/3/
- Python `argparse` documentation: https://docs.python.org/3/library/argparse.html
- Pydantic documentation: https://docs.pydantic.dev/
- flake8 documentation: https://flake8.pycqa.org/
- mypy documentation: https://mypy.readthedocs.io/

### Use of AI

ChatGPT was used as a learning and debugging assistant during the project. It was used to discuss Python and Pydantic syntax, parser validation and error handling, Dijkstra design and priority tie-breaking, simulation edge cases involving zone and connection capacities, CLI behaviour, and documentation.

AI suggestions were reviewed, tested, and adapted to the project's architecture rather than being used as a replacement for understanding the implementation. The final code structure, implementation choices, testing, and debugging decisions were made and verified during development.
