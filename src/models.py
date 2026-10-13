# src/models.py

from pydantic import BaseModel, Field, model_validator
from enum import Enum


class HubRole(str, Enum):
    START = "start"
    REGULAR = "regular"
    END = "end"


class ZoneType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Hub(BaseModel):
    l_nb: int
    role: HubRole = HubRole.REGULAR
    name: str  # start. junction1, deadend1, end, etc.
    x: int
    y: int
    zone: ZoneType = ZoneType.NORMAL
    max_capacity: int = Field(gt=0, default=1, alias='max_drones')
    remaining_capacity: int = 1
    color: str = "none"

    @model_validator(mode="after")
    def set_remaining_capacity(self) -> "Hub":
        self.remaining_capacity = self.max_capacity
        return self


class Connection(BaseModel):
    l_nb: int  # 5
    end1: Hub  # start
    end2: Hub  # junction1
    max_capacity: int = Field(gt=0, default=1, alias='max_link_capacity')
    remaining_capacity: int = 1

    @model_validator(mode="after")
    def set_remaining_capacity(self) -> "Connection":
        self.remaining_capacity = self.max_capacity
        return self

    def key(self) -> frozenset[str]:
        return frozenset({self.end1.name, self.end2.name})
    def name(self) -> str:
        return f"{self.end1.name}-{self.end2.name}"


class MapConfig(BaseModel):
    nb_drones: int = Field(gt=0)
    hubs: list[Hub] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_rules(self) -> 'MapConfig':
        '''checking if just one start and one end hub'''
        start_count = 0
        end_count = 0
        for hub in self.hubs:
            if hub.role == HubRole.START:
                start_count += 1
            elif hub.role == HubRole.END:
                end_count += 1
        if start_count != 1:
            raise ValueError(
                f"exactly one start_hub required, found {start_count}")
        if end_count != 1:
            raise ValueError(
                f"exactly one end_hub required, found {end_count}")
        return self


class Route(BaseModel):
    hubs: list[Hub]
    connections: list[Connection]
    cost: int
    nb_drones: int = 0


class Drone(BaseModel):
    id: int
    route: Route
    # position: intex in route.hubs
    # current hub is: drone.route.hubs[drone.position]
    position: int = 0
    future_position: int = 0
    connection: Connection | None = None
    future_connection: Connection | None = None
    arrived: bool = False
