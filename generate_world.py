import random

import numpy as np
from perlin_noise import PerlinNoise  # type: ignore[import]

from classes import (Tile, abandoned_tile, biome_to_tile, entry_road, lily_pad,
                     shrub, tree, weeds)
from map_object import Map
from utils import (DEFAULT_MAP_SETTINGS, VERSION, MapSettingsType, clip,
                   get_neighbour_coords)

FLOORING_TO_PLANT = {
    "Grass": tree,
    "Sand": shrub,
    "Dirt": weeds,
    "Gravel": weeds,
    "Water": lily_pad,
}


def generate_world(map_settings: MapSettingsType = DEFAULT_MAP_SETTINGS, seed: int | None = None) -> Map:
    map_width, map_height = map_settings["map_width"], map_settings["map_height"]
    world: np.ndarray[tuple[int, int], Tile] = np.array(  # type: ignore[assignment, type-var]
        [[Tile() for _ in range(map_width)] for _ in range(map_height)]
    )
    noise = PerlinNoise(octaves=2, seed=seed or map_settings["seed"])
    random.seed(seed or map_settings["seed"])

    for x in range(map_height):
        for y in range(map_width):
            world[x, y].biome = clip(noise([x/map_width, y/map_height]) * 3, -1, 1)
            world[x, y].type = biome_to_tile(world[x, y].biome, include_water=map_settings["generate_lakes"], even_generate=map_settings["generate_biomes"])

            if random.randint(1, 100) < map_settings["tree_density"]:
                floor_name = world[x, y].type.name
                if floor_name in FLOORING_TO_PLANT:
                    world[x, y].type = FLOORING_TO_PLANT[floor_name]

            # Water map
            # We generate 10 million on each water tile, knowing it'll be smoothed out+reduced by the next step
            world[x, y].water = 10_000_000 if world[x, y].type.name == "Water" else 0
    # ==================================================================
    # Generate water map
    for _ in range(10):  # 10x smoothing
        for x in range(map_height):
            for y in range(map_width):
                neighbours = get_neighbour_coords(map_width, map_height, x, y)
                total = sum(world[_x, _y].water for (_x, _y) in neighbours)  # Won't always have 4 neighbours
                world[x, y].water = int(clip(num=total / len(neighbours), minimum=0, maximum=255))
    # ==================================================================
    if map_settings["generate_ruins"]:
        for _ in range((map_width*map_height) // 144):
            x, y = random.randint(0, map_height - 1), random.randint(0, map_width - 1)
            if world[x, y].type.can_place_on:
                world[x, y].type = abandoned_tile

    world[0, map_height // 2].type = entry_road  # Set the entry road in

    map = Map(world, map_settings["starting_cash"], VERSION, map_settings)
    return map
