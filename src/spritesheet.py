from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class FrameRect:
    x: int
    y: int
    width: int
    height: int

    @property
    def pygame_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)


class SpriteSheet:
    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface

    def get_frame(self, rect: FrameRect) -> pygame.Surface:
        frame = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        frame.blit(self.surface, (0, 0), rect.pygame_rect)
        return frame

    def get_grid_frames(
        self,
        columns: int,
        rows: int,
        frame_count: int | None = None,
    ) -> list[pygame.Surface]:
        frame_width = self.surface.get_width() // columns
        frame_height = self.surface.get_height() // rows
        frames: list[pygame.Surface] = []
        for row in range(rows):
            for column in range(columns):
                if frame_count is not None and len(frames) >= frame_count:
                    return frames
                frames.append(
                    self.get_frame(
                        FrameRect(
                            column * frame_width,
                            row * frame_height,
                            frame_width,
                            frame_height,
                        )
                    )
                )
        return frames
