# generated file
import pygame

TILE_SIZE = 60

MAP_DATA = [
    list("111111111111111"),
    list("100000000000001"),
    list("100000000000001"),
    list("100000000000001"),
    list("100000000000001"),
    list("100000000000001"),
    list("100000000000001"),
    list("100000000000001"),
    list("100000000000001"),
    list("111111111111111"),
]

WALL_COLOR = (110, 110, 110)
SP_COLOR = (80, 180, 255)

WALLS = []


def load_map():
    WALLS.clear()

    for row_index, row in enumerate(MAP_DATA):
        for col_index, tile in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE

            if tile == "1":
                WALLS.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))


def get_tile_rect(row, col):
    return pygame.Rect(
        col * TILE_SIZE,
        row * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE
    )


def set_tile(row, col, value):
    MAP_DATA[row][col] = value


def get_tile(row, col):
    return MAP_DATA[row][col]


def find_tiles(tile_value):
    result = []

    for row_index, row in enumerate(MAP_DATA):
        for col_index, tile in enumerate(row):
            if tile == tile_value:
                result.append((row_index, col_index))

    return result


def draw_map(screen):
    for row_index, row in enumerate(MAP_DATA):
        for col_index, tile in enumerate(row):
            rect = get_tile_rect(row_index, col_index)

            if tile == "1":
                pygame.draw.rect(screen, WALL_COLOR, rect)

            elif tile == "2":
                pygame.draw.circle(screen, SP_COLOR, rect.center, 7)

            elif tile == "3":
                pygame.draw.rect(screen, (220, 180, 60), rect.inflate(-15, -15))

            elif tile == "4":
                pygame.draw.rect(screen, (120, 90, 30), rect.inflate(-15, -15))

            elif tile == "5":
                pygame.draw.rect(screen, (180, 60, 180), rect.inflate(-15, -15))

            elif tile == "6":
                pygame.draw.rect(screen, (80, 30, 80), rect.inflate(-15, -15))

            elif tile == "7":
                pygame.draw.rect(screen, (40, 120, 40), rect.inflate(-5, -5))


load_map()