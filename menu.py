import sys
from os import listdir
from typing import Any, NoReturn

import pygame

from file_manager import (PreferencesType, load_game, load_preferences,
                          save_game, save_preferences)
from generate_world import generate_world
from map_object import Map
from menu_elements import (BACK_BUTTON, Button, GoBack, IntegerSelector,
                           SliderRow, TextEntry, ToggleRow, go_back,
                           handle_menu)
from utils import DEFAULT_MAP_SETTINGS, MapSettingsType, centered_text


def margins(window: pygame.Surface) -> tuple[int, int, int, int]:
    LEFT_MARGIN = int(window.get_width() * 0.15)
    RIGHT_MARGIN = int(window.get_width() - LEFT_MARGIN)
    ELEMENT_WIDTH = int(window.get_width() - (LEFT_MARGIN * 2))
    TOP_MARGIN = int(window.get_height() // 6)
    return ELEMENT_WIDTH, TOP_MARGIN, LEFT_MARGIN, RIGHT_MARGIN

# ================================================================================================================================


def load_game_menu(window: pygame.surface.Surface, *_: Any) -> str:
    button_height = window.get_height() * 0.1
    element_width, top_margin, left_margin, right_margin = margins(window)

    def generate_save_slice(offset: int) -> tuple[tuple[Button, ...], int]:
        save_names = [file for file in listdir("saves") if file.endswith(".simcity")]
        save_buttons = [
            Button(left_margin - 32, top_margin + i * 110, element_width, button_height, save_name, lambda window, button, *_: button.text)
            for i, save_name in enumerate(save_names[offset : offset + 5])
        ]
        return tuple(save_buttons), len(save_names)

    offset = 0
    while True:
        save_buttons, num_of_saves = generate_save_slice(offset)  # Recalculate the offsetted saves each update
        elements = [BACK_BUTTON, *save_buttons]
        if num_of_saves > 5:
            elements.append(Button(right_margin, top_margin, button_height, button_height, "^", lambda *_: max(0, offset - 1)))
            elements.append(Button(right_margin, top_margin + (110 * 4), button_height, button_height, "V", lambda *_: min(offset + 1, num_of_saves - 5)))

        result = handle_menu(window, "Saves:", elements)  # type: ignore[arg-type]
        if isinstance(result, int):  # Result can either be whichever level they selected, or the new offset - to scroll
            offset = result
        elif result is not None:  # Level seleted
            return result  # type: ignore[return-value]

# ================================================================================================================================


def world_settings_menu(window: pygame.surface.Surface, *_: Any) -> MapSettingsType:
    element_width, top_margin, left_margin, _ = margins(window)  # type: ignore[assignment]
    map_settings = DEFAULT_MAP_SETTINGS
    elements: list[ToggleRow | IntegerSelector | Button] = [
        BACK_BUTTON,
        ToggleRow(left_margin, top_margin + 0, element_width, 64, "Generate Lakes", "generate_lakes", map_settings["generate_lakes"]),
        ToggleRow(left_margin, top_margin + 64, element_width, 64, "Generate Ruins", "generate_ruins", map_settings["generate_ruins"]),
        ToggleRow(left_margin, top_margin + 128, element_width, 64, "Generate Biomes", "generate_biomes", map_settings["generate_biomes"]),
        IntegerSelector(left_margin, top_margin + 200, element_width, 128, "Trees", "trees", map_settings["trees"], minimum=0, maximum=1000),
        IntegerSelector(left_margin, top_margin + 328, element_width, 128, "Starting cash", "starting_cash", map_settings["starting_cash"],  # fmt: skip
                        minimum=500, maximum=100_000, big_step=10000, small_step=1000, middle=50000),  # fmt: skip
        IntegerSelector(left_margin, top_margin + 456, element_width, 128, "Map Size", "map_width", map_settings["map_width"], minimum=24,
                        maximum=96, small_step=1, big_step=10, middle=48),  # fmt: skip
        Button(left_margin, window.get_height() - (top_margin // 2), element_width, 64, "Start", lambda *_: "New game"),
    ]

    while True:
        result = handle_menu(window, "World", elements)  # type: ignore[arg-type]
        if result not in [None, "Not None"]:  # type: ignore[comparison-overlap]
            new_map_settings: MapSettingsType = map_settings | {x.key: x.value for x in elements if hasattr(x, "key")}  # type: ignore[union-attr, assignment]
            #new_map_settings["map_height"] = new_map_settings["map_width"]
            return new_map_settings


def settings_menu(window: pygame.surface.Surface, *_: Any) -> NoReturn:
    element_width, top_margin, left_margin, _ = margins(window)  # type: ignore[assignment]
    prefs = load_preferences()

    elements: list[Button | ToggleRow | IntegerSelector] = [
        BACK_BUTTON,
        ToggleRow(left_margin, top_margin + 10, element_width, 64, "Rainbow Entities", "rainbow_entities", prefs["rainbow_entities"]),
        ToggleRow(left_margin, top_margin + 10+128, element_width, 64, "Old Town Roads", "old_roads", prefs["old_roads"]),
        IntegerSelector(left_margin, top_margin + 10+256, element_width, 128, "Max Vehicles", "max_vehicles", prefs["max_vehicles"], maximum=1000),
        IntegerSelector(left_margin, top_margin + 10+384, element_width, 128, "Max People", "max_people", prefs["max_people"], maximum=1000),
    ]

    while True:
        handle_menu(window, "Settings", elements)  # type: ignore[arg-type]
        prefs: PreferencesType = prefs | {x.key: x.value for x in elements if hasattr(x, "key")}  # type: ignore[union-attr, no-redef]
        save_preferences(prefs)


# ================================================================================================================================


def draw_main_menu(window: pygame.surface.Surface, *_: Any) -> Map:
    element_width, top_margin, left_margin, _ = margins(window)  # type: ignore[assignment]
    elements = [
        Button(left_margin, top_margin + 30 + i * 128, element_width, 64, button_text, function)  # type: ignore[arg-type]
        for i, (button_text, function) in enumerate(
            zip(["New game", "Load game", "Settings", "Quit"], [world_settings_menu, load_game_menu, settings_menu, lambda *_: pygame.quit()])
        )
    ]

    while True:
        try:
            result = handle_menu(window, "Main Menu", elements)  # type: ignore[arg-type]
        except GoBack:
            pass  # This forces the next iteration of the while True loop, going back to the main menu
        else:
            if result is not None:  # result will be dict of map settings or a save name
                if isinstance(result, dict):
                    return generate_world(result)  # type: ignore[arg-type]
                else:
                    return load_game(result)  # type: ignore[arg-type]


# ===============================================================================================================================
def save_world_window(window: pygame.surface.Surface, world: Map, *_: Any) -> str | None:
    element_width, _, left_margin, _ = margins(window)  # type: ignore[assignment]
    text = ""
    text_entry = TextEntry(left_margin, 320, element_width, 64)
    window.fill((0, 0, 0))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # elif event.type == pygame.MOUSEBUTTONDOWN:
            #     return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_RETURN:  # Enter
                    if len(text) > 0:
                        save_game(world, text + ".simcity")
                        return None
                elif event.key == pygame.K_BACKSPACE:
                    if len(text) > 0:
                        text = text[:-1]
                elif len(text) < 15 and event.unicode in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-":
                    text += event.unicode

            text_entry.text = text
            text_entry.draw(window)
            centered_text(window, 60, "Save World", (255, 255, 255), window.get_width() // 2, 80)  # TODO: Fix this
            pygame.display.update()


# ===============================================================================================================================
def draw_pause_menu(window: pygame.surface.Surface, world: Map) -> Map | None:
    element_width, top_margin, left_margin, _ = margins(window)
    pause_menu_buttons = [
        Button(left_margin, top_margin + 30 + i * 128, element_width, 64, button_text, function)  # type: ignore[arg-type]
        for i, (button_text, function) in enumerate(
            zip(["Resume", "Save", "Settings", "Main menu"], [lambda *_: go_back(), lambda window, *_: save_world_window(window, world), settings_menu, draw_main_menu])
        )
    ]

    while True:
        try:
            result = handle_menu(window, "Pause menu", pause_menu_buttons)  # type: ignore[arg-type]
        except GoBack:
            return None
        if result is not None:
            if isinstance(result, Map):
                return result  # Resume, new settings probably
            elif isinstance(result, dict):
                return generate_world(result)  # type: ignore[arg-type]  # This is for new game
            else:
                return load_game(result)  # type: ignore[arg-type]  # This is for loading a game


def draw_policy_screen(window: pygame.surface.Surface, settings: MapSettingsType) -> MapSettingsType:
    element_width, top_margin, left_margin, _ = margins(window)
    buttons: list[Button | SliderRow] = [
        BACK_BUTTON,
        SliderRow(left_margin, top_margin, element_width, 128, "Residential Tax", starting_value=settings["residential_tax_rate"], maximum=100),
        SliderRow(left_margin, top_margin + 128, element_width, 128, "Commercial Tax", starting_value=settings["commercial_tax_rate"], maximum=100),
        SliderRow(left_margin, top_margin + 256, element_width, 128, "Industrial Tax", starting_value=settings["industrial_tax_rate"], maximum=100),
        Button(left_margin, top_margin + 384 + 64, element_width, 64, "Done", lambda *_: go_back()),
    ]
    while True:
        try:
            handle_menu(window, "Policies", buttons)  # type: ignore[arg-type]
        except GoBack:
            settings = settings | {x.key: x.value for x in buttons if hasattr(x, "key")}  # type: ignore[assignment, union-attr]
            return settings
