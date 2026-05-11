from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .assets import load_grid_frames
from .constants import PLAYER_SHIELD_SPRITE
from .settings import (
    PLAYER_SHIELD_FRAME_COLUMNS,
    PLAYER_SHIELD_FRAME_COUNT,
    PLAYER_SHIELD_FRAME_ROWS,
    PLAYER_SHIELD_FRAME_TIME,
    PLAYER_SHIELD_ALPHA,
    PLAYER_SHIELD_FLASH_ALPHA,
)

if TYPE_CHECKING:
    from .player import Player


def load_shield_frames(size: tuple[int, int]) -> list[pygame.Surface]:
    frames = load_grid_frames(
        PLAYER_SHIELD_SPRITE,
        PLAYER_SHIELD_FRAME_COLUMNS,
        PLAYER_SHIELD_FRAME_ROWS,
        size,
        PLAYER_SHIELD_FRAME_COUNT,
    )
    return [_remove_checker_background(frame) for frame in frames]


def _remove_checker_background(frame: pygame.Surface) -> pygame.Surface:
    clean_frame = frame.convert_alpha()
    for y in range(clean_frame.get_height()):
        for x in range(clean_frame.get_width()):
            r, g, b, alpha = clean_frame.get_at((x, y))
            if alpha == 0:
                continue
            if max(r, g, b) <= 95 and max(r, g, b) - min(r, g, b) <= 14:
                clean_frame.set_at((x, y), (r, g, b, 0))
    return clean_frame


class ShieldVisual:
    def __init__(self, frames: list[pygame.Surface]) -> None:
        self.frames = [self._create_alpha_frame(frame, PLAYER_SHIELD_ALPHA) for frame in frames]
        self.flash_frames = [self._create_flash_frame(frame) for frame in frames]
        self.frame_timer = 0.0
        self.frame_index = 0

    def update(self, dt: float) -> None:
        self.frame_timer += dt
        if self.frame_timer < PLAYER_SHIELD_FRAME_TIME:
            return
        self.frame_timer = 0.0
        self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, surface: pygame.Surface, player: Player) -> None:
        if player.shield <= 0:
            return
        frames = self.flash_frames if player.shield_flash_timer > 0 else self.frames
        image = frames[self.frame_index]
        rect = image.get_rect(center=player.rect.center)
        surface.blit(image, rect)

    def _create_flash_frame(self, frame: pygame.Surface) -> pygame.Surface:
        flash_frame = frame.copy()
        flash_frame.fill((90, 170, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
        flash_frame.set_alpha(PLAYER_SHIELD_FLASH_ALPHA)
        return flash_frame

    def _create_alpha_frame(self, frame: pygame.Surface, alpha: int) -> pygame.Surface:
        alpha_frame = frame.copy()
        alpha_frame.set_alpha(alpha)
        return alpha_frame
