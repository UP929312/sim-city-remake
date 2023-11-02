from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from classes import ICON_LIST, get_type_by_name
from menu import draw_policy_screen
from menu_elements import BottomRow, FadingTextBottomButton, IconButton
from utils import ICON_SIZE, IMAGES

if TYPE_CHECKING:
    from map_object import Map
    from utils import MapSettingsType


def icon_name_to_function(name: str, tool: str, draw_style: str, icon_offset: int, settings: MapSettingsType) -> tuple[str, str, int, MapSettingsType]:
    if name == "change_draw_style":
        draw_style = "drag" if (draw_style == "single") else "single"
    elif name == "change_tool_select":
        tool = "select"
        draw_style = "single"
    elif name == "change_tool_destroy":
        tool = "destroy"
        draw_style = "drag"
    elif name == "scroll_up":
        icon_offset = icon_offset - 1 if icon_offset > 0 else len(ICON_LIST) - 1
    elif name == "scroll_down":
        icon_offset += 1
    elif "click_icon_" in name:
        tool = name.removeprefix("click_icon_").removesuffix("_icon")
        tile_class = get_type_by_name(tool)
        draw_style = "single" if tile_class.single_place else "drag"

    return tool, draw_style, icon_offset, settings


def handle_policy_change(window: pygame.surface.Surface, tool: str, draw_style: str, icon_offset: int, settings: MapSettingsType) -> tuple[str, str, int, MapSettingsType]:
    settings = draw_policy_screen(window, settings)
    return tool, draw_style, icon_offset, settings


def generate_side_bar(tool: str, draw_style: str, icon_offset: int, window: pygame.surface.Surface, settings: MapSettingsType) -> list[IconButton]:
    pygame.draw.rect(window, (0, 0, 0), (window.get_width()-ICON_SIZE, 0, ICON_SIZE, window.get_height()))
    verticle_tiles = window.get_height() // (ICON_SIZE*2+1) - 2*3

    def button_press(_: pygame.surface.Surface, button: IconButton, _1: int, _2: int) -> tuple[str, str, int, MapSettingsType]:
        return icon_name_to_function(button.text, tool, draw_style, icon_offset, settings)

    x = window.get_width() - ICON_SIZE
    static_buttons = [
        IconButton(x, 0, ICON_SIZE, ICON_SIZE, "change_draw_style", IMAGES[f"{draw_style}_draw_icon"], is_selected=True, on_click=button_press),
        IconButton(x, 64, ICON_SIZE, ICON_SIZE, "change_tool_select", IMAGES["select_icon"], is_selected=(tool == "select"), on_click=button_press),
        IconButton(x, 128, ICON_SIZE, ICON_SIZE, "change_tool_destroy", IMAGES["destroy_icon"], is_selected=(tool == "destroy"), on_click=button_press),
        IconButton(x, 192, ICON_SIZE, ICON_SIZE, "click_icon_road", IMAGES["road_icon"], is_selected=(tool == "road"), on_click=button_press),
        IconButton(x, 256, ICON_SIZE, ICON_SIZE, "scroll_up", IMAGES["up_arrow"], is_selected=True, on_click=button_press),
        IconButton(x, window.get_height()-ICON_SIZE*3, ICON_SIZE, ICON_SIZE, "scroll_down",   IMAGES["down_arrow"], is_selected=True, on_click=button_press),
        IconButton(x, window.get_height()-ICON_SIZE,   ICON_SIZE, ICON_SIZE, "policy_screen", IMAGES["policy_menu"], is_selected=True,
                   on_click=lambda *_: handle_policy_change(window, tool, draw_style, icon_offset, settings)),
    ]
    dynamic_buttons = []
    for i, icon in enumerate([ICON_LIST[(i + icon_offset) % len(ICON_LIST)] for i in range(verticle_tiles)]):
        button = IconButton(x, 320 + i * 64, ICON_SIZE, ICON_SIZE, f"click_icon_{icon}", IMAGES[icon], is_selected=(tool == icon.removesuffix("_icon")), on_click=button_press)
        dynamic_buttons.append(button)

    for element in static_buttons + dynamic_buttons:
        element.draw(window, 0, 0)

    return static_buttons + dynamic_buttons


def generate_bottom_bar(
    window: pygame.surface.Surface, map: Map, view: str, run_counter: int, clock: pygame.time.Clock,
    mouse_tile_x: int | None, mouse_tile_y: int | None, mouse_x: int | None, mouse_y: int | None,
    fading_text_element: FadingTextBottomButton,
) -> None:
    bottom_row = BottomRow(
        0, window.get_height() - ICON_SIZE, window.get_width()-ICON_SIZE, ICON_SIZE,
        f"Cash: {map.cash}  "
        f"{view.removesuffix('_view').capitalize()}  "
        f"FPS: {int(clock.get_fps())}  "
        f"Vehicles: {len(map.entity_lists['Vehicle'])}  "
        f"Run Counter: {run_counter}  "
        f"Coords: {mouse_x}, {mouse_y}  "
        f"Tile: {mouse_tile_x}, {mouse_tile_y}  ",
        fading_text_element,
    )
    bottom_row.draw(window, 0, 0)
