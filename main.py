import sys  # For sys.exit()
from random import choice, randint  # For random ticks (and picking traffic)
from typing import Literal

import pygame

from classes import get_type_by_name
from entities import Pedestrian, Vehicle
from file_manager import load_preferences
#from generate_world import generate_world
from generate_world_2 import generate_world
# ============================
from menu import draw_main_menu, draw_pause_menu
from menu_elements import handle_collisions
from on_tick import on_tick
from overlays import generate_bottom_bar, generate_side_bar
from utils import (BACKGROUND_COLOUR, DESIRED_FPS, ICON_SIZE, IMAGES,
                   TICK_RATE, TILE_WIDTH, VERSION, MapSettingsType,
                   cursor_is_in_world, get_all_grid_coords,
                   get_class_properties, reset_map)

# https://www.freepik.com/search?format=search&query=fire%20station%20icon%20pixel%20art
print("main: Starting")
# ============================
# Pygame inits
pygame.display.init()
window = pygame.display.set_mode((1710, 870), pygame.RESIZABLE)  # Used to be 800, 800
pygame.display.set_caption(f"Sim City {'.'.join([str(x) for x in VERSION])}")
pygame.font.init()
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.VIDEORESIZE])
# ============================
# Vars init
run_counter = 0
icon_offset = 0
view_index = 0
ENTITIES_TO_CREATE_PER_TICK = 2
movement_keys = [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]

mouse_down_x, mouse_down_y = None, None
mouse_down_tile_x, mouse_down_tile_y = None, None
mouse_motion_x, mouse_motion_y = None, None
mouse_motion_tile_x, mouse_motion_tile_y = None, None

pause = False

tool = "select"
draw_style = "single"
error_text = ""

views = (
    "general_view",
    "nearest_services",
    "happiness_view",
    "heatmap_view",
    "quality_view",
    "density_view",
    "water_view",
    "fire_view",
    "hospital_view",
    "police_view",
    "colour_view",
    "crazy_view",
)
view = views[0]

# ============================
map = draw_main_menu(window)
preferences = load_preferences()
x_offset, y_offset = reset_map(window, map)
# DRAWING Right Bar
side_bar_elements = generate_side_bar(tool, draw_style, icon_offset, window, map.settings)
# ============================
clock = pygame.time.Clock()

while True:
    if run_counter % (DESIRED_FPS*3) == 0:  # Once a second
        map.check_connected()  # Update any roads that are not connected to the main road network, and also check any buildings not on roads

    held_keys = pygame.key.get_pressed()
    pressing_movement_key = [held_keys[x] for x in movement_keys if held_keys[x]]

    if pressing_movement_key:
        held_key = movement_keys[[held_keys[x] for x in movement_keys].index(True)]
        offsets = {"w": (0, TILE_WIDTH), "s": (0, -TILE_WIDTH), "a": (TILE_WIDTH, 0), "d": (-TILE_WIDTH, 0)}
        x_offset += offsets[pygame.key.name(held_key)][0]
        y_offset += offsets[pygame.key.name(held_key)][1]

        window.fill(BACKGROUND_COLOUR, rect=(0, 0, window.get_width()-ICON_SIZE, window.get_height()-ICON_SIZE))
        map.redraw_entire_map()

        mouse_down_x, mouse_down_y = None, None
        mouse_down_tile_x, mouse_down_tile_y = None, None
        mouse_motion_x, mouse_motion_y = None, None
        mouse_motion_tile_x, mouse_motion_tile_y = None, None
    # =========================================================
    # DRAWING - MAP | Emergency services | fire and more
    on_tick(map, window, preferences, view, run_counter, x_offset, y_offset)
    # ---------------------------------------------------------
    if cursor_is_in_world(map, window, mouse_motion_tile_x, mouse_motion_tile_y):
        assert mouse_motion_tile_x is not None and mouse_motion_tile_y is not None

        # GENERATE DRAG GRID
        if pygame.mouse.get_pressed()[0] and cursor_is_in_world(map, window, mouse_down_tile_x, mouse_down_tile_y):
            assert mouse_down_tile_x is not None and mouse_down_tile_y is not None
            for x, y in get_all_grid_coords(mouse_down_tile_x, mouse_down_tile_y, mouse_motion_tile_x, mouse_motion_tile_y, single_place=draw_style == "single"):
                window.blit(IMAGES["dragged_square"].convert_alpha(), ((x * TILE_WIDTH)+x_offset, (y * TILE_WIDTH)+y_offset))
                map[x, y].redraw = True

        window.blit(IMAGES["dragged_square"], ((mouse_motion_tile_x * TILE_WIDTH)+x_offset, (mouse_motion_tile_y * TILE_WIDTH)+y_offset))
        map[mouse_motion_tile_x, mouse_motion_tile_y].redraw = True
        # ---------------------------------------------------------
        # DRAWING - Bottom bar
        if tool == "select" and len(map[mouse_motion_tile_x, mouse_motion_tile_y].error_list) > 0:  # type: ignore[index]
            error_text = map[mouse_motion_tile_x, mouse_motion_tile_y].error_list[0]  # type: ignore[index]

    generate_bottom_bar(window, map, view, run_counter, clock, error_text)
    error_text = ""
    # DRAWING - Side bar only happens on update
    # =========================================================
    # CONTROLS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # ----------------------------------------------------------
        if event.type == pygame.VIDEORESIZE:
            window.fill(BACKGROUND_COLOUR, rect=(0, 0, window.get_width()-ICON_SIZE, window.get_height()-ICON_SIZE))
            map.redraw_entire_map()
        # ----------------------------------------------------------
        # KEY DOWN
        elif event.type == pygame.KEYDOWN:  # If they press a key
            if event.key == pygame.K_SPACE:
                pause = not pause

            elif event.key == pygame.K_q:  # Re-center map
                x_offset, y_offset = reset_map(window, map)
                generate_side_bar(tool, draw_style, icon_offset, window, map.settings)

            elif event.key in [pygame.K_COMMA, pygame.K_PERIOD]:
                view_index += 1 if event.key == pygame.K_PERIOD else -1
                view = views[view_index % len(views)]
                map.redraw_entire_map()

            elif event.key == pygame.K_m:  # Dev tool for testing
                map.cash = 999999

            elif event.key == pygame.K_f:
                map[mouse_motion_tile_x, mouse_motion_tile_y].fire_ticks = 1  # type: ignore[index]

            elif event.key == pygame.K_i:
                print(f"{map.emergency_vehicles_on_route=}")  # {map.services=},

            elif event.key == pygame.K_e:
                map.expand()
                x_offset, y_offset = reset_map(window, map)
                generate_side_bar(tool, draw_style, icon_offset, window, map.settings)

            elif event.key == pygame.K_r:
                if map.width % 4 != 0:  # Only multiples of 4 work
                    map = generate_world(map_settings=map.settings, seed=randint(1, 100))  # pyright: ignore

            elif event.key == pygame.K_ESCAPE:
                result = draw_pause_menu(window, map)
                if result is not None:
                    map = result
                preferences = load_preferences()
                x_offset, y_offset = reset_map(window, map)
        # ----------------------------------------------------------
        # MOUSE DOWN
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:  # When they click the button
            mouse_down_x, mouse_down_y = pygame.mouse.get_pos()
            mouse_down_tile_x, mouse_down_tile_y = (mouse_down_x-x_offset) // TILE_WIDTH, (mouse_down_y-y_offset) // TILE_WIDTH

            right_bar_result: None | tuple[str, str, int, MapSettingsType] = handle_collisions(window, mouse_down_x, mouse_down_y, side_bar_elements)  # type: ignore[arg-type]
            if right_bar_result is not None:
                tool, draw_style, icon_offset, new_settings = right_bar_result
                map.settings: MapSettingsType = map.settings | new_settings  # type: ignore[misc]
                map.redraw_entire_map()
                # DRAWING Right Bar, only if it updates
                side_bar_elements = generate_side_bar(tool, draw_style, icon_offset, window, map.settings)

            vehicles = [x for x in map.entity_lists["Vehicle"] if x.current_loc == (mouse_down_tile_x, mouse_down_tile_y)]
            if vehicles:
                print("main:", str(vehicles[0]))
        # ----------------------------------------------------------
        # MOUSE UP
        elif event.type == pygame.MOUSEBUTTONUP:  # When they release the mouse button
            if event.button == pygame.BUTTON_LEFT:
                mouse_up_x, mouse_up_y = pygame.mouse.get_pos()
                mouse_up_tile_x, mouse_up_tile_y = (mouse_up_x-x_offset) // TILE_WIDTH, (mouse_up_y-y_offset) // TILE_WIDTH
                if cursor_is_in_world(map, window, mouse_up_tile_x, mouse_up_tile_y) and cursor_is_in_world(map, window, mouse_down_tile_x, mouse_down_tile_y):
                    assert mouse_down_tile_x is not None and mouse_down_tile_y is not None
                    for x, y in get_all_grid_coords(mouse_down_tile_x, mouse_down_tile_y, mouse_up_tile_x, mouse_up_tile_y, single_place=draw_style == "single"):
                        if tool == "select":
                            map[x, y].type.on_random_tick(map, x, y)
                            print(f"main: Tile at {x}, {y}: ---------------")
                            for prop in get_class_properties(map[x, y]):
                                print(f"main: {prop}: " + str(getattr(map[x, y], prop)))
                        elif tool == "destroy":
                            map[x, y].type.on_destroy(map, x, y)
                        else:
                            tile_class = get_type_by_name(tool)
                            tile_class.on_place(map, x, y)
                        # -----------------------------------
                        map[x, y].error_list = []

                    map.check_connected()
                    map.redraw_entire_map()

            mouse_up_x, mouse_up_y, mouse_down_x, mouse_down_y = None, None, None, None  # type: ignore[assignment]

        # ----------------------------------------------------------
        # MOUSE MOTION
        elif event.type == pygame.MOUSEMOTION:  # This is for writing the error (when the user moves the mouse over an error square)
            mouse_motion_x, mouse_motion_y = pygame.mouse.get_pos()
            mouse_motion_tile_x, mouse_motion_tile_y = (mouse_motion_x-x_offset) // TILE_WIDTH, (mouse_motion_y-y_offset) // TILE_WIDTH

    # =========================================================
    # ENTITY HANDLING HANDLING
    for entity_type in [Vehicle, Pedestrian]:
        entity_name: Literal["Vehicle", "Pedestrian"] = entity_type.__name__  # type: ignore[assignment]
        entity_list: list[Vehicle] | list[Pedestrian] = map.entity_lists[entity_name]
        # DRAW
        if view in ("general_view", "crazy_view", "colour_view"):
            for entity in entity_list:
                entity.draw(window, x_offset, y_offset)

        if pause:  # If the game is paused, don't move or create entities
            continue

        # MOVE
        if run_counter % entity_type.speed == 0:  # type: ignore[attr-defined]
            for entity in entity_list:
                new_pos = entity.update(map, entity_list)  # type: ignore[arg-type]
                if new_pos is None:
                    entity.on_arrive(map)
                else:
                    map[new_pos].vehicle_heatmap = min(map[new_pos].vehicle_heatmap + 2 * DESIRED_FPS, 255)  # Heatmap

        # CREATE
        for _ in range(ENTITIES_TO_CREATE_PER_TICK):  # type: ignore[assignment]
            if len(entity_list) < preferences["max_" + ("vehicles" if entity_name == "Vehicle" else "people")]:  # type: ignore[literal-required]
                route_type = choice(["residential", "commercial", "industrial"])
                entity_type.try_create(entity_type, map, route_type, rainbow_entities_enabled=preferences["rainbow_entities"])  # type: ignore[attr-defined]
    # =========================================================
    if not pause:
        run_counter += 1

    for i in range(TICK_RATE):
        x, y = randint(1, map.width - 1), randint(1, map.height - 1)  # Can't remember why I exclude the outer edge
        map[x, y].type.on_random_tick(map, x, y)

    pygame.display.update()

    clock.tick(DESIRED_FPS)
