from __future__ import annotations

from dataclasses import dataclass
from math import cos

import pygame

from .assets import load_grid_frames
from .constants import ENEMY_SPRITES, EnemyBulletType, EnemyType, MovementPattern
from .projectile import Projectile, ProjectileAssets
from .settings import (
    ENEMY_ATTACK_FLASH_SECONDS,
    ENEMY_ATTACK_FRAME_LEAD_SECONDS,
    ENEMY_BANK_SPEED_THRESHOLD,
    ENEMY_DEFAULT_AIM_DIRECTION,
    ENEMY_DESPAWN_MARGIN,
    ENEMY_EXIT_VERTICAL_SPEED,
    ENEMY_FRAME_SIZES,
    ENEMY_HEAVY_SIDE_ANGLES,
    ENEMY_HEAVY_SIDE_SPEED_MULTIPLIER,
    ENEMY_HEAVY_SIDE_VOLLEY_INTERVAL,
    ENEMY_HOVER_VERTICAL_SPEED,
    ENEMY_INITIAL_SHOOT_TIMER_FACTOR,
    ENEMY_PROJECTILE_Y_OFFSET,
    ENEMY_SHOOTER_FAN_ANGLES,
    ENEMY_SHOOTER_FAN_INTERVAL,
    ENEMY_STATS,
    ENEMY_TRACKING_RESPONSE,
    ENEMY_ZIGZAG_AIMED_SPREAD_ANGLES,
    ENEMY_ZIGZAG_DOWNWARD_SPREAD_ANGLES,
    ENEMY_ZIGZAG_TRACKING_MULTIPLIER,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


@dataclass(frozen=True)
class EnemyConfig:
    enemy_type: EnemyType
    hp: int
    score: int
    vertical_speed: float
    movement: MovementPattern
    shoot_interval: float
    bullet_speed: float
    bullet_type: EnemyBulletType
    horizontal_track_speed: float
    max_horizontal_speed: float
    target_y: float = 0.0
    hover_duration: float = 0.0
    wave_amplitude: float = 0.0
    wave_frequency: float = 0.0


ENEMY_CONFIGS = {
    EnemyType.SCOUT: EnemyConfig(
        EnemyType.SCOUT,
        ENEMY_STATS["SCOUT"]["hp"],
        ENEMY_STATS["SCOUT"]["score"],
        ENEMY_STATS["SCOUT"]["vertical_speed"],
        MovementPattern.STRAIGHT_DOWN,
        ENEMY_STATS["SCOUT"]["shoot_interval"],
        ENEMY_STATS["SCOUT"]["bullet_speed"],
        EnemyBulletType.BASIC,
        ENEMY_STATS["SCOUT"]["horizontal_track_speed"],
        ENEMY_STATS["SCOUT"]["max_horizontal_speed"],
    ),
    EnemyType.ZIGZAG: EnemyConfig(
        EnemyType.ZIGZAG,
        ENEMY_STATS["ZIGZAG"]["hp"],
        ENEMY_STATS["ZIGZAG"]["score"],
        ENEMY_STATS["ZIGZAG"]["vertical_speed"],
        MovementPattern.ZIGZAG,
        ENEMY_STATS["ZIGZAG"]["shoot_interval"],
        ENEMY_STATS["ZIGZAG"]["bullet_speed"],
        EnemyBulletType.BASIC,
        ENEMY_STATS["ZIGZAG"]["horizontal_track_speed"],
        ENEMY_STATS["ZIGZAG"]["max_horizontal_speed"],
        wave_amplitude=ENEMY_STATS["ZIGZAG"]["wave_amplitude"],
        wave_frequency=ENEMY_STATS["ZIGZAG"]["wave_frequency"],
    ),
    EnemyType.SHOOTER: EnemyConfig(
        EnemyType.SHOOTER,
        ENEMY_STATS["SHOOTER"]["hp"],
        ENEMY_STATS["SHOOTER"]["score"],
        ENEMY_STATS["SHOOTER"]["vertical_speed"],
        MovementPattern.SLOW_DOWN,
        ENEMY_STATS["SHOOTER"]["shoot_interval"],
        ENEMY_STATS["SHOOTER"]["bullet_speed"],
        EnemyBulletType.BOSS_SMALL,
        ENEMY_STATS["SHOOTER"]["horizontal_track_speed"],
        ENEMY_STATS["SHOOTER"]["max_horizontal_speed"],
        target_y=ENEMY_STATS["SHOOTER"]["target_y"],
        hover_duration=ENEMY_STATS["SHOOTER"]["hover_duration"],
    ),
    EnemyType.HEAVY: EnemyConfig(
        EnemyType.HEAVY,
        ENEMY_STATS["HEAVY"]["hp"],
        ENEMY_STATS["HEAVY"]["score"],
        ENEMY_STATS["HEAVY"]["vertical_speed"],
        MovementPattern.STRAIGHT_DOWN,
        ENEMY_STATS["HEAVY"]["shoot_interval"],
        ENEMY_STATS["HEAVY"]["bullet_speed"],
        EnemyBulletType.HEAVY,
        ENEMY_STATS["HEAVY"]["horizontal_track_speed"],
        ENEMY_STATS["HEAVY"]["max_horizontal_speed"],
    ),
}


def rotate_enemy_frame(frame: pygame.Surface) -> pygame.Surface:
    return pygame.transform.rotate(frame, 180).convert_alpha()


def load_enemy_assets() -> dict[EnemyType, list[pygame.Surface]]:
    return {
        enemy_type: [
            rotate_enemy_frame(frame)
            for frame in load_grid_frames(path, 4, 1, ENEMY_FRAME_SIZES[enemy_type.name], 4)
        ]
        for enemy_type, path in ENEMY_SPRITES.items()
    }


class Enemy(pygame.sprite.Sprite):
    def __init__(
        self,
        config: EnemyConfig,
        frames: list[pygame.Surface],
        x: float,
        y: float,
    ) -> None:
        super().__init__()
        self.config = config
        self.frames = frames
        self.image = frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.Vector2(self.rect.center)
        self.hp = config.hp
        self.age = 0.0
        self.hover_timer = 0.0
        self.shoot_timer = config.shoot_interval * ENEMY_INITIAL_SHOOT_TIMER_FACTOR
        self.volley_index = 0
        self.attack_flash_timer = 0.0
        self.velocity = pygame.Vector2(0, config.vertical_speed)

    def update(self, dt: float, player_center: tuple[int, int]) -> None:
        self.age += dt
        self.attack_flash_timer = max(0.0, self.attack_flash_timer - dt)
        self.velocity = self._calculate_velocity(dt, player_center)

        self.position += self.velocity * dt
        half_width = self.rect.width / 2
        self.position.x = max(half_width, min(SCREEN_WIDTH - half_width, self.position.x))
        self.rect.center = (round(self.position.x), round(self.position.y))
        self._update_visual_frame()
        if self.rect.top > SCREEN_HEIGHT + ENEMY_DESPAWN_MARGIN:
            self.kill()

    def _calculate_velocity(self, dt: float, player_center: tuple[int, int]) -> pygame.Vector2:
        player_x, _ = player_center
        direction_to_player = player_x - self.position.x
        tracking = max(
            -self.config.horizontal_track_speed,
            min(
                self.config.horizontal_track_speed,
                direction_to_player * ENEMY_TRACKING_RESPONSE,
            ),
        )
        vertical_speed = self.config.vertical_speed

        if self.config.movement is MovementPattern.ZIGZAG:
            wave_speed = (
                cos(self.age * self.config.wave_frequency)
                * self.config.wave_amplitude
                * self.config.wave_frequency
            )
            horizontal_speed = wave_speed + tracking * ENEMY_ZIGZAG_TRACKING_MULTIPLIER
        elif self.config.movement is MovementPattern.SLOW_DOWN:
            if self.position.y < self.config.target_y:
                vertical_speed = self.config.vertical_speed
            elif self.hover_timer < self.config.hover_duration:
                self.hover_timer += dt
                vertical_speed = ENEMY_HOVER_VERTICAL_SPEED
            else:
                vertical_speed = ENEMY_EXIT_VERTICAL_SPEED
            horizontal_speed = tracking
        else:
            horizontal_speed = tracking

        horizontal_speed = max(
            -self.config.max_horizontal_speed,
            min(self.config.max_horizontal_speed, horizontal_speed),
        )
        return pygame.Vector2(horizontal_speed, vertical_speed)

    def _update_visual_frame(self) -> None:
        if self.attack_flash_timer > 0 or self.shoot_timer < ENEMY_ATTACK_FRAME_LEAD_SECONDS:
            frame_index = 3
        elif self.velocity.x < -ENEMY_BANK_SPEED_THRESHOLD:
            frame_index = 1
        elif self.velocity.x > ENEMY_BANK_SPEED_THRESHOLD:
            frame_index = 2
        else:
            frame_index = 0

        center = self.rect.center
        self.image = self.frames[frame_index]
        self.rect = self.image.get_rect(center=center)

    def take_damage(self, amount: int) -> bool:
        self.hp -= amount
        return self.hp <= 0

    def try_shoot(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
    ) -> list[Projectile]:
        raise NotImplementedError

    def _start_shot_if_ready(self, dt: float) -> bool:
        self.shoot_timer -= dt
        if self.shoot_timer > 0:
            return False
        self.shoot_timer = self.config.shoot_interval
        self.volley_index += 1
        self.attack_flash_timer = ENEMY_ATTACK_FLASH_SECONDS
        return True

    def _create_aimed_projectile(
        self,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
        bullet_type: EnemyBulletType,
        speed: float | None = None,
    ) -> Projectile:
        direction = pygame.Vector2(
            player_center[0] - self.rect.centerx,
            player_center[1] - self.rect.centery,
        )
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(ENEMY_DEFAULT_AIM_DIRECTION)
        velocity = direction * (speed or self.config.bullet_speed)
        image = projectile_assets.enemy[bullet_type]
        return Projectile(
            image,
            self.rect.centerx,
            self.rect.bottom - ENEMY_PROJECTILE_Y_OFFSET,
            velocity.x,
            velocity.y,
            1,
        )

    def _create_aimed_spread(
        self,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
        bullet_type: EnemyBulletType,
        angles: list[float],
        speed: float,
    ) -> list[Projectile]:
        base_direction = pygame.Vector2(
            player_center[0] - self.rect.centerx,
            player_center[1] - self.rect.centery,
        )
        if base_direction.length_squared() > 0:
            base_direction = base_direction.normalize()
        else:
            base_direction = pygame.Vector2(ENEMY_DEFAULT_AIM_DIRECTION)
        image = projectile_assets.enemy[bullet_type]
        bullets = []
        for angle in angles:
            velocity = base_direction.rotate(angle) * speed
            bullets.append(
                Projectile(
                    image,
                    self.rect.centerx,
                    self.rect.bottom - ENEMY_PROJECTILE_Y_OFFSET,
                    velocity.x,
                    velocity.y,
                    1,
                )
            )
        return bullets

    def _create_downward_spread(
        self,
        projectile_assets: ProjectileAssets,
        bullet_type: EnemyBulletType,
        angles: list[float],
        speed: float,
    ) -> list[Projectile]:
        image = projectile_assets.enemy[bullet_type]
        bullets = []
        for angle in angles:
            velocity = pygame.Vector2(ENEMY_DEFAULT_AIM_DIRECTION).rotate(angle) * speed
            bullets.append(
                Projectile(
                    image,
                    self.rect.centerx,
                    self.rect.bottom - ENEMY_PROJECTILE_Y_OFFSET,
                    velocity.x,
                    velocity.y,
                    1,
                )
            )
        return bullets


class ScoutEnemy(Enemy):
    def try_shoot(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
    ) -> list[Projectile]:
        if not self._start_shot_if_ready(dt):
            return []
        return [
            self._create_aimed_projectile(
                projectile_assets,
                player_center,
                EnemyBulletType.BASIC,
            )
        ]


class ZigzagEnemy(Enemy):
    def try_shoot(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
    ) -> list[Projectile]:
        if not self._start_shot_if_ready(dt):
            return []
        if self.volley_index % 2 == 0:
            return self._create_downward_spread(
                projectile_assets,
                EnemyBulletType.BASIC,
                ENEMY_ZIGZAG_DOWNWARD_SPREAD_ANGLES,
                self.config.bullet_speed,
            )
        return self._create_aimed_spread(
            projectile_assets,
            player_center,
            EnemyBulletType.BASIC,
            ENEMY_ZIGZAG_AIMED_SPREAD_ANGLES,
            self.config.bullet_speed,
        )


class ShooterEnemy(Enemy):
    def try_shoot(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
    ) -> list[Projectile]:
        if not self._start_shot_if_ready(dt):
            return []
        if self.volley_index % ENEMY_SHOOTER_FAN_INTERVAL == 0:
            return self._create_aimed_spread(
                projectile_assets,
                player_center,
                EnemyBulletType.BOSS_SMALL,
                ENEMY_SHOOTER_FAN_ANGLES,
                self.config.bullet_speed,
            )
        return [
            self._create_aimed_projectile(
                projectile_assets,
                player_center,
                EnemyBulletType.BOSS_SMALL,
            )
        ]


class HeavyEnemy(Enemy):
    def try_shoot(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        player_center: tuple[int, int],
    ) -> list[Projectile]:
        if not self._start_shot_if_ready(dt):
            return []
        bullets = [
            self._create_aimed_projectile(
                projectile_assets,
                player_center,
                EnemyBulletType.HEAVY,
            )
        ]
        if self.volley_index % ENEMY_HEAVY_SIDE_VOLLEY_INTERVAL == 0:
            bullets.extend(
                self._create_aimed_spread(
                    projectile_assets,
                    player_center,
                    EnemyBulletType.BASIC,
                    ENEMY_HEAVY_SIDE_ANGLES,
                    self.config.bullet_speed * ENEMY_HEAVY_SIDE_SPEED_MULTIPLIER,
                )
            )
        return bullets


ENEMY_CLASSES = {
    EnemyType.SCOUT: ScoutEnemy,
    EnemyType.ZIGZAG: ZigzagEnemy,
    EnemyType.SHOOTER: ShooterEnemy,
    EnemyType.HEAVY: HeavyEnemy,
}


def create_enemy(
    enemy_type: EnemyType,
    assets: dict[EnemyType, list[pygame.Surface]],
    x: float,
    y: float,
) -> Enemy:
    enemy_class = ENEMY_CLASSES[enemy_type]
    return enemy_class(ENEMY_CONFIGS[enemy_type], assets[enemy_type], x, y)
