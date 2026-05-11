from __future__ import annotations

from dataclasses import dataclass
import random

from .balance import (
    PANIC_BOMB_CHANCE,
    PANIC_BOMB_COOLDOWN_SECONDS,
    PANIC_BOMB_MIN_ENEMIES,
    PANIC_BOMB_MIN_ENEMY_BULLETS,
    PANIC_CHECK_INTERVAL_SECONDS,
    PANIC_ENABLED,
    PANIC_EXTRA_SHOT_CHANCE,
    PANIC_MIN_ENEMIES,
    PANIC_MIN_ENEMY_BULLETS,
    PANIC_SHOT_COOLDOWN_SECONDS,
    PANIC_SHOT_COOLDOWN_VARIANCE_SECONDS,
)


@dataclass(frozen=True)
class PanicContext:
    enemy_count: int
    enemy_bullet_count: int
    boss_active: bool
    boss_hp: int
    bomb_ready: bool


@dataclass(frozen=True)
class PanicAction:
    shot_velocities: tuple[tuple[float, float], ...] = ()
    trigger_bomb: bool = False
    message_index: int = 0


class PicardoPanicSystem:
    def __init__(self) -> None:
        self.check_timer = 0.0
        self.shot_cooldown = 0.0
        self.bomb_cooldown = 0.0
        self.previous_pattern_index = -1
        self.message_index = 0
        self.bomb_message_index = 0

    def update(self, dt: float, game_context: PanicContext) -> list[PanicAction]:
        self.check_timer = max(0.0, self.check_timer - dt)
        self.shot_cooldown = max(0.0, self.shot_cooldown - dt)
        self.bomb_cooldown = max(0.0, self.bomb_cooldown - dt)
        if not PANIC_ENABLED or self.check_timer > 0:
            return []

        self.check_timer = PANIC_CHECK_INTERVAL_SECONDS
        if not self._is_under_pressure(game_context):
            return []

        actions: list[PanicAction] = []
        if self.shot_cooldown <= 0:
            actions.append(self._next_shot_action())
            if random.random() < PANIC_EXTRA_SHOT_CHANCE:
                actions.append(self._next_shot_action())
            self.shot_cooldown = self._next_shot_cooldown()

        if self._should_trigger_bomb(game_context):
            actions.append(self._next_bomb_action())
            self.bomb_cooldown = PANIC_BOMB_COOLDOWN_SECONDS

        return actions

    def reset(self) -> None:
        self.check_timer = 0.0
        self.shot_cooldown = 0.0
        self.bomb_cooldown = 0.0
        self.previous_pattern_index = -1
        self.message_index = 0
        self.bomb_message_index = 0

    def _is_under_pressure(self, context: PanicContext) -> bool:
        return (
            context.enemy_count >= PANIC_MIN_ENEMIES
            or context.enemy_bullet_count >= PANIC_MIN_ENEMY_BULLETS
            or (context.boss_active and context.boss_hp > 0)
        )

    def _is_high_pressure(self, context: PanicContext) -> bool:
        return (
            context.enemy_count >= PANIC_BOMB_MIN_ENEMIES
            or context.enemy_bullet_count >= PANIC_BOMB_MIN_ENEMY_BULLETS
            or (context.boss_active and context.enemy_bullet_count >= 30)
        )

    def _should_trigger_bomb(self, context: PanicContext) -> bool:
        return (
            self.bomb_cooldown <= 0
            and context.bomb_ready
            and self._is_high_pressure(context)
            and random.random() < PANIC_BOMB_CHANCE
        )

    def _next_shot_action(self) -> PanicAction:
        patterns = (
            ((-260.0, -460.0), (260.0, -460.0)),
            ((-470.0, 0.0), (470.0, 0.0)),
            ((0.0, 430.0), (-90.0, 410.0), (90.0, 410.0)),
            (
                (0.0, -470.0),
                (330.0, -330.0),
                (470.0, 0.0),
                (330.0, 330.0),
                (0.0, 470.0),
                (-330.0, 330.0),
                (-470.0, 0.0),
                (-330.0, -330.0),
            ),
            ((0.0, -500.0), (430.0, 0.0), (0.0, 430.0), (-250.0, -350.0)),
        )
        pattern_index = self._random_pattern_index(len(patterns))
        velocities = patterns[pattern_index]
        action = PanicAction(
            shot_velocities=velocities,
            message_index=self.message_index,
        )
        self.message_index += random.randint(1, 3)
        return action

    def _random_pattern_index(self, pattern_count: int) -> int:
        pattern_index = random.randrange(pattern_count)
        if pattern_count > 1 and pattern_index == self.previous_pattern_index:
            pattern_index = (pattern_index + random.randrange(1, pattern_count)) % pattern_count
        self.previous_pattern_index = pattern_index
        return pattern_index

    def _next_shot_cooldown(self) -> float:
        cooldown = PANIC_SHOT_COOLDOWN_SECONDS + random.uniform(
            -PANIC_SHOT_COOLDOWN_VARIANCE_SECONDS,
            PANIC_SHOT_COOLDOWN_VARIANCE_SECONDS,
        )
        return max(0.75, cooldown)

    def _next_bomb_action(self) -> PanicAction:
        action = PanicAction(
            trigger_bomb=True,
            message_index=self.bomb_message_index,
        )
        self.bomb_message_index += 1
        return action
