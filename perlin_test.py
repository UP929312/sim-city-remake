from generate_world import generate_world
from utils import DEFAULT_MAP_SETTINGS

# print()
# for value in [6, 8]:
#     map = generate_world(map_settings=DEFAULT_MAP_SETTINGS | {"map_height": value, "map_width": value, "generate_ruins": False, "generate_lakes": False, "trees": 0, "seed": 12})  # type: ignore
#     map.print()
#     print()

for i in range(100):
    print("World)")
    generate_world(map_settings=DEFAULT_MAP_SETTINGS | {"map_height": 96, "map_width": 96})  # type: ignore