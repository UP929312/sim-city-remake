import matplotlib.pyplot as plt
from perlin_noise import PerlinNoise  # type: ignore[import]

seed = 5
noise = PerlinNoise(octaves=2, seed=5)

map_width, map_height = 48, 48
pic = []
for x in range(map_width):
    row = []
    for y in range(map_height):
        noise_value = noise([x/map_width, y/map_height]) * 3
        row.append(noise_value)
    pic.append(row)

plt.imshow(pic, cmap='gray')
plt.show()  # type: ignore[no-untyped-call]
