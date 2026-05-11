# generated file
import pygame

pygame.font.init()

FONT = pygame.font.SysFont("malgungothic", 28)


def draw_text(screen, text, x, y, color=(255, 255, 255)):
    img = FONT.render(str(text), True, color)
    screen.blit(img, (x, y))