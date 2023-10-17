import sys
from random import choice
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from classes import ROADS, Tile, grass
from entities import EntityList
from utils import MapSettingsType, get_neighbour_coords

sys.setrecursionlimit(1500)  # 1200 used to be the limit, now it's not

from pathfinding.core.grid import Grid  # type: ignore[import]
from pathfinding.finder.best_first import BestFirst  # type: ignore[import]

if TYPE_CHECKING:
    from entities import Vehicle

# map.road:
# 0 = Not a read
# 1 = A road but not connected to the main road
# 2 = Connected to the main road.

NO_ROAD = "No road!"
ROAD_NOT_CONNECTED = "Road not connected!"
SERVICE_VEHICLES = Literal["FireStation", "PoliceStation", "Hospital"]
COORD_TYPE = tuple[int, int]

finder = BestFirst()


class Map:
    def __init__(self, tiles: np.ndarray[tuple[int, int], Tile], cash: int, version: tuple[int, int, int], settings: MapSettingsType) -> None:  # type: ignore[type-var]
        self.tiles = tiles
        self.cash = cash
        self.version = version
        self.settings = settings

        self.entity_lists: EntityList = {"Vehicle": [], "Pedestrian": []}
        self.services: dict[SERVICE_VEHICLES, list[Vehicle]] = {
           "FireStation": [],
           "PoliceStation": [],
           "Hospital": [],
        }
        self.emergency_vehicles_on_route: dict[SERVICE_VEHICLES, list[Vehicle]] = {
            "FireStation": [],
            "PoliceStation": [],
            "Hospital": [],
        }
        self.route_cache: dict[tuple[COORD_TYPE, COORD_TYPE], list[COORD_TYPE]] = {}
        # The route cache maps start and end coords to their routes

    @property
    def width(self) -> int:
        return self.settings["map_width"]
    
    @property
    def height(self) -> int:
        return self.settings["map_height"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tiles": [[x.to_dict() for x in tile_list] for tile_list in self.tiles],
            "cash": self.cash,
            "version": self.version,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Map":
        one_dimension_tiles = [[Tile.from_dict(x) for x in tile_list] for tile_list in data["tiles"]]
        # set the value of redraw for each tile
        del data["tiles"]

        width, height = data["settings"]["map_width"], data["settings"]["map_height"]
        tiles = np.array(one_dimension_tiles).reshape(width, height)

        map = Map(tiles, **data)  # type: ignore[arg-type]
        map.redraw_entire_map()
        return map

    def __repr__(self) -> str:
        return f"Map({self.version}, {self.settings})"

    def __getitem__(self, key: tuple[int, int]) -> Tile:  # type: ignore[return]
        try:
            return self.tiles[key]  # type: ignore[no-any-return]
        except:
            print("ERROR", key)

    def __setitem__(self, key: tuple[int, int], value: Tile) -> None:
        self.tiles[key] = value

    def redraw_entire_map(self) -> None:
        for x in range(self.width):
            for y in range(self.height):
                self[x, y].redraw = True

    def generate_route(self, start: COORD_TYPE, end: COORD_TYPE) -> list[COORD_TYPE]:
        if (start, end) in self.route_cache:
            return self.route_cache[(start, end)]
        if (end, start) in self.route_cache:
            self.route_cache[(start, end)] = self.route_cache[(end, start)][::-1]
            return self.route_cache[(start, end)]
        matrix = np.array([
            [(self[x, y].type.name in ROADS or (x, y) in [start, end]) and self[x, y].fire_ticks is None
              for x in range(self.width)] for y in range(self.height)
        ])
        grid = Grid(matrix=matrix)
        start_node, end_node = grid.node(*start), grid.node(*end)
        path, _ = finder.find_path(start_node, end_node, grid)
        self.route_cache[(start, end)] = [(node.x, node.y) for node in path]
        return self.route_cache[(start, end)]

    def get_all_tiles_by_type(self, tile_type: str) -> list[COORD_TYPE] | None:
        return [(x, y) for x in range(self.width) for y in range(self.height) if self[x, y].type.name == tile_type and self[x, y].fire_ticks is None] or None

    def get_random_tile_by_type(self, tile_type: str) -> COORD_TYPE | None:
        if tile_type == "Spawn":
            return (0, self.height // 2)
        valid_tiles = self.get_all_tiles_by_type(tile_type)
        return choice(valid_tiles) if valid_tiles else None

    def get_neighbours(self, x: int, y: int) -> list[Tile]:
        neighbours: list[Tile] = []
        for x_neigh, y_neigh in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            if 0 <= x + x_neigh < self.width and 0 <= y + y_neigh < self.height:
                tile: Tile = self[x + x_neigh, y + y_neigh]
                neighbours.append(tile)
        return neighbours

    def update_neighbours(self, x: int, y: int) -> None:
        """Recursively expand in a depth first search spreading "actively connected" too all roads"""
        # This on very rare occasions can cause a maximum recursion depth error
        self[x, y].road = 2
        for _x, _y in get_neighbour_coords(self.width, self.height, x, y):
            if self[_x, _y].road == 1:
                self.update_neighbours(_x, _y)

    def update_road_map(self) -> None:
        for i in range(self.width):
            for j in range(self.height):
                self[i, j].road = 1 if self[i, j].type.name in ROADS else 0
        self.update_neighbours(0, self.width // 2)

    def check_connected(self) -> None:
        self.update_road_map()

        for x in range(self.width):
            for y in range(self.height):
                if not self[x, y].type.need_road:
                    continue

                # If at least one of the neighbours is a fully connected road
                if has_connected_road(self, x, y):
                    if NO_ROAD in self[x, y].error_list:
                        self[x, y].error_list.remove(NO_ROAD)
                    if ROAD_NOT_CONNECTED in self[x, y].error_list:
                        self[x, y].error_list.remove(ROAD_NOT_CONNECTED)
                # If at least one of the neighbours is an unconnected road
                elif has_neighbour_road(self, x, y):
                    if NO_ROAD in self[x, y].error_list:
                        self[x, y].error_list.remove(NO_ROAD)
                    if ROAD_NOT_CONNECTED not in self[x, y].error_list:
                        self[x, y].error_list.append(ROAD_NOT_CONNECTED)
                # None of the neighbours are roads at all.
                else:
                    if NO_ROAD not in self[x, y].error_list:
                        self[x, y].error_list.append(NO_ROAD)
                    if ROAD_NOT_CONNECTED not in self[x, y].error_list:
                        self[x, y].error_list.append(ROAD_NOT_CONNECTED)

    def calculate_nearest_services(self) -> None:
        pass
        """
        for service_name, service_list in self.services:
            for service_coords in service_list:
                pass
        """
    
    def expand(self) -> None:
        self.settings["map_width"] += 2
        self.settings["map_height"] += 2
        self.tiles = np.pad(self.tiles, 1, mode="edge")  # type: ignore[call-overload]
        for x in range(self.width):
            for y in range(self.height):
                if x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                    self[x, y] = Tile()
        self.redraw_entire_map()

def has_connected_road(map: Map, x: int, y: int) -> bool:
    return any(tile.road == 2 for tile in map.get_neighbours(x, y))


def has_neighbour_road(map: Map, x: int, y: int) -> bool:
    return any(tile.type.name == "Road" for tile in map.get_neighbours(x, y))
