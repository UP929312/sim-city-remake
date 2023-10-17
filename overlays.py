from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from classes import ICON_LIST, get_type_by_name
from menu import draw_policy_screen
from menu_elements import IconButton, RowOfButtons
from utils import ICON_SIZE

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

    def button_press(_1: Any, button: IconButton, *_: Any) -> tuple[str, str, int, MapSettingsType]:
        return icon_name_to_function(button.text, tool, draw_style, icon_offset, settings)  # type: ignore[arg-type]

    x = window.get_width() - ICON_SIZE
    static_buttons = [
        IconButton(x, 0, ICON_SIZE, ICON_SIZE, "change_draw_style", icon_image=f"{draw_style}_draw_icon", is_selected=True, on_click=button_press),  # type: ignore[arg-type]
        IconButton(x, 64, ICON_SIZE, ICON_SIZE, "change_tool_select", icon_image="select_icon", is_selected=(tool == "select"), on_click=button_press),  # type: ignore[arg-type]
        IconButton(x, 128, ICON_SIZE, ICON_SIZE, "change_tool_destroy", icon_image="destroy_icon", is_selected=(tool == "destroy"), on_click=button_press),  # type: ignore[arg-type]
        IconButton(x, 192, ICON_SIZE, ICON_SIZE, "click_icon_road", icon_image="road_icon", is_selected=(tool == "road"), on_click=button_press),  # type: ignore[arg-type]
        IconButton(x, 256, ICON_SIZE, ICON_SIZE, "scroll_up", icon_image="up_arrow", is_selected=True, on_click=button_press),  # type: ignore[arg-type]
        IconButton(x, window.get_height()-ICON_SIZE*3, ICON_SIZE, ICON_SIZE, "scroll_down", icon_image="down_arrow", is_selected=True, on_click=button_press),  # type: ignore[arg-type]
        IconButton(x, window.get_height()-ICON_SIZE, ICON_SIZE, ICON_SIZE, "policy_screen", icon_image="policy_menu", is_selected=True, on_click=lambda *_: handle_policy_change(window, tool, draw_style, icon_offset, settings)  # type: ignore[arg-type]
        ),
    ]
    dynamic_buttons = []
    for i, icon in enumerate([ICON_LIST[(i + icon_offset) % len(ICON_LIST)] for i in range(verticle_tiles)]):
        button = IconButton(x, 320 + i * 64, ICON_SIZE, ICON_SIZE, f"click_icon_{icon}", icon_image=icon, is_selected=(tool == icon.removesuffix("_icon")), on_click=button_press)  # type: ignore[arg-type]
        dynamic_buttons.append(button)
    return static_buttons + dynamic_buttons

def generate_bottom_bar(window: pygame.surface.Surface, map: Map, view: str, run_counter: int, clock: pygame.time.Clock, error_text: str) -> list[RowOfButtons]:
    return [RowOfButtons(0, window.get_height() - ICON_SIZE, window.get_width()-ICON_SIZE, ICON_SIZE,
                        [f"Cash: {map.cash}", view.removesuffix("_view").capitalize(), f"FPS: {int(clock.get_fps())}, Vehics: {len(map.entity_lists['Vehicle'])}", str(run_counter)]
                        +([error_text] if error_text else []),
                        # lambda *_: None
    )]
