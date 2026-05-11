from __future__ import annotations

from dataclasses import dataclass
import random

import pygame

from .assets import load_background
from .boss import Boss, load_boss_frames
from .constants import BACKGROUND_IMAGE, GameState, PickupType, StageEventType
from .database import get_top_scores, initialize_database, save_score
from .effects import AnimatedEffect, load_bomb_explosion_frames, load_enemy_explosion_frames
from .enemy import Enemy, create_enemy, load_enemy_assets
from .localization import (
    CHECKPOINT_BOSS_LABEL,
    CHECKPOINT_START_LABEL,
    DEFAULT_PLAYER_NAME,
    GAME_TITLE,
    OPENING_STORY,
    PANIC_BOMB_MESSAGES,
    PANIC_MESSAGES,
    SHIELD_HIT_MESSAGE,
)
from .panic import PanicContext, PicardoPanicSystem
from .pickup import Pickup, load_pickup_assets
from .player import Player, load_player_assets
from .projectile import Projectile, load_projectile_assets
from .shield import ShieldVisual, load_shield_frames
from .settings import (
    BOMB_DAMAGE,
    BACKGROUND_SCROLL_SPEED,
    BOSS_CHARGE_GLOW_CENTER,
    BOSS_CHARGE_GLOW_SIZE,
    BOSS_CHARGE_INNER_GLOW_COLOR,
    BOSS_CHARGE_INNER_GLOW_RADIUS,
    BOSS_CHARGE_INNER_GLOW_WIDTH,
    BOSS_CHARGE_OUTER_GLOW_COLOR,
    BOSS_CHARGE_OUTER_GLOW_RADIUS,
    BOSS_CHARGE_OUTER_GLOW_WIDTH,
    BOSS_DEFEAT_EFFECT_FRAME_TIME,
    BOSS_SCORE,
    BOSS_TEST_SECRET_SEQUENCE,
    CHECKPOINT_RECOVERY_MINIMUMS,
    CHECKPOINT_TIMES_SECONDS,
    COIN_SCORE,
    COIN_DROP_CHANCE,
    FPS,
    MAXED_PICKUP_SCORE,
    MAX_BOMBS,
    MAX_WEAPON_LEVEL,
    OPENING_STORY_AUTO_START_Y,
    OPENING_STORY_LINE_HEIGHT,
    OPENING_STORY_SCROLL_SPEED,
    OPENING_STORY_SCROLL_START_Y,
    PLAYER_BOMB_EFFECT_FRAME_TIME,
    PLAYER_CONTINUES,
    PLAYER_MAX_SHIELD,
    PLAYER_SHIELD_HEIGHT_SCALE,
    PLAYER_SHIELD_WIDTH_SCALE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_HIT_MESSAGE_DURATION_SECONDS,
    SHIELD_PICKUP_BONUS_SCORE,
    SHIELD_PICKUP_VALUE,
    VICTORY_CONGRATULATIONS_SECONDS,
)
from .balance import (
    PANIC_BOMB_CONSUMES_PLAYER_BOMB,
    PANIC_MESSAGE_DURATION_SECONDS,
    PANIC_SHOT_DAMAGE,
)
from .sound import SoundManager
from .stage import Stage, StageEvent
from .ui import UI


@dataclass(frozen=True)
class CheckpointSnapshot:
    time_seconds: float
    score: int
    weapon_level: int
    bomb_count: int


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.sound = SoundManager()
        self.running = True
        self.state = GameState.MENU
        self.opening_story_elapsed = 0.0
        self.victory_elapsed = 0.0
        self.boss_test_mode = False
        self.reached_boss = False
        self.defeated_boss = False
        self.game_over_score_saved = False
        self.victory_score_saved = False
        self.secret_sequence_progress = 0
        self.continues_remaining = PLAYER_CONTINUES
        self.next_checkpoint_index = 1
        self.top_scores = []
        self.status_message = ""
        self.status_message_timer = 0.0

        self.background = load_background(BACKGROUND_IMAGE)
        self.background_scroll = 0.0

        self.player_assets = load_player_assets()
        self.enemy_assets = load_enemy_assets()
        self.boss_frames = load_boss_frames()
        self.projectile_assets = load_projectile_assets()
        self.panic_projectile_image = self._create_panic_projectile_image()
        self.pickup_assets = load_pickup_assets()
        self.enemy_explosion_frames = load_enemy_explosion_frames()
        self.bomb_explosion_frames = load_bomb_explosion_frames()

        self.player = Player(self.player_assets)
        self.stage = Stage()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.shield_visual = ShieldVisual(load_shield_frames(self._shield_visual_size()))
        self.panic_system = PicardoPanicSystem()
        self.checkpoint_snapshot = self._create_checkpoint_snapshot(CHECKPOINT_TIMES_SECONDS[0])
        initialize_database()
        self.top_scores = get_top_scores()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state is GameState.MENU:
                        self.running = False
                    else:
                        self._return_to_menu()
                elif event.key == pygame.K_RETURN:
                    if self.state is GameState.MENU:
                        self.state = GameState.OPENING_STORY
                        self.opening_story_elapsed = 0.0
                        self.sound.play("menu_select")
                    elif self.state is GameState.OPENING_STORY:
                        self._start_game()
                    elif self.state is GameState.VICTORY:
                        self._start_game()
                    elif self.state is GameState.GAME_OVER:
                        self._handle_game_over_enter()
                    elif self.state is GameState.BOSS_TEST_MENU:
                        self._start_boss_test()
                elif self.state is GameState.MENU:
                    self._handle_menu_input(event.key)
                elif event.key == pygame.K_b and self.state is GameState.PLAYING:
                    self._use_bomb()

    def _handle_menu_input(self, key: int) -> None:
        if key == pygame.K_r:
            self.top_scores = get_top_scores()
            self.state = GameState.SCORES
            self.sound.play("menu_select")
            return
        self._handle_secret_menu_input(key)

    def _return_to_menu(self) -> None:
        self.state = GameState.MENU
        self.opening_story_elapsed = 0.0
        self.victory_elapsed = 0.0
        self.sound.stop_music()
        self._clear_playfield()
        self.panic_system.reset()
        self.status_message = ""
        self.status_message_timer = 0.0

    def _handle_secret_menu_input(self, key: int) -> None:
        input_name = self._secret_input_name(key)
        if input_name is None:
            return

        expected = BOSS_TEST_SECRET_SEQUENCE[self.secret_sequence_progress]
        if input_name == expected:
            self.secret_sequence_progress += 1
            if self.secret_sequence_progress >= len(BOSS_TEST_SECRET_SEQUENCE):
                self.secret_sequence_progress = 0
                self.state = GameState.BOSS_TEST_MENU
                self.sound.play("menu_select")
            return

        self.secret_sequence_progress = 1 if input_name == BOSS_TEST_SECRET_SEQUENCE[0] else 0

    def _secret_input_name(self, key: int) -> str | None:
        if key in {pygame.K_UP, pygame.K_w}:
            return "UP"
        if key in {pygame.K_DOWN, pygame.K_s}:
            return "DOWN"
        return None

    def _start_game(self, boss_test_mode: bool = False) -> None:
        self.state = GameState.PLAYING
        self.boss_test_mode = boss_test_mode
        self.opening_story_elapsed = 0.0
        self.victory_elapsed = 0.0
        self.reached_boss = boss_test_mode
        self.defeated_boss = False
        self.game_over_score_saved = False
        self.victory_score_saved = False
        self.panic_system.reset()
        self.status_message = ""
        self.status_message_timer = 0.0
        self.player.reset_for_new_game()
        self.stage.reset()
        self._reset_checkpoint_progress()
        self._clear_playfield()
        self.sound.play("game_start")
        self.sound.play_music()
        if boss_test_mode:
            self.player.set_weapon_level(MAX_WEAPON_LEVEL)
            self.player.bomb_count = MAX_BOMBS
            self.stage.seek(self.stage.boss_spawn_time)
            self.checkpoint_snapshot = self._create_checkpoint_snapshot(self.stage.boss_spawn_time)
            self.next_checkpoint_index = len(CHECKPOINT_TIMES_SECONDS)
            self.boss_group.add(Boss(self.boss_frames))

    def _clear_playfield(self) -> None:
        self.enemies.empty()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.pickups.empty()
        self.effects.empty()
        self.boss_group.empty()

    def _reset_checkpoint_progress(self) -> None:
        self.continues_remaining = PLAYER_CONTINUES
        self.checkpoint_snapshot = self._create_checkpoint_snapshot(CHECKPOINT_TIMES_SECONDS[0])
        self.next_checkpoint_index = self._next_checkpoint_index_after(CHECKPOINT_TIMES_SECONDS[0])

    def _create_checkpoint_snapshot(self, time_seconds: float) -> CheckpointSnapshot:
        return CheckpointSnapshot(
            time_seconds=time_seconds,
            score=self.player.score,
            weapon_level=self.player.weapon_level,
            bomb_count=self.player.bomb_count,
        )

    def _next_checkpoint_index_after(self, time_seconds: float) -> int:
        for index, checkpoint_time in enumerate(CHECKPOINT_TIMES_SECONDS):
            if checkpoint_time > time_seconds:
                return index
        return len(CHECKPOINT_TIMES_SECONDS)

    def _update_checkpoint_progress(self) -> None:
        if self.boss_test_mode:
            return
        while self.next_checkpoint_index < len(CHECKPOINT_TIMES_SECONDS):
            checkpoint_time = CHECKPOINT_TIMES_SECONDS[self.next_checkpoint_index]
            if self.stage.elapsed < checkpoint_time:
                break
            self.checkpoint_snapshot = self._create_checkpoint_snapshot(checkpoint_time)
            self.next_checkpoint_index += 1

    def _handle_game_over_enter(self) -> None:
        if self.continues_remaining > 0:
            self._continue_from_checkpoint()
            return
        self._start_game(self.boss_test_mode)

    def _continue_from_checkpoint(self) -> None:
        self.continues_remaining -= 1
        self.state = GameState.PLAYING
        self.victory_elapsed = 0.0
        self.game_over_score_saved = False
        self.panic_system.reset()
        self.status_message = ""
        self.status_message_timer = 0.0
        snapshot = self.checkpoint_snapshot

        weapon_level, bomb_count = self._checkpoint_recovery_values(snapshot)
        self.player.reset_for_checkpoint(snapshot.score, weapon_level, bomb_count)
        self.stage.reset()
        self._clear_playfield()

        checkpoint_time = (
            self.stage.boss_spawn_time
            if self.boss_test_mode
            else snapshot.time_seconds
        )
        self.stage.seek(checkpoint_time)
        self.next_checkpoint_index = self._next_checkpoint_index_after(checkpoint_time)
        if checkpoint_time >= self.stage.boss_spawn_time:
            self.reached_boss = True
            self.boss_group.add(Boss(self.boss_frames))

        self.sound.play("game_start")
        self.sound.play_music()

    def _checkpoint_recovery_values(self, snapshot: CheckpointSnapshot) -> tuple[int, int]:
        recovery = CHECKPOINT_RECOVERY_MINIMUMS.get(snapshot.time_seconds, {})
        weapon_level = max(
            snapshot.weapon_level,
            recovery.get("weapon_level", snapshot.weapon_level),
        )
        bomb_count = max(snapshot.bomb_count, recovery.get("bomb_count", snapshot.bomb_count))
        return weapon_level, bomb_count

    def _start_boss_test(self) -> None:
        self._start_game(boss_test_mode=True)

    def _opening_story_reached_start_point(self) -> bool:
        last_line_index = self._last_visible_opening_story_index()
        if last_line_index is None:
            return False

        last_line_y = (
            OPENING_STORY_SCROLL_START_Y
            - self.opening_story_elapsed * OPENING_STORY_SCROLL_SPEED
            + last_line_index * OPENING_STORY_LINE_HEIGHT
        )
        return last_line_y < OPENING_STORY_AUTO_START_Y

    def _last_visible_opening_story_index(self) -> int | None:
        for index in range(len(OPENING_STORY) - 1, -1, -1):
            if OPENING_STORY[index]:
                return index
        return None

    def _update(self, dt: float) -> None:
        self._update_background(dt)
        self._update_status_message(dt)
        if self.state is not GameState.PLAYING:
            if self.state is GameState.OPENING_STORY:
                self.opening_story_elapsed += dt
                if self._opening_story_reached_start_point():
                    self._start_game()
                    return
            if self.state is GameState.VICTORY:
                self.victory_elapsed += dt
            self.effects.update(dt)
            return

        self.player.update(dt)
        self.shield_visual.update(dt)
        self._handle_continuous_shooting()
        if not self.boss_test_mode:
            self._handle_stage_events(dt)
        self._handle_panic_actions(dt)

        self.enemies.update(dt, self.player.rect.center)
        self.player_bullets.update(dt)
        self.enemy_bullets.update(dt)
        self.pickups.update(dt)
        self.effects.update(dt)
        self.boss_group.update(dt)

        self._handle_enemy_shooting(dt)
        self._handle_boss_shooting(dt)
        self._handle_collisions()

    def _update_background(self, dt: float) -> None:
        self.background_scroll += BACKGROUND_SCROLL_SPEED * dt
        if self.background_scroll >= self.background.get_height():
            self.background_scroll = 0.0

    def _handle_continuous_shooting(self) -> None:
        keys = pygame.key.get_pressed()
        if not keys[pygame.K_SPACE]:
            return
        now = pygame.time.get_ticks() / 1000.0
        bullets = self.player.shoot(now, self.projectile_assets)
        if bullets:
            self.player_bullets.add(bullets)
            self.sound.play("player_shoot")

    def _handle_panic_actions(self, dt: float) -> None:
        boss = self.boss_group.sprite
        now = pygame.time.get_ticks() / 1000.0
        context = PanicContext(
            enemy_count=len(self.enemies),
            enemy_bullet_count=len(self.enemy_bullets),
            boss_active=bool(boss),
            boss_hp=boss.hp if boss else 0,
            bomb_ready=self.player.bomb_cooldown_remaining(now) <= 0,
        )
        for action in self.panic_system.update(dt, context):
            if action.shot_velocities:
                self._spawn_panic_shots(action.shot_velocities)
                self._show_panic_message(action.message_index)
                self.sound.play("menu_select")
            if action.trigger_bomb:
                if self._use_bomb(is_panic_bomb=True):
                    self._show_panic_bomb_message(action.message_index)

    def _spawn_panic_shots(self, velocities: tuple[tuple[float, float], ...]) -> None:
        x, y = self.player.rect.center
        bullets = [
            Projectile(
                self.panic_projectile_image,
                x,
                y,
                vx,
                vy,
                PANIC_SHOT_DAMAGE,
            )
            for vx, vy in velocities
        ]
        self.player_bullets.add(bullets)

    def _show_panic_message(self, message_index: int) -> None:
        self.status_message = PANIC_MESSAGES[message_index % len(PANIC_MESSAGES)]
        self.status_message_timer = PANIC_MESSAGE_DURATION_SECONDS

    def _show_panic_bomb_message(self, message_index: int) -> None:
        self.status_message = PANIC_BOMB_MESSAGES[message_index % len(PANIC_BOMB_MESSAGES)]
        self.status_message_timer = PANIC_MESSAGE_DURATION_SECONDS

    def _update_status_message(self, dt: float) -> None:
        if self.status_message_timer <= 0:
            return
        self.status_message_timer = max(0.0, self.status_message_timer - dt)
        if self.status_message_timer <= 0:
            self.status_message = ""

    def _handle_stage_events(self, dt: float) -> None:
        for event in self.stage.update(dt):
            self._execute_stage_event(event)
        self._update_checkpoint_progress()

    def _execute_stage_event(self, event: StageEvent) -> None:
        if event.event_type is StageEventType.SPAWN_ENEMY:
            enemy_type = event.payload["enemy_type"]
            enemy = create_enemy(enemy_type, self.enemy_assets, event.x, event.y)
            self.enemies.add(enemy)
        elif event.event_type is StageEventType.SPAWN_PICKUP:
            pickup_type = event.payload["pickup_type"]
            self._spawn_pickup(pickup_type, event.x, event.y)
        elif event.event_type is StageEventType.SPAWN_BOSS:
            boss = Boss(self.boss_frames)
            self.boss_group.add(boss)
            self.reached_boss = True

    def _handle_enemy_shooting(self, dt: float) -> None:
        for enemy in list(self.enemies):
            bullets = enemy.try_shoot(dt, self.projectile_assets, self.player.rect.center)
            if bullets:
                self.enemy_bullets.add(bullets)
                self.sound.play("enemy_shoot")

    def _handle_boss_shooting(self, dt: float) -> None:
        boss = self.boss_group.sprite
        if not boss:
            return
        bullets = boss.try_shoot(dt, self.projectile_assets, len(self.enemy_bullets))
        if bullets:
            self.enemy_bullets.add(bullets)
            self.sound.play("boss_shoot")

    def _handle_collisions(self) -> None:
        self._handle_player_bullets_vs_enemies()
        if self.state is not GameState.PLAYING:
            return
        self._handle_player_bullets_vs_boss()
        if self.state is not GameState.PLAYING:
            return
        self._handle_pickups()
        if self.state is not GameState.PLAYING:
            return
        self._handle_player_damage()

    def _handle_player_bullets_vs_enemies(self) -> None:
        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True)
        for enemy, bullets in hits.items():
            for bullet in bullets:
                if enemy.take_damage(bullet.damage):
                    self._destroy_enemy(enemy)
                    break

    def _handle_player_bullets_vs_boss(self) -> None:
        boss = self.boss_group.sprite
        if not boss:
            return
        hits = pygame.sprite.spritecollide(boss, self.player_bullets, True)
        for bullet in hits:
            if boss.take_damage(bullet.damage):
                self._destroy_boss(boss)
                return

    def _handle_pickups(self) -> None:
        pickups = pygame.sprite.spritecollide(self.player, self.pickups, True)
        for pickup in pickups:
            if pickup.pickup_type is PickupType.COIN:
                self.player.score += COIN_SCORE
                self.sound.play("coin_pickup")
            elif pickup.pickup_type is PickupType.WEAPON_UPGRADE:
                if self.player.add_weapon_upgrade():
                    self.sound.play("weapon_upgrade")
                else:
                    self.player.score += MAXED_PICKUP_SCORE
                    self.sound.play("coin_pickup")
            elif pickup.pickup_type is PickupType.BOMB:
                if self.player.add_bomb():
                    self.sound.play("bomb_pickup")
                else:
                    self.player.score += MAXED_PICKUP_SCORE
                    self.sound.play("coin_pickup")
            elif pickup.pickup_type is PickupType.SHIELD:
                if self.player.add_shield(SHIELD_PICKUP_VALUE):
                    self.sound.play("weapon_upgrade")
                else:
                    self.player.score += SHIELD_PICKUP_BONUS_SCORE
                    self.sound.play("coin_pickup")

    def _handle_player_damage(self) -> None:
        enemy_hits = pygame.sprite.spritecollide(
            self.player,
            self.enemy_bullets,
            True,
            collided=self._collides_with_player_hitbox,
        )
        body_hits = pygame.sprite.spritecollide(
            self.player,
            self.enemies,
            False,
            collided=self._collides_with_player_hitbox,
        )
        boss = self.boss_group.sprite
        boss_hit = bool(boss and self.player.hitbox.colliderect(boss.rect))
        if not enemy_hits and not body_hits and not boss_hit:
            return

        shield_before = self.player.shield
        lives_before = self.player.lives
        if self.player.take_hit():
            self.sound.play("player_hit")
            self.effects.add(AnimatedEffect(self.enemy_explosion_frames, self.player.rect.center))
            if self.player.lives <= 0:
                self._save_game_over_score()
                self.state = GameState.GAME_OVER
                self.sound.stop_music()
                self.sound.play("game_over")
        elif self.player.lives == lives_before and self.player.shield < shield_before:
            self.sound.play("player_hit")
            self._show_shield_hit_message()

    def _collides_with_player_hitbox(self, player: Player, sprite: pygame.sprite.Sprite) -> bool:
        return player.hitbox.colliderect(sprite.rect)

    def _destroy_enemy(self, enemy: Enemy) -> None:
        self.player.score += enemy.config.score
        center = enemy.rect.center
        enemy.kill()
        self.effects.add(AnimatedEffect(self.enemy_explosion_frames, center))
        self.sound.play("enemy_explosion")
        if random.random() < COIN_DROP_CHANCE:
            self._spawn_pickup(PickupType.COIN, center[0], center[1])

    def _destroy_boss(self, boss: Boss) -> None:
        center = boss.rect.center
        boss.kill()
        self.player.score += BOSS_SCORE
        self.reached_boss = True
        self.defeated_boss = True
        self._save_victory_score()
        self.effects.add(
            AnimatedEffect(
                self.bomb_explosion_frames,
                center,
                BOSS_DEFEAT_EFFECT_FRAME_TIME,
            )
        )
        self.sound.stop_music()
        self.sound.play("boss_explosion")
        self.sound.play("victory")
        self.victory_elapsed = 0.0
        self.state = GameState.VICTORY

    def _spawn_pickup(self, pickup_type: PickupType, x: int, y: int) -> None:
        frames = self.pickup_assets.frames_for(pickup_type)
        self.pickups.add(Pickup(pickup_type, frames, x, y))

    def _use_bomb(self, is_panic_bomb: bool = False) -> bool:
        now = pygame.time.get_ticks() / 1000.0
        if is_panic_bomb:
            if (
                PANIC_BOMB_CONSUMES_PLAYER_BOMB
                and not self.player.can_use_bomb(now)
            ):
                return False
        elif not self.player.can_use_bomb(now):
            return False

        if not is_panic_bomb or PANIC_BOMB_CONSUMES_PLAYER_BOMB:
            self.player.mark_bomb_used(now)

        self.enemy_bullets.empty()
        self.sound.play("bomb_use")
        self.effects.add(
            AnimatedEffect(
                self.bomb_explosion_frames,
                self.player.rect.center,
                PLAYER_BOMB_EFFECT_FRAME_TIME,
            )
        )

        for enemy in list(self.enemies):
            if enemy.take_damage(BOMB_DAMAGE):
                self._destroy_enemy(enemy)

        boss = self.boss_group.sprite
        if boss and boss.take_damage(BOMB_DAMAGE):
            self._destroy_boss(boss)
        return True

    def _draw(self) -> None:
        self._draw_background()
        if self.state is GameState.MENU:
            self.effects.draw(self.screen)
            self.ui.draw_menu(self.screen)
        elif self.state is GameState.SCORES:
            self.effects.draw(self.screen)
            self.ui.draw_scores(self.screen, self.top_scores)
        elif self.state is GameState.OPENING_STORY:
            self.effects.draw(self.screen)
            self.ui.draw_opening_story(self.screen, self.opening_story_elapsed)
        elif self.state is GameState.BOSS_TEST_MENU:
            self.effects.draw(self.screen)
            self.ui.draw_boss_test_menu(self.screen)
        elif self.state is GameState.PLAYING:
            self.pickups.draw(self.screen)
            self.player_bullets.draw(self.screen)
            self.enemies.draw(self.screen)
            boss = self.boss_group.sprite
            if boss and boss.is_charging_radial:
                glow = pygame.Surface(BOSS_CHARGE_GLOW_SIZE, pygame.SRCALPHA)
                pygame.draw.circle(
                    glow,
                    BOSS_CHARGE_OUTER_GLOW_COLOR,
                    BOSS_CHARGE_GLOW_CENTER,
                    BOSS_CHARGE_OUTER_GLOW_RADIUS,
                    BOSS_CHARGE_OUTER_GLOW_WIDTH,
                )
                pygame.draw.circle(
                    glow,
                    BOSS_CHARGE_INNER_GLOW_COLOR,
                    BOSS_CHARGE_GLOW_CENTER,
                    BOSS_CHARGE_INNER_GLOW_RADIUS,
                    BOSS_CHARGE_INNER_GLOW_WIDTH,
                )
                self.screen.blit(glow, glow.get_rect(center=boss.rect.center))
            self.boss_group.draw(self.screen)
            self.enemy_bullets.draw(self.screen)
            self.shield_visual.draw(self.screen, self.player)
            self.screen.blit(self.player.image, self.player.rect)
            self.effects.draw(self.screen)
            now = pygame.time.get_ticks() / 1000.0
            self.ui.draw_hud(
                self.screen,
                self.player.score,
                self.player.lives,
                self.player.shield,
                PLAYER_MAX_SHIELD,
                self.player.weapon_level,
                self.player.bomb_count,
                self.player.bomb_cooldown_remaining(now),
            )
            if boss:
                self.ui.draw_boss_bar(self.screen, boss.hp, boss.max_hp)
            if self.status_message:
                self.ui.draw_status_message(self.screen, self.status_message)
        elif self.state is GameState.VICTORY:
            self.effects.draw(self.screen)
            if self.victory_elapsed < VICTORY_CONGRATULATIONS_SECONDS:
                self.ui.draw_congratulations(self.screen, self.player.score)
            else:
                credits_elapsed = self.victory_elapsed - VICTORY_CONGRATULATIONS_SECONDS
                self.ui.draw_victory(
                    self.screen,
                    self.player.score,
                    credits_elapsed,
                    self.top_scores,
                )
        elif self.state is GameState.GAME_OVER:
            self.effects.draw(self.screen)
            self.ui.draw_game_over(
                self.screen,
                self.player.score,
                self.continues_remaining,
                self._checkpoint_display_name(),
            )

        pygame.display.flip()

    def _draw_background(self) -> None:
        height = self.background.get_height()
        y = int(self.background_scroll)
        self.screen.blit(self.background, (0, y))
        self.screen.blit(self.background, (0, y - height))

    def _checkpoint_display_name(self) -> str:
        checkpoint_time = self.checkpoint_snapshot.time_seconds
        if checkpoint_time >= self.stage.boss_spawn_time:
            return CHECKPOINT_BOSS_LABEL
        if checkpoint_time <= CHECKPOINT_TIMES_SECONDS[0]:
            return CHECKPOINT_START_LABEL
        return f"{int(checkpoint_time)}s"

    def _save_game_over_score(self) -> None:
        if self.game_over_score_saved or self.boss_test_mode:
            return

        self.defeated_boss = False
        save_score(DEFAULT_PLAYER_NAME, self.player.score, self.reached_boss, self.defeated_boss)
        self.game_over_score_saved = True
        self.top_scores = get_top_scores()

    def _save_victory_score(self) -> None:
        if self.victory_score_saved or self.boss_test_mode:
            return

        self.defeated_boss = True
        save_score(DEFAULT_PLAYER_NAME, self.player.score, self.reached_boss, self.defeated_boss)
        self.victory_score_saved = True
        self.top_scores = get_top_scores()

    def _create_panic_projectile_image(self) -> pygame.Surface:
        image = self.projectile_assets.player[1].copy()
        image.fill((80, 255, 120, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return image

    def _shield_visual_size(self) -> tuple[int, int]:
        frame = self.player.assets[self.player.weapon_level][0]
        return (
            int(frame.get_width() * PLAYER_SHIELD_WIDTH_SCALE),
            int(frame.get_height() * PLAYER_SHIELD_HEIGHT_SCALE),
        )

    def _show_shield_hit_message(self) -> None:
        self.status_message = SHIELD_HIT_MESSAGE
        self.status_message_timer = SHIELD_HIT_MESSAGE_DURATION_SECONDS
