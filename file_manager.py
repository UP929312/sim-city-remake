from __future__ import annotations

import json
from typing import TypedDict

from map_object import Map

BASE_PREFERENCES: PreferencesType = {"max_vehicles": 500, "max_people": 0, "rainbow_entities": False, "old_roads": False}


class PreferencesType(TypedDict):
    max_vehicles: int
    max_people: int
    rainbow_entities: bool
    old_roads: bool


def save_game(map: Map, save_file_name: str) -> None:
    with open("saves/" + save_file_name, "w") as file:
        json.dump(map.to_dict(), file, indent=4)


def load_game(save_file_name: str) -> Map:
    with open("saves/" + save_file_name, "r") as file:
        return Map.from_dict(json.load(file))


def load_preferences() -> PreferencesType:
    with open("preferences.txt", "r") as file:
        return BASE_PREFERENCES | json.load(file)  # type: ignore[no-any-return]


def save_preferences(preferences: PreferencesType) -> None:
    with open("preferences.txt", "w") as file:
        json.dump(preferences, file)


def migrate_worlds() -> None:
    import os

    for save in os.listdir("saves"):
        print(save)
        map = load_game(save)

        # for x in range(map.width):
        #     for y in range(map.height):
        #         #old_tile = map[x, y]

        # map.version = VERSION
        save_game(map, save)


if __name__ == "__main__":
    migrate_worlds()
