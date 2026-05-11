# generated file
import pygame
import sys
import time
import os

# 관전/플레이에서는 latest 모델 우선 사용
os.environ["PROCESS_ID"] = "1"

from game.core.map import draw_map, WALLS, MAP_DATA
from game.core.manager import GameManager


pygame.init()

WIDTH = 900
HEIGHT = 600
FPS = 60

AUTO_RESTART = True
RESTART_DELAY = 2.0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI 3명 + 플레이어 1명")

clock = pygame.time.Clock()

font = pygame.font.SysFont("malgungothic", 24)


def create_game():
    return GameManager(
        WIDTH,
        HEIGHT,
        ai_count=3,
        use_player=True
    )


game = create_game()

game_count = 1
game_over_time = None


while True:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    game.update(dt, WALLS, MAP_DATA)

    screen.fill((30, 30, 30))

    draw_map(screen)
    game.draw(screen)

    game_text = font.render(
        f"GAME : {game_count}",
        True,
        (255, 255, 255)
    )
    screen.blit(game_text, (10, 10))

    if game.game_over:
        if game.winner:
            winner_name = game.winner.name
        else:
            winner_name = "없음"

        winner_text = font.render(
            f"WINNER : {winner_name}",
            True,
            (255, 255, 0)
        )
        screen.blit(winner_text, (10, 40))

        if game_over_time is None:
            game_over_time = time.time()

        if AUTO_RESTART and time.time() - game_over_time >= RESTART_DELAY:
            game_count += 1
            game_over_time = None
            game = create_game()

    pygame.display.flip()