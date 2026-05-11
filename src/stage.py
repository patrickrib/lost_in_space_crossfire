from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import EnemyType, PickupType, StageEventType
from .settings import BOSS_SPAWN_TIME_SECONDS, STAGE_DURATION_SECONDS


@dataclass(frozen=True)
class StageEvent:
    time_seconds: float
    event_type: StageEventType
    x: int
    y: int
    payload: dict[str, Any] = field(default_factory=dict)


class Stage:
    def __init__(self) -> None:
        self.events = self._create_events()
        self.elapsed = 0.0
        self.next_event_index = 0

    def reset(self) -> None:
        self.elapsed = 0.0
        self.next_event_index = 0

    def seek(self, time_seconds: float) -> None:
        self.elapsed = max(0.0, time_seconds)
        self.next_event_index = 0
        while self.next_event_index < len(self.events):
            if self.events[self.next_event_index].time_seconds > self.elapsed:
                break
            self.next_event_index += 1

    @property
    def boss_spawn_time(self) -> float:
        for event in self.events:
            if event.event_type is StageEventType.SPAWN_BOSS:
                return event.time_seconds
        return STAGE_DURATION_SECONDS

    def update(self, dt: float) -> list[StageEvent]:
        self.elapsed += dt
        ready: list[StageEvent] = []
        while self.next_event_index < len(self.events):
            event = self.events[self.next_event_index]
            if event.time_seconds > self.elapsed:
                break
            ready.append(event)
            self.next_event_index += 1
        return ready

    def _create_events(self) -> list[StageEvent]:
        events: list[StageEvent] = []

        def enemy(time: float, enemy_type: EnemyType, x: int, y: int = -50) -> None:
            events.append(
                StageEvent(time, StageEventType.SPAWN_ENEMY, x, y, {"enemy_type": enemy_type})
            )

        def pickup(time: float, pickup_type: PickupType, x: int, y: int = -40) -> None:
            events.append(
                StageEvent(time, StageEventType.SPAWN_PICKUP, x, y, {"pickup_type": pickup_type})
            )

        def wave(
            start_time: float,
            enemy_type: EnemyType,
            lanes: tuple[int, ...],
            spacing: float = 0.3,
        ) -> None:
            for index, x in enumerate(lanes):
                enemy(start_time + index * spacing, enemy_type, x)

        def coin_path(start_time: float, lanes: tuple[int, ...]) -> None:
            for index, x in enumerate(lanes):
                pickup(start_time + index * 0.22, PickupType.COIN, x)

        wave(4.0, EnemyType.SCOUT, (120, 240, 360), 0.35)
        enemy(6.2, EnemyType.ZIGZAG, 240)
        wave(8.0, EnemyType.SCOUT, (90, 190, 290), 0.30)
        wave(12.0, EnemyType.SCOUT, (80, 180, 300, 400), 0.25)
        coin_path(13.0, (110, 170, 230, 290, 350))
        wave(15.5, EnemyType.SCOUT, (145, 240, 335), 0.28)

        wave(18.0, EnemyType.ZIGZAG, (145, 335), 0.45)
        pickup(22.0, PickupType.WEAPON_UPGRADE, 240)
        wave(26.0, EnemyType.SCOUT, (75, 165, 315, 405), 0.25)
        enemy(27.2, EnemyType.ZIGZAG, 240)
        wave(30.0, EnemyType.SCOUT, (100, 190, 290, 380), 0.24)
        wave(32.0, EnemyType.SHOOTER, (150, 330), 0.60)
        wave(36.0, EnemyType.SCOUT, (85, 180, 300, 395), 0.26)
        enemy(37.3, EnemyType.ZIGZAG, 240)
        pickup(38.0, PickupType.BOMB, 150)

        wave(42.0, EnemyType.SCOUT, (70, 150, 240, 330, 410), 0.22)
        wave(48.0, EnemyType.ZIGZAG, (130, 350), 0.45)
        enemy(49.0, EnemyType.SHOOTER, 240)
        wave(51.5, EnemyType.SCOUT, (95, 185, 295, 385), 0.25)
        enemy(55.0, EnemyType.HEAVY, 240)
        wave(55.4, EnemyType.SCOUT, (115, 365), 0.35)
        wave(60.5, EnemyType.ZIGZAG, (130, 350), 0.42)
        pickup(62.0, PickupType.WEAPON_UPGRADE, 290)

        wave(68.0, EnemyType.SHOOTER, (135, 345), 0.55)
        wave(68.4, EnemyType.SCOUT, (80, 240, 400), 0.32)
        wave(72.0, EnemyType.SCOUT, (70, 155, 240, 325, 410), 0.22)
        pickup(75.0, PickupType.BOMB, 340)
        wave(78.0, EnemyType.ZIGZAG, (115, 240, 365), 0.32)
        enemy(79.2, EnemyType.SHOOTER, 310)
        enemy(82.0, EnemyType.HEAVY, 150)
        enemy(83.2, EnemyType.HEAVY, 330)
        wave(88.0, EnemyType.ZIGZAG, (105, 240, 375), 0.32)
        wave(88.6, EnemyType.SCOUT, (170, 310), 0.40)

        wave(92.0, EnemyType.SCOUT, (80, 160, 240, 320, 400), 0.22)
        pickup(95.0, PickupType.SHIELD, 240)
        wave(98.0, EnemyType.ZIGZAG, (125, 355), 0.35)
        enemy(99.0, EnemyType.SHOOTER, 240)
        pickup(102.0, PickupType.WEAPON_UPGRADE, 240)
        wave(104.0, EnemyType.SCOUT, (95, 185, 295, 385), 0.25)
        wave(108.0, EnemyType.SHOOTER, (135, 345), 0.55)
        wave(108.4, EnemyType.ZIGZAG, (210, 285), 0.45)
        coin_path(109.2, (90, 150, 210, 270, 330, 390))
        wave(112.0, EnemyType.ZIGZAG, (105, 240, 375), 0.32)
        enemy(116.0, EnemyType.HEAVY, 240)
        wave(116.4, EnemyType.SCOUT, (80, 160, 320, 400), 0.25)
        wave(120.0, EnemyType.SCOUT, (100, 190, 290, 380), 0.24)

        events.append(StageEvent(BOSS_SPAWN_TIME_SECONDS, StageEventType.SPAWN_BOSS, 240, -100))

        return sorted(events, key=lambda event: event.time_seconds)
