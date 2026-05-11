from __future__ import annotations

from dataclasses import dataclass

import pygame

from .assets import load_manual_frames
from .constants import EnemyBulletType, PROJECTILE_SPRITE
from .settings import (
    BOSS_ORB_PROJECTILE_SIZE,
    ENEMY_PROJECTILE_FRAME_SIZE,
    HEAVY_PROJECTILE_SIZE,
    PLAYER_PROJECTILE_FRAME_SIZE,
    PROJECTILE_BOUNDS_MARGIN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from .spritesheet import FrameRect


@dataclass(frozen=True)
class ProjectileAssets:
    player: dict[int, pygame.Surface]
    enemy: dict[EnemyBulletType, pygame.Surface]


def load_projectile_assets() -> ProjectileAssets:
    player_rects = [FrameRect(i * 384, 0, 384, 512) for i in range(4)]
    enemy_rects = [FrameRect(i * 384, 512, 384, 512) for i in range(4)]
    player_frames = load_manual_frames(
        PROJECTILE_SPRITE,
        player_rects,
        PLAYER_PROJECTILE_FRAME_SIZE,
    )
    enemy_frames = load_manual_frames(
        PROJECTILE_SPRITE,
        enemy_rects,
        ENEMY_PROJECTILE_FRAME_SIZE,
    )
    boss_orb = pygame.transform.smoothscale(
        enemy_frames[2],
        BOSS_ORB_PROJECTILE_SIZE,
    ).convert_alpha()
    return ProjectileAssets(
        player={index + 1: frame for index, frame in enumerate(player_frames)},
        enemy={
            EnemyBulletType.BASIC: enemy_frames[0],
            EnemyBulletType.HEAVY: pygame.transform.smoothscale(
                enemy_frames[2],
                HEAVY_PROJECTILE_SIZE,
            ).convert_alpha(),
            EnemyBulletType.BOSS_SMALL: enemy_frames[3],
            EnemyBulletType.BOSS_ORB: boss_orb,
        },
    )


class Projectile(pygame.sprite.Sprite):
    def __init__(
        self,
        image: pygame.Surface,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: int,
        lifetime: float | None = None,
    ) -> None:
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.Vector2(self.rect.center)
        self.velocity = pygame.Vector2(vx, vy)
        self.damage = damage
        self.lifetime = lifetime
        self.age = 0.0

    def update(self, dt: float) -> None:
        self.age += dt
        if self.lifetime is not None and self.age >= self.lifetime:
            self.kill()
            return
        self.position += self.velocity * dt
        self.rect.center = (round(self.position.x), round(self.position.y))
        if (
            self.rect.bottom < -PROJECTILE_BOUNDS_MARGIN
            or self.rect.top > SCREEN_HEIGHT + PROJECTILE_BOUNDS_MARGIN
            or self.rect.right < -PROJECTILE_BOUNDS_MARGIN
            or self.rect.left > SCREEN_WIDTH + PROJECTILE_BOUNDS_MARGIN
        ):
            self.kill()
