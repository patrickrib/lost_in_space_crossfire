from __future__ import annotations

from enum import Enum, auto
from pathlib import Path


class GameState(Enum):
    MENU = auto()
    SCORES = auto()
    OPENING_STORY = auto()
    BOSS_TEST_MENU = auto()
    PLAYING = auto()
    VICTORY = auto()
    GAME_OVER = auto()


class EnemyType(Enum):
    SCOUT = auto()
    ZIGZAG = auto()
    HEAVY = auto()
    SHOOTER = auto()


class MovementPattern(Enum):
    STRAIGHT_DOWN = auto()
    ZIGZAG = auto()
    SLOW_DOWN = auto()


class PickupType(Enum):
    COIN = auto()
    WEAPON_UPGRADE = auto()
    BOMB = auto()
    SHIELD = auto()


class StageEventType(Enum):
    SPAWN_ENEMY = auto()
    SPAWN_PICKUP = auto()
    SPAWN_BOSS = auto()


class EnemyBulletType(Enum):
    BASIC = auto()
    HEAVY = auto()
    BOSS_SMALL = auto()
    BOSS_ORB = auto()


class BossAttackState(Enum):
    ENTERING = auto()
    SWEEPING = auto()
    MOVING_TO_CENTER = auto()
    CHARGING_RADIAL = auto()
    RADIAL_BURST = auto()
    RETURNING_TO_SWEEP = auto()
    DEFEATED = auto()


PLAYER_SPRITES = {
    1: Path("images/player/player_lv1_spritesheet.png"),
    2: Path("images/player/player_lv2_spritesheet.png"),
    3: Path("images/player/player_lv3_spritesheet.png"),
    4: Path("images/player/player_lv4_spritesheet.png"),
}

ENEMY_SPRITES = {
    EnemyType.SCOUT: Path("images/enemies/enemy_scout_spritesheet.png"),
    EnemyType.ZIGZAG: Path("images/enemies/enemy_interceptor_spritesheet.png"),
    EnemyType.HEAVY: Path("images/enemies/enemy_tank_spritesheet.png"),
    EnemyType.SHOOTER: Path("images/enemies/enemy_bomber_spritesheet.png"),
}

BOSS_SPRITE = Path("images/enemies/boss_01_spritesheet.png")
PROJECTILE_SPRITE = Path("images/projectiles/weapon_projectiles_spritesheet.png")
PICKUP_SPRITE = Path("images/items/pickups_spritesheet.png")
PLAYER_SHIELD_SPRITE = Path("images/player/player_shield.png")
ENEMY_EXPLOSION_SPRITE = Path("images/effects/enemy_explosion_spritesheet.png")
BOMB_EXPLOSION_SPRITE = Path("images/effects/bomb_explosion_spritesheet.png")
BACKGROUND_IMAGE = Path("images/backgrounds/background_stage_01.png")

SOUND_FILES = {
    "player_shoot": Path("sounds/player_shoot.wav"),
    "enemy_shoot": Path("sounds/enemy_shoot.wav"),
    "boss_shoot": Path("sounds/boss_shoot.wav"),
    "enemy_explosion": Path("sounds/enemy_explosion.wav"),
    "boss_explosion": Path("sounds/boss_explosion.wav"),
    "coin_pickup": Path("sounds/coin_pickup.wav"),
    "weapon_upgrade": Path("sounds/weapon_upgrade.wav"),
    "bomb_pickup": Path("sounds/bomb_pickup.wav"),
    "bomb_use": Path("sounds/bomb_use.wav"),
    "player_hit": Path("sounds/player_hit.wav"),
    "menu_select": Path("sounds/menu_select.wav"),
    "game_start": Path("sounds/game_start.wav"),
    "game_over": Path("sounds/game_over.wav"),
    "victory": Path("sounds/victory.wav"),
    "stage_theme": Path("sounds/stage_theme.wav"),
}
