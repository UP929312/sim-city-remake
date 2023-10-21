from random import randint

import numpy as np

from classes import (Tile, abandoned_tile, biome_to_tile, entry_road, grass,
                     lily_pad, shrub, tree, weeds)
from map_object import Map
from utils import (DEFAULT_MAP_SETTINGS, VERSION, MapSettingsType, clip,
                   get_neighbour_coords)


# Probably a modified version of https://pvigier.github.io/2018/06/13/perlin-noise-numpy.html
def generate_perlin_noise_2d(width: int, height: int, res: tuple[int, int]) -> np.ndarray[tuple[int, int], Tile]:  # type: ignore[type-var]
    """Returns a size by size matrix in the range of -1 to 1"""

    if width % 4 in [1, 2, 3]:
        raise TypeError(f"Width {width} is not allowed")

    delta = (res[0] / width, res[1] / height)
    d = (width // res[0], height // res[1])
    grid = np.mgrid[0 : res[0] : delta[0], 0 : res[1] : delta[1]].transpose(1, 2, 0) % 1  # type: ignore[misc]
    # Gradients
    angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)
    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)
    # Interpolation
    t = 6 * grid**5 - 15 * grid**4 + 10 * grid**3
    n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
    n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
    return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)  # type: ignore[no-any-return]


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

    np.random.seed(seed or map_settings["seed"])
    noise = generate_perlin_noise_2d(map_width, map_height, (4, 4))  # Default 8, 8

    for x in range(map_width):
        for y in range(map_height):
            world[x, y].biome = noise[x, y]

            if map_settings["generate_biomes"]:
                world[x, y].type = biome_to_tile(noise[x, y], include_water=map_settings["generate_lakes"])
            else:
                world[x, y].type = grass

            # Water map
            # We generate 10 million on each water tile, knowing it'll be smoothed out+reduced by the next step
            world[x, y].water = 10_000_000 if world[x, y].type.name == "Water" else 0

    # ==================================================================
    # Generate water map
    for _ in range(10):  # 10x smoothing
        for x in range(map_width):
            for y in range(map_height):
                neighbours = get_neighbour_coords(map_width, map_height, x, y)
                total = sum(world[_x, _y].water for (_x, _y) in neighbours)  # Won't always have 4 neighbours
                world[x, y].water = int(clip(num=total / len(neighbours), minimum=0, maximum=255))
    # ==================================================================
    # Tree generation
    for _ in range(map_settings["trees"]):
        x, y = randint(0, map_width - 1), randint(0, map_height - 1)
        # Now get the right type of tree, e.g. shrub, weeds, etc
        floor_name = world[x, y].type.name
        if floor_name in FLOORING_TO_PLANT:
            world[x, y].type = FLOORING_TO_PLANT[floor_name]

    if map_settings["generate_ruins"]:
        for _ in range(15):
            x, y = randint(0, map_width - 1), randint(0, map_height - 1)
            if world[x, y].type.name not in ["Water", "LilyPad"]:
                world[x, y].type = abandoned_tile

    world[0, map_height // 2].type = entry_road  # Set the entry road in

    map = Map(world, map_settings["starting_cash"], VERSION, map_settings)
    return map
