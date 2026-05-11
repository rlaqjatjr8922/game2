# generated file
import math
import pygame

from game.core.collision import move_with_collision
from game.core.map import TILE_SIZE, get_tile


class Player:
    def __init__(self, x, y, screen_width, screen_height):

        self.name = "PLAYER"

        self.rect = pygame.Rect(x, y, 32, 32)

        self.screen_rect = pygame.Rect(
            0,
            0,
            screen_width,
            screen_height
        )

        self.normal_speed = 3.5
        self.run_speed = 6.0

        self.sp = 50
        self.max_sp = 100

        self.running = False

        self.is_tagger = False

        self.hp = 100

        self.stun_timer = 0

    def update(self, dt, walls, map_data, players, others):

        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.running = False
            return

        keys = pygame.key.get_pressed()

        dx = 0
        dy = 0

        if keys[pygame.K_w]:
            dy -= 1

        if keys[pygame.K_s]:
            dy += 1

        if keys[pygame.K_a]:
            dx -= 1

        if keys[pygame.K_d]:
            dx += 1

        self.running = (
            keys[pygame.K_LSHIFT]
            and self.sp > 0
        )

        speed = (
            self.run_speed
            if self.running
            else self.normal_speed
        )

        if self.is_tagger:
            speed += 0.7

        # SP 감소
        if self.running:

            self.sp -= 35 * dt

            if self.sp < 0:
                self.sp = 0

        # 대각선 보정
        if dx != 0 and dy != 0:
            dx /= math.sqrt(2)
            dy /= math.sqrt(2)

        move_with_collision(
            self.rect,
            dx * speed,
            dy * speed,
            walls,
            self.screen_rect
        )

    def add_sp(self, amount):

        self.sp += amount

        if self.sp > self.max_sp:
            self.sp = self.max_sp

    def get_current_tile(self):

        row = self.rect.centery // TILE_SIZE
        col = self.rect.centerx // TILE_SIZE

        return get_tile(row, col)

    def draw(self, screen):

        if self.is_tagger:
            color = (255, 80, 80)

        else:
            color = (80, 140, 255)

        # 부쉬 안
        try:
            if self.get_current_tile() == "7":
                color = tuple(
                    max(0, c - 80)
                    for c in color
                )

        except Exception:
            pass

        pygame.draw.rect(
            screen,
            color,
            self.rect
        )

        # SP 바
        bar_width = 32
        bar_height = 5

        sp_ratio = self.sp / self.max_sp

        bg_rect = pygame.Rect(
            self.rect.x,
            self.rect.y - 8,
            bar_width,
            bar_height
        )

        sp_rect = pygame.Rect(
            self.rect.x,
            self.rect.y - 8,
            int(bar_width * sp_ratio),
            bar_height
        )

        pygame.draw.rect(
            screen,
            (50, 50, 50),
            bg_rect
        )

        pygame.draw.rect(
            screen,
            (80, 180, 255),
            sp_rect
        )