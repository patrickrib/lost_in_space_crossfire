from __future__ import annotations

from dataclasses import dataclass
from math import sin

import pygame

from .assets import load_manual_frames
from .constants import PICKUP_SPRITE, PickupType
from .settings import SCREEN_HEIGHT
from .spritesheet import FrameRect


@dataclass(frozen=True)
class PickupAssets:
    coin: list[pygame.Surface]
    weapon_upgrade: list[pygame.Surface]
    bomb: list[pygame.Surface]
    shield: list[pygame.Surface]

    def frames_for(self, pickup_type: PickupType) -> list[pygame.Surface]:
        if pickup_type is PickupType.COIN:
            return self.coin
        if pickup_type is PickupType.WEAPON_UPGRADE:
            return self.weapon_upgrade
        if pickup_type is PickupType.BOMB:
            return self.bomb
        return self.shield


def load_pickup_assets() -> PickupAssets:
    coin_rects = [FrameRect(i * 256, 0, 256, 330) for i in range(6)]
    upgrade_rects = [FrameRect(i * 384, 330, 384, 340) for i in range(4)]
    bomb_rects = [FrameRect(i * 384, 660, 384, 364) for i in range(4)]
    return PickupAssets(
        coin=load_manual_frames(PICKUP_SPRITE, coin_rects, (30, 30)),
        weapon_upgrade=load_manual_frames(PICKUP_SPRITE, upgrade_rects, (42, 42)),
        bomb=load_manual_frames(PICKUP_SPRITE, bomb_rects, (46, 46)),
        shield=_create_shield_pickup_frames(),
    )


def _create_shield_pickup_frames() -> list[pygame.Surface]:
    frames: list[pygame.Surface] = []
    colors = ((80, 170, 255), (105, 205, 255), (145, 230, 255), (105, 205, 255))
    for color in colors:
        frame = pygame.Surface((42, 42), pygame.SRCALPHA)
        pygame.draw.circle(frame, (20, 55, 95, 150), (21, 21), 19)
        points = [(21, 6), (34, 12), (31, 28), (21, 36), (11, 28), (8, 12)]
        pygame.draw.polygon(frame, color, points)
        pygame.draw.polygon(frame, (235, 250, 255), points, 2)
        pygame.draw.line(frame, (235, 250, 255), (21, 10), (21, 31), 2)
        frames.append(frame.convert_alpha())
    return frames


class Pickup(pygame.sprite.Sprite):
    def __init__(
        self,
        pickup_type: PickupType,
        frames: list[pygame.Surface],
        x: float,
        y: float,
    ) -> None:
        super().__init__()
        self.pickup_type = pickup_type
        self.frames = frames
        self.image = frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.Vector2(self.rect.center)
        self.base_x = x
        self.age = 0.0
        self.frame_timer = 0.0
        self.frame_index = 0
        self.speed = 95.0

    def update(self, dt: float) -> None:
        self.age += dt
        self.frame_timer += dt
        self.position.y += self.speed * dt
        self.position.x = self.base_x + sin(self.age * 4.0) * 18.0
        if self.frame_timer >= 0.10:
            self.frame_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            center = self.rect.center
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect(center=center)
        self.rect.center = (round(self.position.x), round(self.position.y))
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()
