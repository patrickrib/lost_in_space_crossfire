from __future__ import annotations

import pygame

from .database import ScoreRecord
from .localization import (
    BACK_TO_MENU_PROMPT,
    BOSS_LABEL,
    BOSS_TEST_MENU_OPTIONS,
    BOSS_TEST_MENU_SUBTITLE,
    BOSS_TEST_MENU_TITLE,
    CHECKPOINT_LABEL,
    CONGRATULATIONS_LINES,
    CONGRATULATIONS_TITLE,
    CONTINUE_PROMPT,
    CONTINUES_REMAINING_LABEL,
    CREDITS_LINES,
    CREDITS_TITLE,
    FINAL_SCORE_LABEL,
    GAME_OVER_TITLE,
    HUD_LABELS,
    MENU_OPTIONS,
    MENU_TITLE_LINES,
    NO_CONTINUES_TEXT,
    OPENING_STORY,
    OPENING_STORY_PROMPT,
    REPLAY_PROMPT,
    RESTART_PROMPT,
    RANKING_EMPTY_TEXT,
    RANKING_SCORE_TEMPLATE,
    RANKING_TITLE,
    SCORES_TITLE,
)
from .settings import SCREEN_WIDTH
from .settings import (
    CREDITS_LINE_HEIGHT,
    CREDITS_SCROLL_SPEED,
    CREDITS_SCROLL_START_Y,
    OPENING_STORY_LINE_HEIGHT,
    OPENING_STORY_SCROLL_SPEED,
    OPENING_STORY_SCROLL_START_Y,
)


class UI:
    def __init__(self) -> None:
        self.title_font = pygame.font.Font(None, 64)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 26)
        self.small_font = pygame.font.Font(None, 22)

    def draw_menu(self, surface: pygame.Surface) -> None:
        self._draw_centered(
            surface,
            MENU_TITLE_LINES[0],
            self.title_font,
            125,
            (130, 235, 255),
        )
        self._draw_centered(
            surface,
            MENU_TITLE_LINES[1],
            self.subtitle_font,
            180,
            (255, 220, 120),
        )
        for index, line in enumerate(MENU_OPTIONS):
            self._draw_centered(
                surface,
                line,
                self.text_font,
                275 + index * 35,
                (235, 242, 255),
            )

    def draw_scores(self, surface: pygame.Surface, top_scores: list[ScoreRecord]) -> None:
        self._draw_centered(
            surface,
            SCORES_TITLE,
            self.title_font,
            82,
            (130, 255, 180),
        )
        self._draw_ranking(surface, top_scores, 150, max_records=10)
        self._draw_centered(
            surface,
            BACK_TO_MENU_PROMPT,
            self.text_font,
            670,
            (235, 242, 255),
        )

    def draw_opening_story(self, surface: pygame.Surface, elapsed_seconds: float) -> None:
        start_y = OPENING_STORY_SCROLL_START_Y - elapsed_seconds * OPENING_STORY_SCROLL_SPEED
        for index, line in enumerate(OPENING_STORY):
            if not line:
                continue
            y = int(start_y + index * OPENING_STORY_LINE_HEIGHT)
            self._draw_centered_if_visible(
                surface,
                line,
                self.text_font,
                y,
                (235, 242, 255),
                45,
                610,
            )
        self._draw_centered(surface, OPENING_STORY_PROMPT, self.text_font, 670, (255, 220, 120))

    def draw_boss_test_menu(self, surface: pygame.Surface) -> None:
        self._draw_centered(
            surface,
            BOSS_TEST_MENU_TITLE,
            self.title_font,
            150,
            (255, 220, 120),
        )
        self._draw_centered(
            surface,
            BOSS_TEST_MENU_SUBTITLE,
            self.subtitle_font,
            230,
            (235, 242, 255),
        )
        for index, line in enumerate(BOSS_TEST_MENU_OPTIONS):
            self._draw_centered(surface, line, self.text_font, 315 + index * 36, (235, 242, 255))

    def draw_hud(
        self,
        surface: pygame.Surface,
        score: int,
        lives: int,
        shield: int,
        max_shield: int,
        weapon_level: int,
        bombs: int,
        cooldown_remaining: float,
    ) -> None:
        cooldown_text = (
            HUD_LABELS["ready"]
            if cooldown_remaining <= 0
            else f"{cooldown_remaining:.1f}{HUD_LABELS['seconds_suffix']}"
        )
        lines = [
            f"{HUD_LABELS['score']}: {score}",
            f"{HUD_LABELS['lives']}: {lives}",
            f"{HUD_LABELS['shield']}: {shield}/{max_shield}",
            f"{HUD_LABELS['weapon']}: {weapon_level}",
            f"{HUD_LABELS['bombs']}: {bombs}",
            f"{HUD_LABELS['bomb']}: {cooldown_text}",
        ]
        for index, line in enumerate(lines):
            image = self.small_font.render(line, True, (235, 242, 255))
            surface.blit(image, (12, 10 + index * 22))

    def draw_boss_bar(self, surface: pygame.Surface, hp: int, max_hp: int) -> None:
        bar_rect = pygame.Rect(70, 36, SCREEN_WIDTH - 140, 14)
        pygame.draw.rect(surface, (45, 21, 31), bar_rect)
        fill_width = int(bar_rect.width * max(0, hp) / max_hp)
        pygame.draw.rect(
            surface,
            (220, 52, 70),
            (bar_rect.x, bar_rect.y, fill_width, bar_rect.height),
        )
        pygame.draw.rect(surface, (245, 220, 210), bar_rect, 2)
        self._draw_centered(surface, BOSS_LABEL, self.small_font, 20, (255, 230, 230))

    def draw_status_message(self, surface: pygame.Surface, message: str) -> None:
        self._draw_centered(surface, message, self.text_font, 145, (255, 235, 130))

    def draw_congratulations(self, surface: pygame.Surface, score: int) -> None:
        self._draw_centered(surface, CONGRATULATIONS_TITLE, self.title_font, 100, (130, 255, 180))
        for index, line in enumerate(CONGRATULATIONS_LINES):
            if not line:
                continue
            self._draw_centered(surface, line, self.text_font, 190 + index * 34, (235, 242, 255))
        self._draw_centered(
            surface,
            f"{FINAL_SCORE_LABEL}: {score}",
            self.text_font,
            455,
            (235, 242, 255),
        )

    def draw_victory(
        self,
        surface: pygame.Surface,
        score: int,
        elapsed_seconds: float,
        top_scores: list[ScoreRecord],
    ) -> None:
        start_y = CREDITS_SCROLL_START_Y - elapsed_seconds * CREDITS_SCROLL_SPEED
        self._draw_centered_if_visible(
            surface,
            CREDITS_TITLE,
            self.title_font,
            int(start_y),
            (130, 255, 180),
            -40,
            620,
        )
        for index, line in enumerate(CREDITS_LINES):
            if not line:
                continue
            y = int(start_y + 70 + index * CREDITS_LINE_HEIGHT)
            self._draw_centered_if_visible(
                surface,
                line,
                self.text_font,
                y,
                (235, 242, 255),
                -30,
                620,
            )
        ranking_start_index = len(CREDITS_LINES) + 1
        for index, line in enumerate(self._ranking_lines(top_scores)):
            y = int(start_y + 70 + (ranking_start_index + index) * CREDITS_LINE_HEIGHT)
            self._draw_centered_if_visible(
                surface,
                line,
                self.text_font,
                y,
                (255, 220, 120),
                -30,
                620,
            )
        self._draw_centered(
            surface,
            f"{FINAL_SCORE_LABEL}: {score}",
            self.small_font,
            642,
            (255, 220, 120),
        )
        self._draw_centered(surface, REPLAY_PROMPT, self.small_font, 672, (235, 242, 255))
        self._draw_centered(surface, BACK_TO_MENU_PROMPT, self.small_font, 696, (235, 242, 255))

    def draw_game_over(
        self,
        surface: pygame.Surface,
        score: int,
        continues_remaining: int,
        checkpoint_name: str,
    ) -> None:
        self._draw_centered(surface, GAME_OVER_TITLE, self.title_font, 190, (255, 94, 94))
        self._draw_centered(
            surface,
            f"{FINAL_SCORE_LABEL}: {score}",
            self.subtitle_font,
            285,
            (235, 242, 255),
        )
        if continues_remaining > 0:
            self._draw_centered(
                surface,
                f"{CONTINUES_REMAINING_LABEL}: {continues_remaining}",
                self.text_font,
                350,
                (255, 220, 120),
            )
            self._draw_centered(
                surface,
                f"{CHECKPOINT_LABEL}: {checkpoint_name}",
                self.text_font,
                385,
                (235, 242, 255),
            )
            self._draw_centered(surface, CONTINUE_PROMPT, self.text_font, 430, (235, 242, 255))
        else:
            self._draw_centered(surface, NO_CONTINUES_TEXT, self.text_font, 365, (255, 220, 120))
            self._draw_centered(surface, RESTART_PROMPT, self.text_font, 430, (235, 242, 255))
        self._draw_centered(surface, BACK_TO_MENU_PROMPT, self.text_font, 470, (235, 242, 255))

    def _draw_ranking(
        self,
        surface: pygame.Surface,
        top_scores: list[ScoreRecord],
        start_y: int,
        max_records: int | None = None,
    ) -> None:
        for index, line in enumerate(self._ranking_lines(top_scores, max_records)):
            color = (255, 220, 120) if index == 0 else (235, 242, 255)
            self._draw_centered(surface, line, self.small_font, start_y + index * 23, color)

    def _ranking_lines(
        self,
        top_scores: list[ScoreRecord],
        max_records: int | None = None,
    ) -> list[str]:
        if not top_scores:
            return [RANKING_TITLE, RANKING_EMPTY_TEXT]
        records = top_scores[:max_records] if max_records is not None else top_scores
        return [RANKING_TITLE] + [
            RANKING_SCORE_TEMPLATE.format(
                position=index,
                player_name=record.player_name,
                score=record.score,
            )
            for index, record in enumerate(records, start=1)
        ]

    def _draw_centered(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        y: int,
        color: tuple[int, int, int],
    ) -> None:
        image = font.render(text, True, color)
        rect = image.get_rect(center=(SCREEN_WIDTH // 2, y))
        surface.blit(image, rect)

    def _draw_centered_if_visible(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        y: int,
        color: tuple[int, int, int],
        min_y: int,
        max_y: int,
    ) -> None:
        if min_y <= y <= max_y:
            self._draw_centered(surface, text, font, y, color)
