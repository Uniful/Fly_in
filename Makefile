# MAP ?= maps/easy/01_linear_path.txt
# MAP ?= maps/easy/02_simple_fork.txt
# MAP ?= maps/easy/03_basic_capacity.txt
# MAP ?= maps/medium/01_dead_end_trap.txt
# MAP ?= maps/medium/02_circular_loop.txt
MAP ?= maps/medium/03_priority_puzzle.txt
# MAP ?= maps/hard/01_maze_nightmare.txt
# MAP ?= maps/hard/02_capacity_hell.txt
# MAP ?= maps/hard/03_ultimate_challenge.txt
# MAP ?= maps/challenger/01_the_impossible_dream.txt

install:
	@echo "Installing dependencies..."
	uv sync

run:
	@echo "Running the main script..."
	uv run python -m src $(MAP)

# ask if a file needed here for debug
debug:
	@echo "Running in debug mode..."
	uv run python -m pdb -m src

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
# find .	Start searching from current directory
# -type d	Only find directories (not files)
# -name "__pycache__"	Only find folders named exactly __pycache__
# -exec rm -rf {} +	Add + all found folders and delete them at the same time
# {} is a placeholder for a name file e.g. src/__pycache__
# 2>/dev/null	Hide error messages
# || true	Don't fail if nothing found
# Why not rm -rf __pycache__ .mypy_cache .pytest_cache ? 
#     rm -rf __pycache__ deletes __pycache__ ONLY in the current directory
#     find command deletes __pycache__ in ALL subdirectories, also in llm_sdk

fclean:
	rm -rf .venv

lint:
	echo "Running flake8..."
	uv run flake8 src
	echo "Running mypy..."
	uv run mypy src 
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@echo "Running flake8..."
	uv run flake8 src
	@echo "Running mypy --strict..." 
	uv run mypy src --strict

help:
	@echo "Available targets:"
	@echo ""
	@echo " make install		- Install project dependencies"
	@echo " make run			- Run the main script"
	@echo " make debug			- Run in debug mode with pdb"
	@echo " make clean			- Remove temporary files and caches"
	@echo " make lint			- Run flake8 + mypy (normal)"
	@echo " make lint-strict	- Run flake8 + mypy --strict"
	@echo " make help			- Show this help message"

.PHONY: install run debug clean lint lint-strict