from __future__ import annotations

import random
from os import listdir
from random import choice
from typing import TYPE_CHECKING, Generator, TypedDict

import pygame

if TYPE_CHECKING:
    from map_object import Map

VERSION = (6, 1, 0)

TILE_WIDTH = 16
TICK_RATE = 5
DESIRED_FPS = 30

ICON_SIZE = 32
BACKGROUND_COLOUR = (40, 40, 40)
NEIGHBOURS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class MapSettingsType(TypedDict):
    seed: int
    tree_density: int
    generate_lakes: bool
    generate_ruins: bool
    generate_biomes: bool
    map_width: int
    map_height: int
    starting_cash: int
    residential_tax_rate: int
    commercial_tax_rate: int
    industrial_tax_rate: int


STARTING_CASH = 50000
DEFAULT_MAP_SETTINGS: MapSettingsType = {
    "seed": random.randint(1, 100),
    "tree_density": 25,
    "generate_lakes": True,
    "generate_ruins": True,
    "generate_biomes": True,
    "map_width": 48,  # TODO: Change back to 48
    "map_height": 48,  # TODO: Change back to 48
    "starting_cash": STARTING_CASH,
    "residential_tax_rate": 10,
    "commercial_tax_rate": 10,
    "industrial_tax_rate": 10,
}


class DeleteEntity(Exception):
    pass


def rot_center(image: pygame.surface.Surface, angle: int) -> pygame.surface.Surface:
    """rotate a `Surface`, maintaining position."""
    if angle == 0:
        return image
    loc = image.get_rect().center
    rot_sprite = pygame.transform.rotate(image, angle)
    rot_sprite.get_rect().center = loc
    return rot_sprite


IMAGES: dict[str, pygame.surface.Surface] = {}
for image in listdir("images"):
    if image.endswith(".png"):
        IMAGES[image.removesuffix(".png")] = pygame.image.load("images/" + image)  # TODO: This: .convert_alpha()
for road_image in listdir("images/roads"):
    for rotation in [0, 90, 180, 270, 360]:
        IMAGES["roads/" + road_image.removesuffix(".png") + f"_rotation_{rotation}"] = rot_center(pygame.image.load("images/roads/" + road_image), rotation)
for entity_image in listdir("images/entities"):
    IMAGES["entities/" + entity_image.removesuffix(".png")] = pygame.image.load("images/entities/" + entity_image)

with open("name_list.txt", "r", encoding="utf-8") as file:
    people_names = file.read().split("\n")


def get_random_name() -> str:
    return choice(people_names)


def cursor_is_in_world(map: Map, window: pygame.surface.Surface, mouse_tile_x: int | None, mouse_tile_y: int | None) -> bool:
    return (
        mouse_tile_x is not None
        and mouse_tile_y is not None
        and mouse_tile_x < map.width
        and mouse_tile_y < map.height
        and mouse_tile_x >= 0
        and mouse_tile_y >= 0
        and mouse_tile_x < window.get_height() - ICON_SIZE  # Need offset and stuff
        and mouse_tile_y < window.get_width() - ICON_SIZE  # Need offset and stuff
    )


def clip(num: int | float, minimum: int, maximum: int) -> int:
    return min(max(num, minimum), maximum)  # type: ignore[return-value]


def get_neighbour_coords(map_width: int, map_height: int, x: int, y: int, include_void_tiles: bool = False) -> list[tuple[int, int] | tuple[int, int]]:
    neighbours: list[tuple[int, int] | tuple[int, int]] = []
    for x_neigh, y_neigh in NEIGHBOURS:
        if 0 <= x + x_neigh < map_height and 0 <= y + y_neigh < map_width:
            neighbours.append((x + x_neigh, y + y_neigh))
        elif include_void_tiles:
            neighbours.append((None, None))  # type: ignore[arg-type]
    return neighbours


def get_neighbouring_road_string(map: Map, x: int, y: int) -> str | None:  # DO NOT TYPE HINT THIS TILE
    tile = map[x, y]
    if tile.type.name == "Road":
        neighbours = get_neighbour_coords(map.width, map.height, x, y, include_void_tiles=True)
        neighbouring_roads = "".join(["0" if (_x is None or not map[_x, _y].road) else "1" for (_x, _y) in neighbours])
    else:
        neighbouring_roads = None
    return neighbouring_roads


def get_all_grid_coords(x1: int, y1: int, x2: int, y2: int, single_place: bool) -> Generator[tuple[int, int], None, None]:
    if single_place:
        top_left_x = x1
        top_left_y = y1
        bottom_right_x = x1
        bottom_right_y = y1
    else:
        top_left_x = min(x1, x2)
        top_left_y = min(y1, y2)
        bottom_right_x = max(x1, x2)
        bottom_right_y = max(y1, y2)

    # We always draw from top left to bottom right (like reading a book)
    # But a way to make single lines work is to mess with the step
    # When the step is 1000, the start will far exceed the end and it will
    # terminate the loop, allowing just one iteration.
    x_step = 1000 if top_left_x == bottom_right_x else 1
    y_step = 1000 if top_left_y == bottom_right_y else 1
    for x in range(top_left_x, bottom_right_x + 1, x_step):
        for y in range(top_left_y, bottom_right_y + 1, y_step):
            yield (x, y)


def get_class_properties(cls: object) -> list[str]:
    return [i for i in dir(cls) if not i.startswith("_")]


def reset_map(window: pygame.surface.Surface, map: Map) -> tuple[int, int]:
    map.check_connected()
    window.fill(BACKGROUND_COLOUR, rect=(0, 0, window.get_width()-ICON_SIZE, window.get_height()-ICON_SIZE))
    x_offset = window.get_width() // 2 - (TILE_WIDTH * map.width // 2) - TILE_WIDTH  # Center the world
    y_offset = window.get_height() // 2 - (TILE_WIDTH * map.height // 2) - TILE_WIDTH  # Center the world
    map.redraw_entire_map()
    return x_offset, y_offset


def convert_mouse_pos_to_coords(x: int, y: int, x_offset: int, y_offset: int) -> tuple[int, int]:
    return (x-x_offset) // TILE_WIDTH, (y-y_offset) // TILE_WIDTH


def coords_to_screen_pos(x: int, y: int, x_offset: int, y_offset: int) -> tuple[int, int]:
    return ((x * TILE_WIDTH)+x_offset, (y * TILE_WIDTH)+y_offset)  # [::-1]  # type: ignore[abc]

# ================================================================================================
