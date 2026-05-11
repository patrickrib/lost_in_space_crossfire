from __future__ import annotations

import pygame

from .assets import load_grid_frames
from .constants import PLAYER_SPRITES
from .projectile import Projectile, ProjectileAssets
from .settings import (
    BOMB_COOLDOWN_SECONDS,
    MAX_BOMBS,
    MAX_WEAPON_LEVEL,
    PLAYER_INVULNERABILITY_SECONDS,
    PLAYER_LIVES,
    PLAYER_HITBOX_OFFSET,
    PLAYER_HITBOX_SIZE,
    PLAYER_MAX_SHIELD,
    PLAYER_SHIELD_FLASH_SECONDS,
    PLAYER_SHIELD_HIT_DAMAGE,
    PLAYER_SHIELD_INVULNERABILITY_SECONDS,
    PLAYER_SPEED,
    PLAYER_STARTING_SHIELD,
    PLAYER_WEAPON_LEVEL_LOSS_ON_HIT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WEAPON_COOLDOWN_BY_LEVEL,
    WEAPON_DAMAGE_BY_LEVEL,
)


def load_player_assets() -> dict[int, list[pygame.Surface]]:
    return {
        level: load_grid_frames(path, 4, 1, (66, 70), 4)
        for level, path in PLAYER_SPRITES.items()
    }


class Player(pygame.sprite.Sprite):
    def __init__(self, assets: dict[int, list[pygame.Surface]]) -> None:
        super().__init__()
        self.assets = assets
        self.weapon_level = 1
        self.bomb_count = 0
        self.lives = PLAYER_LIVES
        self.shield = PLAYER_STARTING_SHIELD
        self.score = 0
        self.last_shot_time = -10.0
        self.last_bomb_time = -BOMB_COOLDOWN_SECONDS
        self.invulnerability_timer = 0.0
        self.shield_flash_timer = 0.0
        self.image = self.assets[self.weapon_level][0]
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 82))
        self.position = pygame.Vector2(self.rect.center)
        self.hitbox = pygame.Rect(0, 0, *PLAYER_HITBOX_SIZE)
        self._update_hitbox()

    def reset_for_new_game(self) -> None:
        self.weapon_level = 1
        self.bomb_count = 0
        self.lives = PLAYER_LIVES
        self.shield = PLAYER_STARTING_SHIELD
        self.score = 0
        self.last_shot_time = -10.0
        self.last_bomb_time = -BOMB_COOLDOWN_SECONDS
        self.invulnerability_timer = 0.0
        self.shield_flash_timer = 0.0
        self.position = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 82)
        self._set_frame(0)
        self._update_hitbox()

    def reset_for_checkpoint(self, score: int, weapon_level: int, bomb_count: int) -> None:
        self.weapon_level = max(1, min(MAX_WEAPON_LEVEL, weapon_level))
        self.bomb_count = max(0, min(MAX_BOMBS, bomb_count))
        self.lives = PLAYER_LIVES
        self.shield = PLAYER_STARTING_SHIELD
        self.score = score
        self.last_shot_time = -10.0
        self.last_bomb_time = -BOMB_COOLDOWN_SECONDS
        self.invulnerability_timer = PLAYER_INVULNERABILITY_SECONDS
        self.shield_flash_timer = 0.0
        self.position = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 82)
        self._set_frame(0)
        self._update_hitbox()

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y += 1
        if direction.length_squared() > 0:
            direction = direction.normalize()

        self.position += direction * PLAYER_SPEED * dt
        half_width = self.rect.width / 2
        half_height = self.rect.height / 2
        self.position.x = max(half_width, min(SCREEN_WIDTH - half_width, self.position.x))
        self.position.y = max(half_height + 42, min(SCREEN_HEIGHT - half_height, self.position.y))

        if direction.x < -0.2:
            self._set_frame(1)
        elif direction.x > 0.2:
            self._set_frame(2)
        elif direction.y < -0.2:
            self._set_frame(3)
        else:
            self._set_frame(0)

        if self.invulnerability_timer > 0:
            self.invulnerability_timer = max(0.0, self.invulnerability_timer - dt)
            self.image.set_alpha(95 if int(self.invulnerability_timer * 10) % 2 == 0 else 210)
        else:
            self.image.set_alpha(255)
        if self.shield_flash_timer > 0:
            self.shield_flash_timer = max(0.0, self.shield_flash_timer - dt)

        self.rect.center = (round(self.position.x), round(self.position.y))
        self._update_hitbox()

    def _set_frame(self, frame_index: int) -> None:
        center = self.rect.center
        self.image = self.assets[self.weapon_level][frame_index]
        self.rect = self.image.get_rect(center=center)
        self._update_hitbox()

    def _update_hitbox(self) -> None:
        self.hitbox.center = (
            self.rect.centerx + PLAYER_HITBOX_OFFSET[0],
            self.rect.centery + PLAYER_HITBOX_OFFSET[1],
        )

    def can_shoot(self, now: float) -> bool:
        return now - self.last_shot_time >= WEAPON_COOLDOWN_BY_LEVEL[self.weapon_level]

    def shoot(self, now: float, projectile_assets: ProjectileAssets) -> list[Projectile]:
        if not self.can_shoot(now):
            return []
        self.last_shot_time = now
        damage = WEAPON_DAMAGE_BY_LEVEL[self.weapon_level]
        image = projectile_assets.player[self.weapon_level]
        x = self.rect.centerx
        y = self.rect.top + 8
        patterns = {
            1: [(0, 0, -520)],
            2: [(-12, 0, -540), (12, 0, -540)],
            3: [(0, 0, -560), (-18, -95, -535), (18, 95, -535)],
            4: [
                (0, 0, -585),
                (-18, -90, -560),
                (18, 90, -560),
                (-32, -155, -530),
                (32, 155, -530),
            ],
        }
        return [
            Projectile(image, x + offset, y, vx, vy, damage)
            for offset, vx, vy in patterns[self.weapon_level]
        ]

    def add_weapon_upgrade(self) -> bool:
        if self.weapon_level >= MAX_WEAPON_LEVEL:
            return False
        self.weapon_level += 1
        self._set_frame(0)
        return True

    def set_weapon_level(self, weapon_level: int) -> None:
        self.weapon_level = max(1, min(MAX_WEAPON_LEVEL, weapon_level))
        self._set_frame(0)

    def add_bomb(self) -> bool:
        if self.bomb_count >= MAX_BOMBS:
            return False
        self.bomb_count += 1
        return True

    def add_shield(self, amount: int) -> bool:
        if self.shield >= PLAYER_MAX_SHIELD:
            return False
        self.shield = min(PLAYER_MAX_SHIELD, self.shield + amount)
        return True

    def bomb_cooldown_remaining(self, now: float) -> float:
        return max(0.0, BOMB_COOLDOWN_SECONDS - (now - self.last_bomb_time))

    def can_use_bomb(self, now: float) -> bool:
        return self.bomb_count > 0 and self.bomb_cooldown_remaining(now) <= 0

    def mark_bomb_used(self, now: float) -> None:
        self.bomb_count -= 1
        self.last_bomb_time = now

    def take_hit(self) -> bool:
        if self.invulnerability_timer > 0:
            return False
        if self.shield > 0:
            self.shield = max(0, self.shield - PLAYER_SHIELD_HIT_DAMAGE)
            self.invulnerability_timer = PLAYER_SHIELD_INVULNERABILITY_SECONDS
            self.shield_flash_timer = PLAYER_SHIELD_FLASH_SECONDS
            return False
        self.lives -= 1
        self.weapon_level = max(1, self.weapon_level - PLAYER_WEAPON_LEVEL_LOSS_ON_HIT)
        self.shield = PLAYER_STARTING_SHIELD
        self.invulnerability_timer = PLAYER_INVULNERABILITY_SECONDS
        self._set_frame(0)
        return True
