import math
import importlib
import pygame

from game.core.collision import move_with_collision
from game.core.map import TILE_SIZE, get_tile


class Character:
    def __init__(self, number, x, y, screen_width, screen_height, ai_index):
        self.number = number
        self.name = f"AI {number}"

        self.rect = pygame.Rect(x, y, 32, 32)

        self.screen_rect = pygame.Rect(
            0,
            0,
            screen_width,
            screen_height
        )

        module = importlib.import_module(
            f"ai.ai_{ai_index}.brain"
        )

        self.brain = module.Brain()

        self.normal_speed = 3
        self.run_speed = 5.5

        self.tagger_normal_speed = 3.7
        self.tagger_run_speed = 6.2

        self.sp = 50
        self.max_sp = 100

        self.running = False

        self.is_tagger = False

        self.hp = 100

        self.stun_timer = 0

        self.action = {
            "dx": 0,
            "dy": 0,
            "run": False,
        }

        self.think_timer = 0
        self.think_delay = 0.15

    def update(self, dt, walls, map_data, players, others):

        if self.stun_timer > 0:
            self.stun_timer -= dt
            self.running = False
            return

        self.think_timer -= dt

        # AI 판단
        if self.think_timer <= 0:

            info = self.make_info(
                map_data,
                players
            )

            self.action = self.brain.decide(info)

            self.think_timer = self.think_delay

        dx = self.action.get("dx", 0)
        dy = self.action.get("dy", 0)

        self.running = self.action.get("run", False)

        if self.sp <= 0:
            self.running = False

        # 속도 계산
        if self.is_tagger:
            speed = (
                self.tagger_run_speed
                if self.running
                else self.tagger_normal_speed
            )

        else:
            speed = (
                self.run_speed
                if self.running
                else self.normal_speed
            )

        # 달리기 SP 감소
        if self.running:

            self.sp -= 35 * dt

            if self.sp < 0:
                self.sp = 0

        # 대각선 보정
        if dx != 0 and dy != 0:
            dx /= math.sqrt(2)
            dy /= math.sqrt(2)

        old_x = self.rect.x
        old_y = self.rect.y

        move_with_collision(
            self.rect,
            dx * speed,
            dy * speed,
            walls,
            self.screen_rect
        )

        # 벽에 막히면 즉시 재판단
        if self.rect.x == old_x and self.rect.y == old_y:
            self.think_timer = 0

    def make_info(self, map_data, players):
    
        # 자기 정보
        self_info = {
        
            "center_x": self.rect.centerx,
            "center_y": self.rect.centery,
    
            "hp": self.hp,
            "sp": self.sp,
    
            "is_tagger": self.is_tagger,
        }
    
        # 플레이어 정보
        players_info = []
    
        for player in players:
        
            players_info.append({
            
                "name": player.name,
    
                "center_x": player.rect.centerx,
                "center_y": player.rect.centery,
    
                "is_tagger": player.is_tagger,
            })
    
        return {
            "map": map_data,
    
            "self": self_info,
    
            "players": players_info,
        }
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
            color = (255, 60, 60)

        else:
            color = (60, 220, 100)

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