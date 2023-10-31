from __future__ import annotations

from typing import TYPE_CHECKING

from menu_elements import HighlightableRectangle
from utils import TILE_WIDTH

if TYPE_CHECKING:
    from map_object import Map

EXPANSION_AMOUNT = 1
DIRECTION_TO_SHIFT = {  # Axis 0 is horizontal, axis 1 is vertical, the 2nd element is shift amount
    "left": (1, -1),
    "right": ([0, 1], -1),
    "top": (1, 1),
    "bottom": (1, 0)
}
DIRECTION_TO_COORDS = {
    "left": (1, 0),
    "right": (1, 0),
    "top": (0, 1),
    "bottom": (0, 1),
}


def generate_expansion_rectangles(map: Map) -> list[HighlightableRectangle]:
    """
    Draws the red rectangles that show where the map will expand to, and returns the coords of the highlighted rectangle.
    """
    RECTANGLES: list[tuple[int, int, int, int, str]] = [
        (-TILE_WIDTH*EXPANSION_AMOUNT, 0, EXPANSION_AMOUNT*TILE_WIDTH, map.height*TILE_WIDTH, "left"),  # Left
        (map.width * TILE_WIDTH, 0, EXPANSION_AMOUNT*TILE_WIDTH, map.height*TILE_WIDTH, "right"),  # Right
        (0, map.height * TILE_WIDTH, map.width*TILE_WIDTH, EXPANSION_AMOUNT*TILE_WIDTH, "bottom"),  # Bottom
        (0, -TILE_WIDTH*EXPANSION_AMOUNT, map.width*TILE_WIDTH, EXPANSION_AMOUNT*TILE_WIDTH, "top"),  # Top
    ]
    return [HighlightableRectangle(*rectangle, hovered_colour=(255, 0, 0), unhovered_colour=(100, 0, 0)) for rectangle in RECTANGLES]
