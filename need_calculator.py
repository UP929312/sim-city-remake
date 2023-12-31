from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from map_object import Map

LENGTH_TO_CHECK = 6


# def get_array_slice(map: Map, x: int, y: int) -> np.ndarray[Any, np.dtype[Any]]:
#     return np.array([[map[x_offset + x, y_offset + y] for x_offset in range(-LENGTH_TO_CHECK, LENGTH_TO_CHECK)] for y_offset in range(-LENGTH_TO_CHECK, LENGTH_TO_CHECK)])


SERVICES: list[str] = ["Fire Station", "Hospital", "Police Station"]


"""
def update_nearby_service_list(map: Map, x: int, y: int) -> None:
    '''When a service/park is placed, we need to update all the zones in reach
    and add this to their service list'''
    # We have to stop routes longer than needed (outside the i by j area),
    # so we block everything *just* outside that
    bottom = -1 - LENGTH_TO_CHECK
    top = LENGTH_TO_CHECK + 1
    for x_offset in range(bottom, top + 1, 1):
        for y_offset in range(bottom, top + 1, 1):
            if x_offset in [bottom, top] or y_offset in [bottom, top]:
                x_pos, y_pos = x + x_offset, y + y_offset
                if 0 <= x_pos < map.width and 0 < y_pos < map.height:
                    map[x_pos, y_pos].temporarily_blocked = True

    # We then try to pathfind to every tile, if it's a service or park
    for x_offset in range(-LENGTH_TO_CHECK, LENGTH_TO_CHECK + 1, 1):
        for y_offset in range(-LENGTH_TO_CHECK, LENGTH_TO_CHECK + 1, 1):
            x_pos, y_pos = x + x_offset, y + y_offset
            if 0 <= x_pos < map.width and 0 < y_pos < map.height:
                tile = map[x_pos, y_pos]
                if tile.type.name in SERVICES + ["Park"]:
                    if map.generate_route((x, y), (x_pos, y_pos)):
                        map[x_pos, y_pos].nearby_amenities[tile.type.name] += 1

    map.unblock_all_tiles()

"""


def calculate_happiness(map: Map, x: int, y: int) -> int:
    return 5

    # nearby_parks = 0
    # nearby_services = {"FireStation": False, "Hospital": False, "PoliceStation": False}

    # has_water_neighbour = any(tile.type.name == "Water" for tile in map.get_neighbours(x, y))  # Waterfront property
    # has_grass_neighbour = any(tile.type.name == "Grass" for tile in map.get_neighbours(x, y))  # Nice big garden
    # has_cheap_taxes = map.settings["residential_tax_rate"] <= 0.1  # 10% Tax

    # """
    # for _x, _y in map.nearby_amenities:
    #     tile_type = map[_x, _y].type.name
    #     if tile_type in nearby_amenities.keys():
    #         nearby_services[tile_type] = True
    # """
    # # -------------------------------

    # #
    # map[x, y].happiness_reasons = {
    #     "has_water_neighbour": has_water_neighbour,
    #     "has_grass_neighbour": has_grass_neighbour,
    #     "has_cheap_taxes": has_cheap_taxes,
    #     "nearby_services": sum(nearby_services.values()),
    #     "nearby_parks": min(nearby_parks, 2),
    # }

    # # 1 for waterfront, 1 for big garden, up to 3 for unique services, up to 2 for two parks nearby
    # happiness = has_water_neighbour + has_grass_neighbour + has_cheap_taxes + sum(nearby_services.values()) + min(nearby_parks, 2)
    # return happiness


"""
def calculate_needs(world):
    counter_dict = {}

    residents = 0
    shops = 0
    jobs = 0
    water_amount = 0

    for x in range(MAP_WIDTH_TILES):
        for y in range(MAP_HEIGHT_TILES):
            if len(world[x, y].error_list) == 0:

                if world[x, y].type.name not in counter_dict:
                    counter_dict[world[x, y].type.name] = 0

                counter_dict[world[x, y].type.name] += 1

                if world[x, y].type in ("House", "Shop", "Office"):
                    if world[x, y].type == 'House':
                        residents += world[x, y].density

                    elif world[x, y].type == 'Shop':
                        shops += world[x, y].density

                    elif world[x, y].type == 'Office':
                        jobs += world[x, y].density

                    elif world[x, y].water > 0:
                        water_amount += world[x, y].water

    water_needed = (residents + shops + jobs) - (water_amount)

    errors = []
    if water_needed > 0:
        errors.append("Need more water (Water Tower)")

    total = residents + shops + jobs
    if residents < (0.625 * total):
        errors.append("Needs more jobs!")
    elif shops < (0.25 * total):
        errors.append("Need more shops!")
    elif jobs < (0.125 * total):
        errors.append("Need more jobs!")

    if len(errors) == 0:
        errors = ["All jobs satisfied"]

    return errors
"""

"""
def calcualte_cash():

    if counter % 60 == 0:
        calculate_cash()

    if jobs > residents:
        industrial_pay = residents
    if shops > residents:
        commercial_pay = residents
    if jobs < residents:
        residents_pay = jobs
    if shops < residents:
        residents_pay = shops

    cash_per_cycle = int(residents_pay + commercial_pay + industrial_pay * 0.5) + int(0.1 * residents) #Income sysytem
    cash_per_cycle = cash_per_cycle - int(counter_dict["Park"] * 50) - int(counter_dict["Fire station"] * 100) - int(counter_dict["Hospital"] * 100) - (counter_dict["Police station"] * 100)
    cash += cash_per_cycle

    return cash
"""

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
