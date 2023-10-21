import numpy as np

from classes import Tile  # , biome_to_tile


def generate_perlin_noise_2d(width: int, height: int, res: tuple[int, int]) -> np.ndarray[tuple[int, int], Tile]:  # type: ignore[type-var]

    if width % 4 != 0:
        raise TypeError(f"Width {width} is not allowed")

    delta = (res[0] / width, res[1] / height)
    d = (width // res[0], height // res[1])
    grid = np.mgrid[0 : res[0] : delta[0], 0 : res[1] : delta[1]].transpose(1, 2, 0) % 1  # type: ignore[misc]
    # Gradients
    angles = 2 * np.pi * np.random.rand(res[0] + 1, res[1] + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))
    g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
    g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
    g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)
    # Ramps
    n00 = np.sum(grid * g00, 2)
    n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
    n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
    n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)
    # Interpolation
    t = 6 * grid**5 - 15 * grid**4 + 10 * grid**3
    n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
    n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
    return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)  # type: ignore[no-any-return]




# np.random.seed(5)
# for value in [4, 8]:
#     noise = generate_perlin_noise_2d(value, value, (4, 4))  # Default 8, 8
#     two_d_array = np.array([[(0) for x in range(value)] for y in range(value)], dtype=Tile)

#     for x in range(value):
#         for y in range(value):
#             biome = biome_to_tile(noise[x, y], True)
#             two_d_array[x, y] = biome
#         print([str(x).removesuffix(" Tile").center(6) for x in two_d_array[x, :]])

#     print("-------")
