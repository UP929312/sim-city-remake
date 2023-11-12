from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING, TypedDict

import pygame

from utils import (ICON_SIZE, IMAGES, TILE_WIDTH, DeleteEntity,
                   get_random_name, rot_center)

if TYPE_CHECKING:
    from map_object import Map


# LOCATION_TYPES = ["Spawn", "House", "Shop", "Office", "Park"]

ROUTES = {
    "residential": [(1, "House", "Spawn"), (1, "Spawn", "House"), (3, "House", "Shop"), (3, "Shop", "House"), (1, "House", "Park"), (1, "Park", "House")],
    "commercial": [(1, "Shop", "Office"), (1, "Office", "Shop")],
    "industrial": [(3, "Spawn", "Shop"), (3, "Shop", "Spawn"), (2, "Shop", "Shop"), (2, "Shop", "Shop")],
}
ROUTES_CHANCES = {
    route_type: [(sum(x[0] for x in route_values[0:i]), route[1], route[2]) for i, route in enumerate(route_values, 1)] for route_type, route_values in ROUTES.items()
}  # Makes each route accumulative
LOCATION_TYPE = tuple[int, int]


def create_route(map: Map, route_type: str) -> tuple[None, None] | tuple[tuple[int, int] | None, tuple[int, int] | None]:
    routes = ROUTES_CHANCES[route_type]
    random_num = randint(1, routes[-1][0])

    for route in routes:
        if random_num <= route[0]:
            _, start_type, end_type = route
            break
    else:
        return None, None

    initial = map.get_random_tile_by_type(start_type)
    destination = map.get_random_tile_by_type(end_type)

    if initial == destination:
        return None, None

    return initial, destination


num_of_entity_sprites = {
    "Vehicle": len([x for x in IMAGES if x.startswith("entities/vehicle") and x[-1].isdigit()]),
    "Pedestrian": len([x for x in IMAGES if x.startswith("entities/pedestrian") and x[-1].isdigit()]),
}

rotated_entities_cache = {
    image_name.removeprefix("entities/")+f"_rotation_{rotation}": rot_center(image, rotation)
    for image_name, image in IMAGES.items() if image_name.startswith("entities/")
    for rotation in [0, 90, 180, 270]
}


class Entity:
    __slots__ = ("entity_subtype", "start", "end", "rotation", "current_loc", "x_offset", "y_offset", "path")
    max_path_length = 1500
    speed = 2
    direction_offsets = {"LEFT": (0, 0, 0)}

    def __init__(self, entity_subtype: str, map: Map, start: tuple[int, int], end: tuple[int, int], rainbow: bool = False, enforce_minimum_distance: bool = False, route: list[LOCATION_TYPE] | None = None) -> None:
        self.entity_subtype = randint(1, num_of_entity_sprites[self.__class__.__name__]) if rainbow else entity_subtype

        self.start = start
        self.end = end
        self.rotation = 0
        self.current_loc = start
        self.x_offset, self.y_offset = 5, 1  # We start the entities in the middle of the tile
        self.path = map.generate_route(start, end) if route is None else route
        
        if not (5 <= len(self.path) < self.__class__.max_path_length) and enforce_minimum_distance:
            # If the path is too short, or too long, delete the entity
            raise DeleteEntity

    def __str__(self) -> str:
        return f"{self.__class__.__name__} object (of type {self.entity_subtype}) from {self.start} to {self.end}"

    @staticmethod
    def try_create(class_type: type, map: Map, route_type: str, rainbow_entities_enabled: bool) -> None:
        start, end = create_route(map, route_type)
        if start is None or end is None:
            return
        # rint(f"Creating {class_type.__name__} from {start} to {end}")
        try:
            new_entity: Vehicle | Pedestrian = class_type(route_type, map, start, end, rainbow=rainbow_entities_enabled, enforce_minimum_distance=True)
        except DeleteEntity:
            return

        entity_list: list[Vehicle] | list[Pedestrian] = map.entity_lists[new_entity.__class__.__name__]  # type: ignore[literal-required]
        new_entity.update(map, entity_list)  # type: ignore[arg-type]
        entity_list.append(new_entity)  # type: ignore[arg-type]

    def update(self, map: Map, entity_list: list[Vehicle | Pedestrian]) -> tuple[int, int] | None:
        map[self.current_loc[0], self.current_loc[1]].redraw = True
        new_pos = self.make_move()
        if new_pos is None:  # If they've hit the end of their path
            if self in entity_list:
                entity_list.remove(self)  # type: ignore[arg-type]
            return None
        self.current_loc = new_pos
        return self.current_loc[0], self.current_loc[1]

    def draw(self, window: pygame.surface.Surface, x_offset: int, y_offset: int, view: str) -> None:
        if view not in ("general_view", "crazy_view", "colour_view"):
            return
        image = rotated_entities_cache[f"{self.__class__.__name__.lower()}_{self.entity_subtype}_rotation_{self.rotation}"]

        x_loc = (self.current_loc[0] * TILE_WIDTH) + self.x_offset + x_offset
        y_loc = (self.current_loc[1] * TILE_WIDTH) + self.y_offset + y_offset
        if x_loc < 0 or y_loc < 0 or x_loc > window.get_width()-ICON_SIZE or y_loc > window.get_height()-ICON_SIZE:
            return  # Don't draw anything off screen
        window.blit(image, (x_loc, y_loc))

    def make_move(self) -> None | tuple[int, int]:  # If they're at the end, it'll be None
        if not self.path:  # If they've reached the end
            return None

        self.rotation = 0
        self.x_offset = 0
        self.y_offset = 0

        new_position = self.path.pop(0)  # Used to give the inherited objects the next loc
        if new_position[0] < self.current_loc[0]:
            self.x_offset, self.y_offset, self.rotation = self.direction_offsets["LEFT"]
        elif new_position[0] > self.current_loc[0]:
            self.x_offset, self.y_offset, self.rotation = self.direction_offsets["RIGHT"]
        elif new_position[1] < self.current_loc[1]:
            self.x_offset, self.y_offset, self.rotation = self.direction_offsets["UP"]
        elif new_position[1] > self.current_loc[1]:
            self.x_offset, self.y_offset, self.rotation = self.direction_offsets["DOWN"]

        return new_position

    def on_arrive(self, map: Map) -> None:
        if self.entity_subtype == "FireEngine":
            # If a fire truck arrives, remove the fire, and send one home (if it's not already returning)
            map[self.end[0], self.end[1]].fire_ticks = None
            # If they're returning to station, they won't be in the on_route list
            if self in map.emergency_vehicles_on_route["FireStation"]:
                map.emergency_vehicles_on_route["FireStation"].remove(self)  # type: ignore[arg-type]
            if map[self.end[0], self.end[1]].type.name != "FireStation":
                new_fire_engine = Vehicle("FireEngine", map, self.end, self.start)
                map.entity_lists["Vehicle"].append(new_fire_engine)


class Vehicle(Entity):
    """
    A class representing a vehicle.

    Attributes:
        passengers (list): A list of Person objects representing the passengers in the vehicle.
        max_path_length (int): The maximum length of the path the vehicle can travel.
        speed (int): The speed of the vehicle.
        direction_offsets (dict): A dictionary mapping directions to their corresponding x, y, and rotation offsets.
    """

    __slots__ = ("passengers",)
    max_path_length = 1500
    speed = 2
    direction_offsets = {
        "LEFT":  (0, 9, 270),
        "RIGHT": (0, 0, 90),
        "UP":    (0, 0, 0),
        "DOWN":  (9, 0, 180),
    }

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """
        Initializes a Vehicle object.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.passengers = [Person() for _ in range(randint(1, 4))]

    def __repr__(self) -> str:
        """
        Returns a string representation of the Vehicle object.

        Returns:
            str: The string representation of the Vehicle object.
        """
        return f"{self.__class__.__name__}({self.start=}, {self.end=}, {len(self.path)=}, {[repr(x) for x in self.passengers]})"


class Person:
    """
    A class representing a person.
    """

    __slots__ = ("name", "age")

    def __init__(self) -> None:
        self.name = get_random_name()
        self.age = randint(18, 65)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name=}, {self.age=})"


class Pedestrian(Entity):
    __slots__ = ()
    max_path_length = 25
    speed = 6
    direction_offsets = {
        "LEFT":  (0, 13, 270),
        "RIGHT": (0, 2, 90),
        "UP":    (2, 0, 0),
        "DOWN":  (13, 0, 180),
    }


class Passenger(Person):
    __slots__ = ()
    """Does nothing now, but will be in a vehicle's "passenger" list"""


class EntityList(TypedDict):
    Vehicle: list[Vehicle]
    Pedestrian: list[Pedestrian]
