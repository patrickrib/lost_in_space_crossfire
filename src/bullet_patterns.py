from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import pygame

from .constants import EnemyBulletType


@dataclass(frozen=True)
class BulletPatternConfig:
    bullet_count: int
    speed: float
    lifetime: float
    bullet_type: EnemyBulletType
    angle_offset_degrees: float = 0.0
    spread_degrees: float = 90.0


@dataclass(frozen=True)
class BulletSpawn:
    position: pygame.Vector2
    velocity: pygame.Vector2
    bullet_type: EnemyBulletType
    lifetime: float


def vector_from_degrees(angle_degrees: float) -> pygame.Vector2:
    radians = math.radians(angle_degrees)
    return pygame.Vector2(math.cos(radians), math.sin(radians))


def radial_burst(
    center_position: pygame.Vector2 | tuple[float, float],
    config: BulletPatternConfig,
) -> list[BulletSpawn]:
    if config.bullet_count <= 0:
        return []
    center = pygame.Vector2(center_position)
    angle_offset = math.radians(config.angle_offset_degrees)
    spawns: list[BulletSpawn] = []
    for index in range(config.bullet_count):
        angle = 2 * math.pi * index / config.bullet_count + angle_offset
        velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * config.speed
        spawns.append(BulletSpawn(center, velocity, config.bullet_type, config.lifetime))
    return spawns


def rotating_spiral(
    center_position: pygame.Vector2 | tuple[float, float],
    arms: int,
    base_angle_degrees: float,
    angle_step_degrees: float,
    speed: float,
    lifetime: float,
    bullet_type: EnemyBulletType,
) -> tuple[list[BulletSpawn], float]:
    if arms <= 0:
        return [], base_angle_degrees + angle_step_degrees
    center = pygame.Vector2(center_position)
    spawns = []
    for arm in range(arms):
        angle = base_angle_degrees + arm * (360 / arms)
        spawns.append(
            BulletSpawn(
                center,
                vector_from_degrees(angle) * speed,
                bullet_type,
                lifetime,
            )
        )
    return spawns, base_angle_degrees + angle_step_degrees


def sweeping_fan(
    origin: pygame.Vector2 | tuple[float, float],
    angle_start_degrees: float,
    angle_end_degrees: float,
    config: BulletPatternConfig,
) -> list[BulletSpawn]:
    if config.bullet_count <= 0:
        return []
    center = pygame.Vector2(origin)
    if config.bullet_count <= 1:
        angles = [angle_start_degrees]
    else:
        step = (angle_end_degrees - angle_start_degrees) / (config.bullet_count - 1)
        angles = [angle_start_degrees + step * index for index in range(config.bullet_count)]
    return [
        BulletSpawn(
            center,
            vector_from_degrees(angle + config.angle_offset_degrees) * config.speed,
            config.bullet_type,
            config.lifetime,
        )
        for angle in angles
    ]


def lane_pattern_with_moving_gap(
    lanes: Iterable[float],
    y: float,
    volley_index: int,
    config: BulletPatternConfig,
) -> list[BulletSpawn]:
    lane_positions = list(lanes)
    if not lane_positions:
        return []
    gap_index = volley_index % len(lane_positions)
    velocity = vector_from_degrees(90 + config.angle_offset_degrees) * config.speed
    return [
        BulletSpawn(pygame.Vector2(x, y), velocity, config.bullet_type, config.lifetime)
        for index, x in enumerate(lane_positions)
        if index != gap_index
    ]


def alternating_ring(
    center_position: pygame.Vector2 | tuple[float, float],
    ring_index: int,
    angle_step_degrees: float,
    config: BulletPatternConfig,
) -> list[BulletSpawn]:
    ring_config = BulletPatternConfig(
        bullet_count=config.bullet_count,
        speed=config.speed,
        lifetime=config.lifetime,
        bullet_type=config.bullet_type,
        angle_offset_degrees=config.angle_offset_degrees + ring_index * angle_step_degrees,
        spread_degrees=config.spread_degrees,
    )
    return radial_burst(center_position, ring_config)


def mixed_projectile_pattern(
    fan_origin: pygame.Vector2 | tuple[float, float],
    radial_origin: pygame.Vector2 | tuple[float, float],
    fan_config: BulletPatternConfig,
    radial_config: BulletPatternConfig,
    fan_angle_start_degrees: float,
    fan_angle_end_degrees: float,
) -> list[BulletSpawn]:
    return [
        *sweeping_fan(fan_origin, fan_angle_start_degrees, fan_angle_end_degrees, fan_config),
        *radial_burst(radial_origin, radial_config),
    ]
