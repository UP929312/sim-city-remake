from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from file_manager import PreferencesType
    from map_object import Map


def on_tick(map: Map, window: pygame.surface.Surface, preferences: PreferencesType, view: str, run_counter: int, x_offset: int, y_offset: int) -> None:
    """
    Runs every tick, updates the map and draws it to the screen
    """
    for (x, y, tile) in map.iter():
        if tile.redraw:
            tile.type.draw(window, map, x, y, view, old_roads=preferences["old_roads"], x_offset=x_offset, y_offset=y_offset)

        if run_counter % 4 and tile.vehicle_heatmap > 0:  # Only update the heatmap every 4 ticks so it doesn't decrease too quickly.
            tile.vehicle_heatmap -= 1
            if view == "heatmap_view":
                tile.redraw = True

        if tile.fire_ticks is not None:
            tile.redraw = True
            tile.fire_ticks += 1
        