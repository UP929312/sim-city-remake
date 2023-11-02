import sys  # For sys.exit()
from random import choice, randint  # For random ticks (and picking traffic)
from typing import Literal

import pygame

from classes import get_type_by_name
from entities import Pedestrian, Vehicle
from file_manager import load_preferences
from generate_world import generate_world
from menu import draw_main_menu, draw_pause_menu
from menu_elements import FadingTextBottomButton, handle_collisions
from overlays import generate_bottom_bar, generate_side_bar
# ============================
from utils import (DESIRED_FPS, IMAGES, TICK_RATE, TILE_EXPANSION_COST,
                   TILE_WIDTH, VERSION, MapSettingsType,
                   convert_mouse_pos_to_coords, coords_to_screen_pos,
                   generate_background_image, get_all_grid_coords,
                   get_class_properties)

# https://www.freepik.com/search?format=search&query=fire%20station%20icon%20pixel%20art
print("main: Starting")
# ============================
# Pygame inits
pygame.display.init()
window = pygame.display.set_mode((1710, 870), pygame.RESIZABLE)  # | pygame.DOUBLEBUF | pygame.HWSURFACE)  # Doublebuf+HWSURFACE is for performance
window.set_alpha(None)  # This is for performance
pygame.display.set_caption(f"Sim City {'.'.join([str(x) for x in VERSION])}")
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
x_offset, y_offset, expansion_rectangles = map.reset_map(window)
fading_text_element = FadingTextBottomButton(0, 0, 16, 16, [])
side_bar_elements = []  # type: ignore[var-annotated]
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

        window.blit(map.background_image, (0, 0))
        map.redraw_entire_map()

        mouse_down_x, mouse_down_y = None, None
        mouse_down_tile_x, mouse_down_tile_y = None, None
        mouse_motion_x, mouse_motion_y = None, None
        mouse_motion_tile_x, mouse_motion_tile_y = None, None
    # =========================================================
    # CONTROLS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # ----------------------------------------------------------
        if event.type == pygame.VIDEORESIZE:
            map.background_image = generate_background_image(window)
            window.blit(map.background_image, (0, 0))
            x_offset, y_offset, expansion_rectangles = map.reset_map(window)
        # ----------------------------------------------------------
        # KEY DOWN
        elif event.type == pygame.KEYDOWN:  # If they press a key
            if event.key == pygame.K_q:  # Re-center map
                x_offset, y_offset, expansion_rectangles = map.reset_map(window)

            elif event.key in [pygame.K_COMMA, pygame.K_PERIOD]:
                view_index += 1 if event.key == pygame.K_PERIOD else -1
                view = views[view_index % len(views)]
                map.redraw_entire_map()

            elif event.key == pygame.K_m:  # Dev tool for testing
                map.cash = 999999

            elif event.key == pygame.K_p:
                pause = not pause

            elif event.key == pygame.K_f:
                assert mouse_motion_tile_x is not None and mouse_motion_tile_y is not None
                map[mouse_motion_tile_x, mouse_motion_tile_y].fire_ticks = 1

            # elif event.key == pygame.K_i:
            #     rint(f"{map.emergency_vehicles_on_route=}")  # {map.services=},

            elif event.key == pygame.K_e:
                map.expand()
                x_offset, y_offset, expansion_rectangles = map.reset_map(window)

            elif event.key == pygame.K_r:
                map = generate_world(map_settings=map.settings, seed=randint(1, 100))  # pyright: ignore

            elif event.key == pygame.K_ESCAPE:
                result = draw_pause_menu(window, map)
                if result is not None:
                    map = result
                preferences = load_preferences()
                x_offset, y_offset, expansion_rectangles = map.reset_map(window)

                mouse_down_x, mouse_down_y = None, None  # TODO: Change how this works I guess
                mouse_down_tile_x, mouse_down_tile_y = None, None
                mouse_motion_x, mouse_motion_y = None, None
                mouse_motion_tile_x, mouse_motion_tile_y = None, None
        # ----------------------------------------------------------
        # MOUSE DOWN
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:  # When they click the button
            mouse_down_x, mouse_down_y = pygame.mouse.get_pos()
            mouse_down_tile_x, mouse_down_tile_y = convert_mouse_pos_to_coords(mouse_down_x, mouse_down_y, x_offset, y_offset, map, window)

            right_bar_result: None | tuple[str, str, int, MapSettingsType] = handle_collisions(window, mouse_down_x, mouse_down_y, side_bar_elements, 0, 0)
            if right_bar_result is not None:
                tool, draw_style, icon_offset, new_settings = right_bar_result
                map.settings: MapSettingsType = map.settings | new_settings  # type: ignore[misc]
                map.redraw_entire_map()

            vehicles = [x for x in map.entity_lists["Vehicle"] if x.current_loc == (mouse_down_tile_x, mouse_down_tile_y)]
            if vehicles:
                fading_text_element.add_to_queue(str(vehicles[0]))

            for rectangle in expansion_rectangles:
                if rectangle.intersected(mouse_down_x-x_offset, mouse_down_y-y_offset):
                    if (rectangle.width*rectangle.height) // TILE_WIDTH > map.cash:
                        fading_text_element.add_to_queue("Not enough cash")
                    else:
                        fading_text_element.add_to_queue(f"Expanding in direction: {rectangle.text}")
                        map.expand(direction=str(rectangle.text))
                        x_offset -= TILE_WIDTH if rectangle.text == "left" else 0
                        y_offset -= TILE_WIDTH if rectangle.text == "top" else 0
                        map.cash -= (rectangle.width // TILE_WIDTH) * (rectangle.height // TILE_WIDTH) * TILE_EXPANSION_COST
                        _, _, expansion_rectangles = map.reset_map(window)  # Generate new rectangles

        # ----------------------------------------------------------
        # MOUSE UP
        elif event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_LEFT:  # When they release the mouse button
            mouse_up_x, mouse_up_y = pygame.mouse.get_pos()
            mouse_up_tile_x, mouse_up_tile_y = convert_mouse_pos_to_coords(mouse_up_x, mouse_up_y, x_offset, y_offset, map, window)

            if mouse_up_tile_x is not None and mouse_up_tile_y is not None and mouse_down_tile_x is not None and mouse_down_tile_y is not None:
                for x, y in get_all_grid_coords(mouse_down_tile_x, mouse_down_tile_y, mouse_up_tile_x, mouse_up_tile_y, single_place=draw_style == "single"):
                    if tool == "select":
                        map[x, y].type.on_random_tick(map, x, y)
                        print(f"main: Tile at {x}, {y}: ---------------")
                        for prop in get_class_properties(map[x, y]):
                            print(f"main: {prop}: " + str(getattr(map[x, y], prop)))
                    elif tool == "destroy":
                        message = map[x, y].type.on_destroy(map, x, y)
                        fading_text_element.add_to_queue(message)
                    else:
                        tile_class = get_type_by_name(tool)
                        message = tile_class.on_place(map, x, y)
                        fading_text_element.add_to_queue(message)
                    # -----------------------------------
                    map[x, y].error_list = []

                map.check_connected()
                map.redraw_entire_map()  # Mainly for roads

        elif event.type == pygame.MOUSEBUTTONUP:  # Cancel dragging
            mouse_up_x, mouse_up_y, mouse_down_x, mouse_down_y = None, None, None, None  # type: ignore[assignment]
        # ----------------------------------------------------------
        # MOUSE MOTION
        elif event.type == pygame.MOUSEMOTION:  # This is for writing the error (when the user moves the mouse over an error square)
            mouse_motion_x, mouse_motion_y = pygame.mouse.get_pos()
            mouse_motion_tile_x, mouse_motion_tile_y = convert_mouse_pos_to_coords(mouse_motion_x, mouse_motion_y, x_offset, y_offset, map, window)

            for rectangle in expansion_rectangles:
                if rectangle.intersected(mouse_motion_x-x_offset, mouse_motion_y-y_offset):
                    rectangle.on_hover()
                else:
                    rectangle.off_hover()

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
        for _ in range(ENTITIES_TO_CREATE_PER_TICK):
            if len(entity_list) < preferences["max_" + ("vehicles" if entity_name == "Vehicle" else "pedestrians")]:  # type: ignore[literal-required]
                route_type = choice(["residential", "commercial", "industrial"])
                entity_type.try_create(entity_type, map, route_type, rainbow_entities_enabled=preferences["rainbow_entities"])  # type: ignore[attr-defined]
    # =========================================================
    # DRAWING - MAP
    for (x, y, tile) in map.iter():
        if tile.redraw:
            tile.type.draw(window, map, x, y, view, old_roads=preferences["old_roads"], x_offset=x_offset, y_offset=y_offset)

        if run_counter % 4 and tile.vehicle_heatmap > 0:  # Only update the heatmap every 4 ticks so it doesn't decrease too quickly.
            tile.vehicle_heatmap -= 1
            if view == "heatmap_view":
                tile.redraw = True

        if tile.fire_ticks is not None:
            tile.redraw = True  # TODO: Remove this
            tile.fire_ticks += 1
    # ---------------------------------------------------------
    # DRAWING - Drag Grid
    if mouse_motion_tile_x is not None and mouse_motion_tile_y is not None:
        # GENERATE DRAG GRID
        if pygame.mouse.get_pressed()[0] and mouse_down_tile_x is not None and mouse_down_tile_y is not None:
            for x, y in get_all_grid_coords(mouse_down_tile_x, mouse_down_tile_y, mouse_motion_tile_x, mouse_motion_tile_y, single_place=draw_style == "single"):
                window.blit(IMAGES["dragged_square"], coords_to_screen_pos(x, y, x_offset, y_offset))
                map[x, y].redraw = True

        window.blit(IMAGES["dragged_square"], coords_to_screen_pos(mouse_motion_tile_x, mouse_motion_tile_y, x_offset, y_offset))
        map[mouse_motion_tile_x, mouse_motion_tile_y].redraw = True
        # ---------------------------------------------------------
        # DRAWING - Bottom bar
        if tool == "select" and len(map[mouse_motion_tile_x, mouse_motion_tile_y].error_list) > 0:
            fading_text_element.add_to_queue(map[mouse_motion_tile_x, mouse_motion_tile_y].error_list[0])

    # DRAWING Right Bar
    side_bar_elements = generate_side_bar(tool, draw_style, icon_offset, window, map.settings)
    for rectangle in expansion_rectangles:
        rectangle.draw(window, x_offset, y_offset)

    generate_bottom_bar(window, map, view, run_counter, clock, mouse_motion_tile_x, mouse_motion_tile_y, mouse_motion_x, mouse_motion_y, fading_text_element)

    if not pause:
        run_counter += 1

    for i in range(TICK_RATE):
        x, y = randint(0, map.width-1), randint(0, map.height-1)  # randint excludes the last number, so we need to do -1
        map[x, y].type.on_random_tick(map, x, y)

    pygame.display.update()

    clock.tick(DESIRED_FPS)
