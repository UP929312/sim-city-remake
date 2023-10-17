from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from utils import IMAGES, TILE_WIDTH  # , get_neighbour_coords

if TYPE_CHECKING:
    from file_manager import PreferencesType
    from map_object import Map

# from entities import Vehicle

# import time


"""
Plan:
We store every tile that has been checked, we also store a list of tiles that need to be checked,
otherwise we'll do depth first not breadth first.
Everytime we check a tile, we add it's neighbours to "to_check" if they've not already been checked.
"""

"""
def generate_service_routes(map: Map) -> None:
    '''
    First, we set all the fire stations to 0, then add all their neighbours' coords to the list
    If they're not fire stations themselves)
    '''
    checked = []
    to_check = []
    for x in range(map.width):
        for y in range(map.height):
            map[x, y].service_routes["FireStation"] = {"nearest_coords": None, "distance": None}
            if map[x, y].type == "FireStation":
                map[x, y].service_routes["FireStation"] = {"nearest_coords": (x, y), "distance": 0}
                to_check.append((x, y))
                checked.append((x, y))
                for tile in map.get_neighbours(x, y):
                    if tile.type != "FireStation" and (x, y) not in checked:
                        to_check.append((x, y))

    while to_check:
        for x, y in to_check:
            lowest_neighbour = min(
                [
                    map[x, y].service_routes["FireStation"]["distance"]
                    for x, y in get_neighbour_coords(map.width, map.height, x, y)
                    if (x, y) not in checked and map[x, y].service_routes["FireStation"]["distance"] is not None
                ]
            )
            if not lowest_neighbour:
                continue
            if (
                map[x, y].service_routes["FireStation"]["distance"] is None or map[x, y].service_routes["FireStation"]["distance"] < lowest_neighbour["distance"] + 1
            ):  # Maybe less than?
                map[x, y].service_routes["FireStation"] = {
                    "nearest_coords": lowest_neighbour,
                    "distance": lowest_neighbour["distance"] + 1,
                }
                checked.append((x, y))
            for _x, _y in get_neighbour_coords(map.width, map.height, x, y):
                if (_x, _y) not in checked:
                    to_check.append((_x, _y)
# """


def on_tick(map: Map, window: pygame.surface.Surface, preferences: PreferencesType, view: str, run_counter: int, x_offset: int, y_offset: int) -> None:
    """
    Runs every tick, updates the map and draws it to the screen
    """
    for x in range(map.width):
        for y in range(map.height):
            tile = map[x, y]
            if tile.redraw:
                tile.type.draw(window, map, x, y, view, old_roads=preferences["old_roads"], x_offset=x_offset, y_offset=y_offset)

            if view == "general_view" and len(tile.error_list) > 0:
                window.blit(IMAGES["errorsquare"].convert_alpha(), (x * TILE_WIDTH+x_offset, y * TILE_WIDTH+y_offset))
                tile.redraw = True

            if run_counter % 4 and tile.vehicle_heatmap > 0:
                tile.vehicle_heatmap -= 1
                if view == "heatmap_view":
                    tile.redraw = True

            if tile.fire_ticks is not None:
                tile.redraw = True
                tile.fire_ticks += 1
            """
                # Check if any fire trucks are on route, if not, create one
                on_route = any(fire_engine.end==(x, y) for fire_engine in map.emergency_vehicles_on_route["FireStation"])
                if not on_route:
                    nearest_fire_station_route = min(
                        [
                            map[_x, _y].service_routes["FireStation"] for _x, _y in get_neighbour_coords(map.width, map.height, x, y) if
                            map[_x, _y].service_routes["FireStation"] != None
                        ],
                        key=lambda x: len(x)
                    )
                    if nearest_fire_station_route:
                        new_entity = Vehicle("FireEngine", map, nearest_fire_station_route[0], (x, y), enforce_minimum_distance=False, route=nearest_fire_station_route)
                        map.emergency_vehicles_on_route["FireStation"].append(new_entity)
            #"""
