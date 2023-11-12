from __future__ import annotations

import random
from os import listdir
from random import choice
from typing import TYPE_CHECKING, Generator, TypedDict

import pygame

if TYPE_CHECKING:
    from map_object import Map

VERSION = (7, 1, 0)

TILE_WIDTH = 16
TICK_RATE = 5
DESIRED_FPS = 30

ICON_SIZE = 32
NEIGHBOURS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
TILE_EXPANSION_COST = 100


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


DEFAULT_MAP_SETTINGS: MapSettingsType = {
    "seed": random.randint(1, 100),
    "tree_density": 25,
    "generate_lakes": True,
    "generate_ruins": True,
    "generate_biomes": True,
    "map_width": 64,  # Change back to 48
    "map_height": 64,  # Change back to 48
    "starting_cash": 50000,
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


def generate_background_image(window: pygame.surface.Surface) -> pygame.surface.Surface:
    background_image = pygame.Surface((window.get_width()-ICON_SIZE, window.get_height()-ICON_SIZE))
    for x in range(0, background_image.get_width(), TILE_WIDTH):
        for y in range(0, background_image.get_height(), TILE_WIDTH):
            background_image.blit(IMAGES["out_of_bounds"], (x, y))
    return background_image


IMAGES: dict[str, pygame.surface.Surface] = {}
for images, subdirectory in [(listdir("images/icons"), "icons"), (listdir("images/tiles"), "tiles"), ([x for x in listdir("images/") if x.endswith(".png")], "")]:
    for image_name in images:
        IMAGES[image_name.removesuffix(".png")] = pygame.image.load(f"images/{subdirectory}/{image_name}")  # TODO: This: .convert()
for road_image in listdir("images/roads"):
    for rotation in [0, 90, 180, 270, 360]:
        IMAGES["roads/" + road_image.removesuffix(".png") + f"_rotation_{rotation}"] = rot_center(pygame.image.load("images/roads/" + road_image), rotation)
for entity_image in listdir("images/entities"):
    IMAGES["entities/" + entity_image.removesuffix(".png")] = pygame.image.load("images/entities/" + entity_image)


with open("name_list.txt", "r", encoding="utf-8") as file:
    people_names = file.read().split("\n")


def get_random_name() -> str:
    return choice(people_names)


def clip(num: int | float, minimum: int, maximum: int) -> int:
    return min(max(num, minimum), maximum)  # type: ignore[return-value]


def get_neighbour_coords(map_width: int, map_height: int, x: int, y: int, include_void_tiles: bool = False) -> list[tuple[int, int] | tuple[None, None]]:
    neighbours: list[tuple[int, int] | tuple[None, None]] = []
    for x_neigh, y_neigh in NEIGHBOURS:
        if 0 <= x + x_neigh < map_width and 0 <= y + y_neigh < map_height:
            neighbours.append((x + x_neigh, y + y_neigh))
        elif include_void_tiles:
            neighbours.append((None, None))
    return neighbours


def get_neighbouring_road_string(map: Map, x: int, y: int) -> str:
    neighbours = get_neighbour_coords(map.width, map.height, x, y, include_void_tiles=True)
    neighbouring_roads = "".join(["0" if (_x is None or not map[_x, _y].road) else "1" for (_x, _y) in neighbours])  # type: ignore[index]
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
    return [i for i in dir(cls) if not i.startswith("_") and i not in ["to_dict", "from_dict"]]


def convert_mouse_pos_to_coords(x: int, y: int, x_offset: int, y_offset: int, map: Map, window: pygame.surface.Surface) -> tuple[int, int] | tuple[None, None]:
    if x is None or y is None or x > (window.get_width() - ICON_SIZE*1.5) or y > (window.get_height() - ICON_SIZE*1.5):
        return None, None
    tile_x, tile_y = (x-x_offset) // TILE_WIDTH, (y-y_offset) // TILE_WIDTH
    if not (0 <= tile_x < map.width and 0 <= tile_y < map.height):
        return None, None
    return tile_x, tile_y


def coords_to_screen_pos(x: int, y: int, x_offset: int, y_offset: int) -> tuple[int, int]:
    return ((x * TILE_WIDTH)+x_offset, (y * TILE_WIDTH)+y_offset)

# ================================================================================================
