# generated file
import random

from game.core.map import MAP_DATA, get_tile, set_tile, find_tiles, TILE_SIZE


class SPSystem:
    def __init__(self, count=12):
        self.count = count

        for _ in range(self.count):
            self.spawn_orb()

    def spawn_orb(self):
        empty_tiles = find_tiles("0")

        if not empty_tiles:
            return

        row, col = random.choice(empty_tiles)
        set_tile(row, col, "2")

    def update(self, characters):
        for character in characters:
            row = character.rect.centery // TILE_SIZE
            col = character.rect.centerx // TILE_SIZE

            if row < 0 or row >= len(MAP_DATA):
                continue

            if col < 0 or col >= len(MAP_DATA[row]):
                continue

            if get_tile(row, col) == "2":
                character.add_sp(10)
                set_tile(row, col, "0")
                self.spawn_orb()