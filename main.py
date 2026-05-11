# generated file
import pygame
import sys
import time
import os

from game.core.map import (
    draw_map,
    WALLS,
    MAP_DATA,
)

from game.core.manager import GameManager


# 관전 모드에서는 1번 worker 모델 사용
os.environ["PROCESS_ID"] = "1"

pygame.init()

WIDTH = 900
HEIGHT = 600

FPS = 60

AUTO_RESTART = True

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "AI 관전 모드 - P1 모델"
)

clock = pygame.time.Clock()

font = pygame.font.SysFont(
    "malgungothic",
    24
)


def create_game():

    return GameManager(
        WIDTH,
        HEIGHT,
        ai_count=4,
        use_player=False
    )


game = create_game()

game_count = 0

last_restart_time = 0


while True:

    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            pygame.quit()
            sys.exit()

    game.update(
        dt,
        WALLS,
        MAP_DATA
    )

    screen.fill((30, 30, 30))

    draw_map(screen)

    game.draw(screen)

    game_text = font.render(
        f"GAME : {game_count}",
        True,
        (255, 255, 255)
    )

    screen.blit(
        game_text,
        (10, 10)
    )

    model_text = font.render(
        "MODEL : P1",
        True,
        (120, 220, 255)
    )

    screen.blit(
        model_text,
        (10, 40)
    )

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

        screen.blit(
            winner_text,
            (10, 70)
        )

        current_time = time.time()

        if (
            AUTO_RESTART
            and current_time - last_restart_time > 2
        ):

            game_count += 1

            last_restart_time = current_time

            game = create_game()

    pygame.display.flip()