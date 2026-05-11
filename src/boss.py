from __future__ import annotations

from math import sin

import pygame

from .assets import load_grid_frames
from .bullet_patterns import (
    BulletPatternConfig,
    BulletSpawn,
    lane_pattern_with_moving_gap,
    radial_burst,
    sweeping_fan,
)
from .constants import BOSS_SPRITE, BossAttackState, EnemyBulletType
from .projectile import Projectile, ProjectileAssets
from .settings import (
    BOSS_BASE_FRAME_SIZE,
    BOSS_CENTER_MOVE_SPEED,
    BOSS_CENTER_Y,
    BOSS_ENTER_SPEED,
    BOSS_FRAME_ATTACK,
    BOSS_FRAME_BANK_LEFT,
    BOSS_FRAME_BANK_RIGHT,
    BOSS_FRAME_CHARGE,
    BOSS_FRAME_IDLE,
    BOSS_HP,
    BOSS_INITIAL_VOLLEY_TIMER,
    BOSS_PROJECTILE_DAMAGE,
    BOSS_RADIAL_ATTACK_FLASH_SECONDS,
    BOSS_RADIAL_BULLET_COUNT,
    BOSS_RADIAL_BULLET_LIFETIME,
    BOSS_RADIAL_BULLET_SPEED,
    BOSS_RADIAL_CHARGE_SECONDS,
    BOSS_RADIAL_INTERVAL_SECONDS,
    BOSS_RETURN_MOVE_SPEED,
    BOSS_RETURN_REACHED_DISTANCE,
    BOSS_CENTER_REACHED_DISTANCE,
    BOSS_LANE_PATTERN_INTERVAL,
    BOSS_SCALE,
    BOSS_SPRITESHEET_COLUMNS,
    BOSS_SPRITESHEET_FRAME_COUNT,
    BOSS_SPRITESHEET_ROWS,
    BOSS_SWEEP_ATTACK_FLASH_SECONDS,
    BOSS_SWEEP_BULLET_LIFETIME,
    BOSS_SWEEP_BULLET_SPEED,
    BOSS_SWEEP_BOB_AMPLITUDE,
    BOSS_SWEEP_BOB_FREQUENCY,
    BOSS_SWEEP_EDGE_PADDING,
    BOSS_SWEEP_FAN_ANGLE_END,
    BOSS_SWEEP_FAN_ANGLE_START,
    BOSS_SWEEP_FAN_BULLET_COUNT,
    BOSS_SWEEP_LANES,
    BOSS_SWEEP_RESUME_VOLLEY_TIMER,
    BOSS_SWEEP_SIDE_MARGIN,
    BOSS_SWEEP_SPEED,
    BOSS_SWEEP_VOLLEY_INTERVAL,
    BOSS_SWEEP_Y,
    BOSS_TARGET_EPSILON_DISTANCE,
    BOSS_VISUAL_BANK_SPEED_THRESHOLD,
    BOSS_PROJECTILE_Y_OFFSET,
    MAX_BOSS_BULLETS,
    SCREEN_WIDTH,
)


def rotate_enemy_frame(frame: pygame.Surface) -> pygame.Surface:
    return pygame.transform.rotate(frame, 180).convert_alpha()


def scale_surface(surface: pygame.Surface, scale: float) -> pygame.Surface:
    width = int(surface.get_width() * scale)
    height = int(surface.get_height() * scale)
    return pygame.transform.smoothscale(surface, (width, height)).convert_alpha()


def load_boss_frames() -> list[pygame.Surface]:
    frames = load_grid_frames(
        BOSS_SPRITE,
        BOSS_SPRITESHEET_COLUMNS,
        BOSS_SPRITESHEET_ROWS,
        BOSS_BASE_FRAME_SIZE,
        BOSS_SPRITESHEET_FRAME_COUNT,
    )
    return [scale_surface(rotate_enemy_frame(frame), BOSS_SCALE) for frame in frames]


class Boss(pygame.sprite.Sprite):
    def __init__(self, frames: list[pygame.Surface]) -> None:
        super().__init__()
        self.frames = frames
        self.image = frames[0]
        self.rect = self.image.get_rect(
            center=(SCREEN_WIDTH // 2, -self.image.get_height() // 2)
        )
        self.position = pygame.Vector2(self.rect.center)
        self.hp = BOSS_HP
        self.max_hp = BOSS_HP
        self.state = BossAttackState.ENTERING
        self.age = 0.0
        self.state_timer = 0.0
        self.radial_timer = 0.0
        self.volley_timer = BOSS_INITIAL_VOLLEY_TIMER
        self.volley_index = 0
        self.sweep_direction = 1
        self.sweep_speed = BOSS_SWEEP_SPEED
        self.attack_flash_timer = 0.0
        self.pending_radial_burst = False
        self.velocity = pygame.Vector2(0, 0)

    @property
    def is_charging_radial(self) -> bool:
        return self.state is BossAttackState.CHARGING_RADIAL

    @property
    def can_take_damage(self) -> bool:
        return self.state not in {BossAttackState.ENTERING, BossAttackState.DEFEATED}

    def update(self, dt: float) -> None:
        self.age += dt
        self.state_timer += dt
        self.attack_flash_timer = max(0.0, self.attack_flash_timer - dt)
        self.velocity.update(0, 0)

        if self.state is BossAttackState.ENTERING:
            self._update_entering(dt)
        elif self.state is BossAttackState.SWEEPING:
            self._update_sweeping(dt)
        elif self.state is BossAttackState.MOVING_TO_CENTER:
            self._move_toward(
                dt,
                pygame.Vector2(SCREEN_WIDTH // 2, BOSS_CENTER_Y),
                BOSS_CENTER_MOVE_SPEED,
            )
            if (
                self.position.distance_to((SCREEN_WIDTH // 2, BOSS_CENTER_Y))
                <= BOSS_CENTER_REACHED_DISTANCE
            ):
                self._change_state(BossAttackState.CHARGING_RADIAL)
        elif self.state is BossAttackState.CHARGING_RADIAL:
            if self.state_timer >= BOSS_RADIAL_CHARGE_SECONDS:
                self._change_state(BossAttackState.RADIAL_BURST)
        elif self.state is BossAttackState.RADIAL_BURST:
            if not self.pending_radial_burst:
                self._change_state(BossAttackState.RETURNING_TO_SWEEP)
        elif self.state is BossAttackState.RETURNING_TO_SWEEP:
            self._move_toward(
                dt,
                pygame.Vector2(self.position.x, BOSS_SWEEP_Y),
                BOSS_RETURN_MOVE_SPEED,
            )
            if abs(self.position.y - BOSS_SWEEP_Y) <= BOSS_RETURN_REACHED_DISTANCE:
                self._change_state(BossAttackState.SWEEPING)

        self.rect.center = (round(self.position.x), round(self.position.y))
        self._update_visual_frame()

    def _update_entering(self, dt: float) -> None:
        self.velocity.y = BOSS_ENTER_SPEED
        self.position.y += self.velocity.y * dt
        if self.position.y >= BOSS_SWEEP_Y:
            self.position.y = BOSS_SWEEP_Y
            self._change_state(BossAttackState.SWEEPING)

    def _update_sweeping(self, dt: float) -> None:
        min_x = max(
            BOSS_SWEEP_SIDE_MARGIN,
            self.rect.width / 2 + BOSS_SWEEP_EDGE_PADDING,
        )
        max_x = min(
            SCREEN_WIDTH - BOSS_SWEEP_SIDE_MARGIN,
            SCREEN_WIDTH - self.rect.width / 2 - BOSS_SWEEP_EDGE_PADDING,
        )
        self.velocity.x = self.sweep_direction * self.sweep_speed
        self.position.x += self.velocity.x * dt
        self.position.y = (
            BOSS_SWEEP_Y
            + sin(self.age * BOSS_SWEEP_BOB_FREQUENCY) * BOSS_SWEEP_BOB_AMPLITUDE
        )

        if self.position.x >= max_x:
            self.position.x = max_x
            self.sweep_direction = -1
        elif self.position.x <= min_x:
            self.position.x = min_x
            self.sweep_direction = 1

        self.radial_timer += dt
        if self.radial_timer >= BOSS_RADIAL_INTERVAL_SECONDS:
            self._change_state(BossAttackState.MOVING_TO_CENTER)

    def _move_toward(self, dt: float, target: pygame.Vector2, speed: float) -> None:
        if dt <= 0:
            self.velocity.update(0, 0)
            return
        offset = target - self.position
        if offset.length_squared() <= BOSS_TARGET_EPSILON_DISTANCE:
            self.position.update(target)
            return
        direction = offset.normalize()
        movement = direction * speed * dt
        if movement.length_squared() >= offset.length_squared():
            self.position.update(target)
            self.velocity.update(offset)
        else:
            self.position += movement
            self.velocity.update(movement / dt)

    def _change_state(self, state: BossAttackState) -> None:
        self.state = state
        self.state_timer = 0.0
        if state is BossAttackState.SWEEPING:
            self.radial_timer = 0.0
            self.volley_timer = BOSS_SWEEP_RESUME_VOLLEY_TIMER
        elif state is BossAttackState.CHARGING_RADIAL:
            self.attack_flash_timer = BOSS_RADIAL_CHARGE_SECONDS
        elif state is BossAttackState.RADIAL_BURST:
            self.pending_radial_burst = True

    def _update_visual_frame(self) -> None:
        if self.state is BossAttackState.CHARGING_RADIAL:
            frame_index = BOSS_FRAME_CHARGE
        elif self.attack_flash_timer > 0:
            frame_index = BOSS_FRAME_ATTACK
        elif self.velocity.x < -BOSS_VISUAL_BANK_SPEED_THRESHOLD:
            frame_index = BOSS_FRAME_BANK_LEFT
        elif self.velocity.x > BOSS_VISUAL_BANK_SPEED_THRESHOLD:
            frame_index = BOSS_FRAME_BANK_RIGHT
        else:
            frame_index = BOSS_FRAME_IDLE
        center = self.rect.center
        self.image = self.frames[frame_index]
        self.rect = self.image.get_rect(center=center)

    def take_damage(self, amount: int) -> bool:
        if not self.can_take_damage:
            return False
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.state = BossAttackState.DEFEATED
            return True
        return False

    def try_shoot(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        active_boss_bullets: int = 0,
    ) -> list[Projectile]:
        if active_boss_bullets >= MAX_BOSS_BULLETS:
            return []
        if self.state is BossAttackState.SWEEPING:
            return self._try_sweeping_volley(dt, projectile_assets, active_boss_bullets)
        if self.state is BossAttackState.RADIAL_BURST and self.pending_radial_burst:
            self.pending_radial_burst = False
            return self._fire_radial_burst(projectile_assets, active_boss_bullets)
        return []

    def _try_sweeping_volley(
        self,
        dt: float,
        projectile_assets: ProjectileAssets,
        active_boss_bullets: int,
    ) -> list[Projectile]:
        self.volley_timer -= dt
        if self.volley_timer > 0:
            return []

        self.volley_timer = BOSS_SWEEP_VOLLEY_INTERVAL
        self.volley_index += 1
        self.attack_flash_timer = BOSS_SWEEP_ATTACK_FLASH_SECONDS
        config = BulletPatternConfig(
            bullet_count=BOSS_SWEEP_FAN_BULLET_COUNT,
            speed=BOSS_SWEEP_BULLET_SPEED,
            lifetime=BOSS_SWEEP_BULLET_LIFETIME,
            bullet_type=EnemyBulletType.BOSS_SMALL,
        )
        if self.volley_index % BOSS_LANE_PATTERN_INTERVAL == 0:
            spawns = lane_pattern_with_moving_gap(
                BOSS_SWEEP_LANES,
                self.rect.bottom - BOSS_PROJECTILE_Y_OFFSET,
                self.volley_index,
                config,
            )
        else:
            origin = pygame.Vector2(
                self.rect.centerx,
                self.rect.bottom - BOSS_PROJECTILE_Y_OFFSET,
            )
            spawns = sweeping_fan(
                origin,
                BOSS_SWEEP_FAN_ANGLE_START,
                BOSS_SWEEP_FAN_ANGLE_END,
                config,
            )
        return self._create_projectiles(spawns, projectile_assets, active_boss_bullets)

    def _fire_radial_burst(
        self,
        projectile_assets: ProjectileAssets,
        active_boss_bullets: int,
    ) -> list[Projectile]:
        self.attack_flash_timer = BOSS_RADIAL_ATTACK_FLASH_SECONDS
        config = BulletPatternConfig(
            bullet_count=BOSS_RADIAL_BULLET_COUNT,
            speed=BOSS_RADIAL_BULLET_SPEED,
            lifetime=BOSS_RADIAL_BULLET_LIFETIME,
            bullet_type=EnemyBulletType.BOSS_ORB,
        )
        spawns = radial_burst(self.rect.center, config)
        return self._create_projectiles(spawns, projectile_assets, active_boss_bullets)

    def _create_projectiles(
        self,
        spawns: list[BulletSpawn],
        projectile_assets: ProjectileAssets,
        active_boss_bullets: int,
    ) -> list[Projectile]:
        remaining = max(0, MAX_BOSS_BULLETS - active_boss_bullets)
        bullets: list[Projectile] = []
        for spawn in spawns[:remaining]:
            image = projectile_assets.enemy[spawn.bullet_type]
            bullets.append(
                Projectile(
                    image,
                    spawn.position.x,
                    spawn.position.y,
                    spawn.velocity.x,
                    spawn.velocity.y,
                    BOSS_PROJECTILE_DAMAGE,
                    lifetime=spawn.lifetime,
                )
            )
        return bullets
