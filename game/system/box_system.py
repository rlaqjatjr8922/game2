# generated file
import pygame
import math

from game.core.map import MAP_DATA, get_tile, set_tile, TILE_SIZE
from game.system.item_system import ItemSystem


class BoxSystem:
    def __init__(self):
        self.item_system = ItemSystem()

        self.opening_boxes = {}
        self.respawn_boxes = {}

        self.normal_open_time = 1.0
        self.curse_open_time = 3.0

        self.normal_respawn_time = 5.0
        self.curse_respawn_time = 15.0

    def update(self, characters, dt):
        self.update_opening(characters, dt)
        self.update_respawn(dt)

    def update_opening(self, characters, dt):
        touching = {}

        for character in characters:
            row = character.rect.centery // TILE_SIZE
            col = character.rect.centerx // TILE_SIZE

            if row < 0 or row >= len(MAP_DATA):
                continue

            if col < 0 or col >= len(MAP_DATA[row]):
                continue

            tile = get_tile(row, col)

            if tile == "3":
                touching[(row, col)] = character

                if (row, col) not in self.opening_boxes:
                    self.opening_boxes[(row, col)] = {
                        "character": character,
                        "timer": self.normal_open_time,
                        "type": "normal",
                    }

            elif tile == "5":
                touching[(row, col)] = character

                if (row, col) not in self.opening_boxes:
                    self.opening_boxes[(row, col)] = {
                        "character": character,
                        "timer": self.curse_open_time,
                        "type": "curse",
                    }

        for pos in list(self.opening_boxes.keys()):
            data = self.opening_boxes[pos]

            # 열던 캐릭터가 벗어나면 취소
            if pos not in touching or touching[pos] != data["character"]:
                del self.opening_boxes[pos]
                continue

            data["timer"] -= dt

            if data["timer"] <= 0:
                row, col = pos
                character = data["character"]

                if data["type"] == "normal":
                    self.item_system.apply_normal_box(character)
                    set_tile(row, col, "4")

                    self.respawn_boxes[pos] = {
                        "timer": self.normal_respawn_time,
                        "close_tile": "3",
                    }

                elif data["type"] == "curse":
                    self.item_system.apply_curse_box(character, characters)
                    set_tile(row, col, "6")

                    self.respawn_boxes[pos] = {
                        "timer": self.curse_respawn_time,
                        "close_tile": "5",
                    }

                del self.opening_boxes[pos]

    def update_respawn(self, dt):
        for pos in list(self.respawn_boxes.keys()):
            data = self.respawn_boxes[pos]
            data["timer"] -= dt

            if data["timer"] <= 0:
                row, col = pos
                set_tile(row, col, data["close_tile"])
                del self.respawn_boxes[pos]

    def draw(self, screen):
        for pos, data in self.opening_boxes.items():
            row, col = pos

            x = col * TILE_SIZE + TILE_SIZE // 2
            y = row * TILE_SIZE + TILE_SIZE // 2

            if data["type"] == "normal":
                total_time = self.normal_open_time
                color = (255, 220, 80)
            else:
                total_time = self.curse_open_time
                color = (200, 80, 255)

            progress = 1 - (data["timer"] / total_time)

            radius = 20

            pygame.draw.circle(
                screen,
                (40, 40, 40),
                (x, y),
                radius,
                3
            )

            end_angle = progress * 360

            rect = pygame.Rect(
                x - radius,
                y - radius,
                radius * 2,
                radius * 2
            )

            pygame.draw.arc(
                screen,
                color,
                rect,
                0,
                math.radians(end_angle),
                4
            )