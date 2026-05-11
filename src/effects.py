from __future__ import annotations

import pygame

from .assets import load_grid_frames
from .constants import BOMB_EXPLOSION_SPRITE, ENEMY_EXPLOSION_SPRITE


class AnimatedEffect(pygame.sprite.Sprite):
    def __init__(
        self,
        frames: list[pygame.Surface],
        center: tuple[int, int],
        frame_time: float = 0.06,
    ) -> None:
        super().__init__()
        self.frames = frames
        self.frame_time = frame_time
        self.elapsed = 0.0
        self.index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=center)

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed < self.frame_time:
            return
        self.elapsed = 0.0
        self.index += 1
        if self.index >= len(self.frames):
            self.kill()
            return
        center = self.rect.center
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(center=center)


def load_enemy_explosion_frames() -> list[pygame.Surface]:
    return load_grid_frames(ENEMY_EXPLOSION_SPRITE, 3, 2, (74, 74), 6)


def load_bomb_explosion_frames() -> list[pygame.Surface]:
    return load_grid_frames(BOMB_EXPLOSION_SPRITE, 3, 2, (260, 260), 6)
