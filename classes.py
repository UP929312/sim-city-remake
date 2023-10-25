from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

import pygame

# from need_calculator import calculate_happiness
# from utils import rot_center)
from utils import (DESIRED_FPS, ICON_SIZE, IMAGES, TILE_WIDTH,
                   coords_to_screen_pos, get_neighbouring_road_string)

COLOUR_TYPE = tuple[int, int, int]

if TYPE_CHECKING:
    from entities import Person
    from map_object import Map


class GenericTile:

    __slots__ = ("name", "cost", "cost_to_remove", "can_place_on", "need_road", "single_place", "icon",
                 "general_view_image", "quality_view", "density_view", "base_colour", "random_rotation")

    def __init__(
        self,
        cost: int | None = 0,
        cost_to_remove: int | None = 0,
        can_place_on: bool | None = False,
        need_road: bool = False,
        single_place: bool = False,
        base_colour: tuple[int, int, int] = (200, 80, 200),
        random_rotation: bool = False,
    ) -> None:
        self.name = self.__class__.__name__
        self.cost = cost
        self.cost_to_remove = cost_to_remove
        self.can_place_on = can_place_on
        self.need_road = need_road
        self.single_place = single_place

        self.icon = self.__class__.__name__.lower() + "_icon"

        self.general_view_image = self.__class__.__name__.lower()
        self.quality_view = (200, 80, 200)
        self.density_view = (200, 80, 200)

        self.base_colour = base_colour
        self.random_rotation = random_rotation

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return self.name + " Tile"

    # =============================================================================
    # DRAWING
    def draw(self, window: pygame.surface.Surface, map: Map, x: int, y: int, view: str, old_roads: bool, x_offset: int, y_offset: int) -> None:
        x_pos, y_pos = pos = coords_to_screen_pos(x, y, x_offset, y_offset)
        if not (0 <= x_pos < window.get_width()-ICON_SIZE-TILE_WIDTH and 0 <= y_pos < window.get_height()-ICON_SIZE):
            return
        map[x, y].redraw = False

        if view == "general_view":
            general_image = self.get_general_view_texture(map, x, y, old_roads)
            window.blit(general_image, pos)
            if map[x, y].fire_ticks is not None:
                window.blit(IMAGES["fire"].convert_alpha(), pos)
            if len(map[x, y].error_list) > 0:
                window.blit(IMAGES["errorsquare"].convert_alpha(), pos)
            return
        if view == "crazy_view":
            return  # Crazy works by just letting things draw over each other.

        func = getattr(self, "draw_" + view)
        tile_colour = func(map[x, y])
        pygame.draw.rect(window, tile_colour, (*pos, TILE_WIDTH, TILE_WIDTH))

    def get_general_view_texture(self, map: Map, x: int, y: int, old_roads: bool) -> pygame.Surface:  # Leave types for typing.
        return IMAGES[self.general_view_image].convert_alpha()
        # return rot_center(IMAGES[self.general_view_image].convert_alpha(), 0 if not self.random_rotation else 90*((x*1111 + y*3)%4))

    def draw_nearest_services(self, _: Tile) -> COLOUR_TYPE:
        return self.base_colour

    def draw_density_view(self, tile: Tile) -> COLOUR_TYPE:
        density = tile.density
        if self.name == "House":
            tile_type_format = (0, density * 25, 0)
        elif self.name == "Shop":
            tile_type_format = (0, 0, density * 25)
        elif self.name == "Office":
            tile_type_format = (density * 25, density * 25, 0)
        elif self.name in ROADS:
            tile_type_format = (50, 50, 50)
        else:
            tile_type_format = (20, 20, 20)
        return tile_type_format

    def draw_quality_view(self, tile: Tile) -> COLOUR_TYPE:
        tile_type_format = (50, 50, 50) if self.name in ROADS else (20, 20, 20)

        quality = tile.quality

        if quality is not None:
            if self.name == "House":
                tile_type_format = (0, quality * 25, 0)
            elif self.name == "Shop":
                tile_type_format = (0, 0, quality * 25)
            elif self.name == "Office":
                tile_type_format = (quality * 25, quality * 25, 0)

        return tile_type_format

    def draw_fire_view(self, _: Tile) -> COLOUR_TYPE:
        return self.base_colour

    def draw_hospital_view(self, _: Tile) -> COLOUR_TYPE:
        return self.base_colour

    def draw_police_view(self, _: Tile) -> COLOUR_TYPE:
        return self.base_colour

    def draw_colour_view(self, _: Tile) -> COLOUR_TYPE:
        return self.base_colour

    def draw_heatmap_view(self, _: Tile) -> COLOUR_TYPE:
        return (0, 0, 0)

    def draw_happiness_view(self, _: Tile) -> COLOUR_TYPE:
        return (10, 10, 10)

    def draw_water_view(self, tile: Tile) -> COLOUR_TYPE:
        return (0, 0, tile.water)

    # =============================================================================
    # PLACING
    def on_place(self, map: Map, x: int, y: int) -> None:
        place_on_type = map[x, y].type
        if self.cost is not None and map.cash < self.cost:
            return print("classes:", f"Cannot afford a {self.name}, it costs {self.cost}")

        if not place_on_type.can_place_on:
            return  # rint("classes:", f"Cannot place {self.name} on {place_on_type.name}")

        if place_on_type.name == self.name:
            return  # rint("classes:", f"The tile there is already a {self.name}")

        assert self.cost is not None
        map.cash -= self.cost
        map[x, y].type = self

    def on_matrix_place(self, map: Map) -> None:
        pass

    # =============================================================================
    # DESTROYING
    def on_destroy(self, map: Map, x: int, y: int) -> None:
        if self.cost_to_remove is None:
            return  # rint("classes:", f"{map[x, z].type.name} can't be removed")

        if map.cash < self.cost_to_remove:
            return  # rint("classes:", f"Not enough money to remove {map[x, z].type.name}")

        map.cash -= self.cost_to_remove
        map[x, y].type = biome_to_tile(map[x, y].biome)

    def on_matrix_destroy(self, map: Map) -> None:
        pass

    # =============================================================================
    # RANDOM TICK
    def on_random_tick(self, map: Map, x: int, y: int) -> None:
        if map[x, y].fire_ticks is not None and map[x, y].fire_ticks >= DESIRED_FPS * 10:  # type: ignore[operator]
            map[x, y].type = abandoned_tile
            map[x, y].fire_ticks = None
        map[x, y].redraw = True

    # =============================================================================


# =============================================================================
# ROADS


class GenericRoad(GenericTile):
    __slots__ = ()
    def on_destroy(self, map: Map, x: int, y: int) -> None:
        super().on_destroy(map, x, y)
        for entity_name in map.entity_lists.keys():
            map.entity_lists[entity_name] = [  # type: ignore[literal-required]
                entity for entity in map.entity_lists[entity_name]  # type: ignore[literal-required]
                if not any(cell == (x, y) for cell in entity.path if cell)
            ]


class Road(GenericRoad):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=50, cost_to_remove=25, base_colour=(50, 50, 50))

    def on_destroy(self, map: Map, x: int, y: int) -> None:
        super().on_destroy(map, x, y)
        # Delete all the cached routes that pass through this tile
        for key, route_list in {k: v for k, v in map.route_cache.items()}:  # Copy dictionary
            if (x, y) in route_list:  # type: ignore[comparison-overlap]
                del map.route_cache[key]  # type: ignore[arg-type]

    def on_matrix_destroy(self, map: Map) -> None:
        pass
        # map.regenerate_pathfinding_matrix_cache()

    def on_place(self, map: Map, x: int, y: int) -> None:
        super().on_place(map, x, y)
        # Delete all the cached routes that pass through this tile
        for key, route_list in {k: v for k, v in map.route_cache.items()}:  # Copy dictionary
            if (x, y) in route_list:  # type: ignore[comparison-overlap]
                del map.route_cache[key]  # type: ignore[arg-type]

    def on_matrix_place(self, map: Map) -> None:
        pass
        # map.regenerate_pathfinding_matrix_cache()

    def get_general_view_texture(self, map: Map, x: int, y: int, old_roads: bool) -> pygame.Surface:  # type: ignore[return]
        if old_roads:
            return IMAGES["roads/road_rotation_0"]
        else:
            neighbour_string = get_neighbouring_road_string(map, x, y)  # Returns something like 1011 = 3 neighours
            assert neighbour_string is not None
            for i, string in enumerate([neighbour_string[i:4] + neighbour_string[0:i] for i in range(4)]):
                final_string = "roads/" + string+f"_rotation_{360+i*-90}"
                if final_string in IMAGES:
                    return IMAGES[final_string]

    def draw_heatmap_view(self, tile: Tile) -> COLOUR_TYPE:
        value = tile.vehicle_heatmap
        if value > 20:
            return (value, 0, 0)
        else:
            return (20, 20, 20)


class EntryRoad(GenericRoad):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=None, cost_to_remove=None, base_colour=(50, 50, 50))


# =============================================================================
# ZONES


class Zoning(GenericTile):
    __slots__ = ("turns_to",)
    def __init__(self, base_colour: tuple[int, int, int], turns_to: GenericTile) -> None:
        super().__init__(cost=0, cost_to_remove=0, can_place_on=True, need_road=True, base_colour=base_colour)
        self.turns_to = turns_to

    def on_random_tick(self, map: Map, x: int, y: int) -> None:
        super().on_random_tick(map, x, y)
        if random.randint(1, 25) == 1 and map[x, y].road >= 2:
            map[x, y].type = self.turns_to


class HouseZoning(Zoning):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(base_colour=(0, 100, 0), turns_to=House())


class ShopZoning(Zoning):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(base_colour=(0, 100, 0), turns_to=Shop())


class OfficeZoning(Zoning):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(base_colour=(0, 100, 0), turns_to=Office())


# -----------------------------------------------------------------------------
# ZONED BUILDINGS


class GenericZonedBuilding(GenericTile):  # ################################
    __slots__ = ()
    def __init__(self, base_colour: tuple[int, int, int]) -> None:
        super().__init__(cost=0, need_road=True, base_colour=base_colour)

    def draw_happiness_view(self, tile: Tile) -> COLOUR_TYPE:
        happiness = tile.happiness or 0
        return (10, 25 * happiness, 10)

    def on_random_tick(self, map: Map, x: int, y: int) -> None:
        # rint(f"Random tick for {self.__class__.__name__}")
        """
        for service_type in ["FireStation", ]:
            all_tiles = map.get_all_tiles_by_type(service_type)
            #rint(all_tiles)
            if all_tiles:
                rint("Found all the tiles")
                shortest_route = min([map.generate_route((x, y), tile) for tile in all_tiles], key=lambda x: len(x))
                if shortest_route:
                    rint("New shortest route)")
                    map[x, y].service_routes[service_type] = shortest_route
        #"""
        # map[x, y].happiness = calculate_happiness(map, x, y)
        # map[x, y].density += 1


class House(GenericZonedBuilding):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(base_colour=(0, 100, 0))


class Shop(GenericZonedBuilding):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(base_colour=(0, 0, 160))


class Office(GenericZonedBuilding):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(base_colour=(160, 160, 0))


# =============================================================================
# SERVICES


class ServiceTile(GenericTile):
    __slots__ = ()
    def on_place(self, map: Map, x: int, y: int) -> None:
        super().on_place(map, x, y)
        if (x, y) in map.services[self.__class__.__name__]:  # type: ignore # No idea how this happens, but this is a safety net
            map.services[self.__class__.__name__].append((x, y))  # type: ignore[arg-type, index]

    def on_destroy(self, map: Map, x: int, y: int) -> None:
        super().on_destroy(map, x, y)
        if (x, y) in map.services[self.__class__.__name__]:  # type: ignore # No idea how this happens, but this is a safety net
            map.services[self.__class__.__name__].remove((x, y))  # type: ignore[arg-type, index]


class FireStation(ServiceTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=500, cost_to_remove=100, single_place=True, need_road=True, base_colour=(100, 0, 0))

    def draw_fire_view(self, *_) -> COLOUR_TYPE:  # type: ignore[no-untyped-def]
        colour = (255, 0, 0)
        return colour


class Hospital(ServiceTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=500, cost_to_remove=100, single_place=True, need_road=True, base_colour=(150, 150, 150))

    def draw_hospital_view(self, *_) -> COLOUR_TYPE:  # type: ignore[no-untyped-def]
        colour = (255, 255, 255)
        return colour


class PoliceStation(ServiceTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=500, cost_to_remove=100, single_place=True, need_road=True, base_colour=(0, 0, 150))

    def draw_police_view(self, *_) -> COLOUR_TYPE:  # type: ignore[no-untyped-def]
        colour = (0, 0, 255)
        return colour


# =============================================================================
# THE REST


class AbandonedTile(GenericTile):
    def __init__(self) -> None:
        super().__init__(cost=None, cost_to_remove=1000, base_colour=(111, 78, 34), random_rotation=True)  # Brown


class Grass(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=10, cost_to_remove=None, can_place_on=True, base_colour=(0, 75, 0), random_rotation=True)


class Dirt(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=500, cost_to_remove=None, can_place_on=True, base_colour=(50, 50, 0), random_rotation=True)

    def on_place(self, map: Map, x: int, y: int) -> None:
        place_on_type: GenericTile = map[x, y].type
        if place_on_type.name not in ["Water", "LilyPad"]:
            return  # rint("build:", "Can only place dirt on water or lily pads!")

        # The cost will always be an int here
        if map.cash < self.cost:  # type: ignore[operator]
            return  # rint("build:", "Not enough money to fill in water")

        # The cost will always be an int here
        map.cash -= self.cost  # type: ignore[operator]
        map[x, y].type = self

    def on_random_tick(self, map: Map, x: int, y: int) -> None:
        super().on_random_tick(map, x, y)
        # if any(neighbour_tile.type.name == "Grass" for neighbour_tile in map.get_neighbours(x, y)):
        #    map[x, y].type = Grass()   # Grow grass on dirt if there is grass nearby


class Sand(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=None, cost_to_remove=None, can_place_on=True, base_colour=(180, 150, 36), random_rotation=True)


class Gravel(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=None, cost_to_remove=None, can_place_on=True, base_colour=(33, 33, 33), random_rotation=True)


class Water(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=100, cost_to_remove=None, base_colour=(0, 0, 100), random_rotation=True)


class LilyPad(Water):  # Inherit from Water
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__()
        self.cost = None


class Tree(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=50, can_place_on=True, base_colour=(0, 50, 0))


class Shrub(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=None, can_place_on=True, base_colour=(50, 50, 0))


class Weeds(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=None, can_place_on=True, base_colour=(50, 50, 0), random_rotation=True)


class Park(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=100, cost_to_remove=25, single_place=True, need_road=True, base_colour=(0, 80, 0))


class WaterTower(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=100, single_place=True, need_road=True, base_colour=(0, 0, 100))

    def draw_water_view(self, _) -> COLOUR_TYPE:  # type: ignore[no-untyped-def]
        colour = (255, 255, 255)
        return colour

    def on_place(self, map: Map, x: int, y: int) -> None:
        if map[x, y].water < 1:  # If there's no water
            return print("classes:", f"{self.name} can only be placed where there is water!")
        super().on_place(map, x, y)


class WindTurbine(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__(cost=1000, single_place=True, need_road=True, base_colour=(100, 100, 100))


class Unzone(GenericTile):
    __slots__ = ()
    def __init__(self) -> None:
        super().__init__()

    def on_place(self, map: Map, x: int, y: int) -> None:
        if map[x, y].type.name in ZONES:
            map[x, y].type = biome_to_tile(map[x, y].biome)


ALL_TILES = [
    (road := Road()),
    (entry_road := EntryRoad()),
    (house := House()),
    (shop := Shop()),
    (office := Office()),
    (house_zoning := HouseZoning()),
    (shop_zoning := ShopZoning()),
    (office_zoning := OfficeZoning()),
    (abandoned_tile := AbandonedTile()),
    (fire_station := FireStation()),
    (hospital := Hospital()),
    (police_station := PoliceStation()),
    (unzone := Unzone()),
    (park := Park()),
    (water_tower := WaterTower()),
    (wind_turbine := WindTurbine()),
    (water := Water()),
    (lily_pad := LilyPad()),
    (tree := Tree()),
    (shrub := Shrub()),
    (weeds := Weeds()),
    (grass := Grass()),
    (sand := Sand()),
    (gravel := Gravel()),
    (dirt := Dirt()),
    (entry_road := EntryRoad()),
]
ICON_LIST = [x.icon for x in ALL_TILES if x.cost is not None and x.name not in ("Road", "House", "Shop", "Office")]

ZONED_BUILDINGS = ("House", "Shop", "Office")
ZONES = ("House_Zoning", "Shop_Zoning", "Office_Zoning")
SERVICES = ("FireStation", "Hospital", "PoliceStation")
ROADS = ["Road", "EntryRoad"]


def get_type_by_name(name: str) -> GenericTile:  # type: ignore[return]
    """Used in left_click to convert an icon name to a class"""
    for cls in ALL_TILES:
        if cls.name.lower() == name.replace("_", " ").lower():
            return cls
    print(f"classes: DEBUG: COULD NOT FIND {name}")


def biome_to_tile(biome: float, include_water: bool = False, even_generate: bool = True) -> Sand | Dirt | Water | Grass | Gravel:
    """Used by the generator to convert noise to tiles, as well
    as when removing zoning to replace the floor that was there before
    Include water is used for generating without lakes, as well as when
    removing stuff so water doesn't replace it
    0.3->1 = sand
    0->0.3 = dirt
    -0.6->0 = water
    -1->-0.6 = grass

    If even_generate is set to False, it won't actually generate, and will just return grass.
    """
    if not even_generate:
        return grass
    if biome > 0.3:
        return sand
    elif biome > 0:
        return dirt
        # return Gravel()
    else:  # > -0.6
        if include_water and biome <= -0.6:
            return water
        else:
            return grass


class Tile:
    __slots__ = ("type", "biome", "quality", "road", "water", "density", "level", "happiness", "people_inside", "fire_ticks",
                 "redraw", "vehicle_heatmap", "error_list", "service_routes")  # , "temporarily_blocked")

    def __init__(
        self,
        tile_type: GenericTile | None = None,
        biome: int = 0,
        quality: int = 0,
        road: int = 0,
        water: int = 0,
        density: int = 0,
        level: int | None = None,
        happiness: int = 5,
        people_inside: list[Person] | None = None,
        fire_ticks: int | None = None,
    ) -> None:
        self.type = tile_type or grass
        self.biome = biome
        self.quality = quality
        self.road = road
        self.water = water
        self.density = density
        self.level = level
        self.happiness = happiness
        self.people_inside: list[Person] = people_inside or []
        self.fire_ticks = fire_ticks

        self.redraw = True
        self.vehicle_heatmap = 0
        self.error_list: list[str] = []
        self.service_routes: dict[str, list[tuple[int, int]]] = {}
        # self.temporarily_blocked = False

    def __repr__(self) -> str:
        return f"Tile({self.type.name=}, {self.biome=}, {self.quality=}, {self.road=}, {self.water=}, {self.density=}, {self.level=}, {self.happiness=}, {self.people_inside=}, {self.fire_ticks=})"

    def to_dict(self) -> dict[str, str | int | bool | list[Person] | None]:
        return {
            "type": self.type.name,
            "biome": self.biome,
            "quality": self.quality,
            "road": self.road,
            "water": self.water,
            "density": self.density,
            "level": self.level,
            "happiness": self.happiness,
            "people_inside": [],
            "fire_ticks": self.fire_ticks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tile":
        tile = [x for x in ALL_TILES if x.name == data["type"]][0]  # Don't create a new object, use our pre-made one
        del data["type"]
        return cls(tile, **data)
