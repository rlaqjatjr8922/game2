# generated file
import random

from game.core.ui import draw_text
from game.entity.character import Character
from game.entity.player import Player
from game.system.sp_system import SPSystem
from game.system.box_system import BoxSystem


class GameManager:
    def __init__(self, screen_width, screen_height, ai_count=4, use_player=False):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.game_over = False
        self.time = 0
        self.winner = None

        self.characters = []

        spawn_points = [
            (100, 100),
            (750, 100),
            (150, 480),
            (760, 480),
        ]

        for i in range(ai_count):
            x, y = spawn_points[i]

            character = Character(
                number=i + 1,
                x=x,
                y=y,
                screen_width=screen_width,
                screen_height=screen_height,
                ai_index=i + 1
            )

            self.characters.append(character)

        if use_player:
            x, y = spawn_points[len(self.characters)]

            player = Player(
                x=x,
                y=y,
                screen_width=screen_width,
                screen_height=screen_height
            )

            self.characters.append(player)

        self.tagger = random.choice(self.characters)
        self.tagger.is_tagger = True
        self.tagger.hp = 100

        self.sp_system = SPSystem()
        self.box_system = BoxSystem()

    def update(self, dt, walls, map_data):
        if self.game_over:
            return

        self.time += dt

        for character in self.characters:
            if character.hp <= 0:
                continue

            others = [
                other for other in self.characters
                if other != character and other.hp > 0
            ]

            character.update(
                dt=dt,
                walls=walls,
                map_data=map_data,
                players=self.characters,
                others=others
            )

        self.sp_system.update(self.characters)
        self.box_system.update(self.characters, dt)
        self.update_tagger(dt)
        self.check_winner()

    def update_tagger(self, dt):
        if self.tagger.hp <= 0:
            self.tagger.hp = 0
            self.pass_tagger_to_alive()
            return

        self.tagger.hp -= dt * 1

        if self.tagger.hp <= 0:
            self.tagger.hp = 0
            self.pass_tagger_to_alive()
            return

        if self.tagger.stun_timer > 0:
            return

        for character in self.characters:
            if character == self.tagger:
                continue

            if character.hp <= 0:
                continue

            if self.tagger.rect.colliderect(character.rect):
                self.change_tagger(character)
                break

    def pass_tagger_to_alive(self):
        alive_players = [
            c for c in self.characters
            if c.hp > 0 and c != self.tagger
        ]

        self.tagger.is_tagger = False

        if len(alive_players) <= 0:
            self.game_over = True
            self.winner = None
            return

        new_tagger = random.choice(alive_players)

        self.tagger = new_tagger
        self.tagger.is_tagger = True
        self.tagger.stun_timer = 0.5

        self.check_winner()

    def change_tagger(self, new_tagger):
        self.tagger.is_tagger = False

        self.tagger = new_tagger
        self.tagger.is_tagger = True
        self.tagger.stun_timer = 0.5

    def check_winner(self):
        alive_players = [
            c for c in self.characters
            if c.hp > 0
        ]

        if len(alive_players) <= 1:
            self.game_over = True

            if alive_players:
                self.winner = alive_players[0]
            else:
                self.winner = None

    def draw(self, screen):
        self.box_system.draw(screen)

        for character in self.characters:
            if character.hp > 0:
                character.draw(screen)

        self.draw_ui(screen)

    def draw_ui(self, screen):
        draw_text(screen, f"술래: {self.tagger.name}", 20, 20)
        draw_text(screen, f"술래 HP: {int(self.tagger.hp)}", 20, 55)
        draw_text(screen, f"시간: {int(self.time)}초", 20, 90)

        alive_count = len([
            c for c in self.characters
            if c.hp > 0
        ])

        draw_text(screen, f"생존: {alive_count}명", 20, 125)

        if self.game_over:
            if self.winner:
                text = f"게임 종료! 승리: {self.winner.name}"
            else:
                text = "게임 종료! 승리자 없음"

            draw_text(
                screen,
                text,
                300,
                280,
                (255, 80, 80)
            )