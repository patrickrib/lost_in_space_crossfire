from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import pygame

from .decorators import safe_asset_loader
from .settings import SCREEN_HEIGHT, SCREEN_WIDTH
from .spritesheet import FrameRect, SpriteSheet


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def assets_root() -> Path:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(getattr(sys, "_MEIPASS")) / "assets")
    candidates.append(Path(sys.executable).resolve().parent / "assets")
    candidates.append(project_root() / "assets")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def asset_path(relative_path: Path | str) -> Path:
    return assets_root() / relative_path


@lru_cache(maxsize=None)
def load_image(relative_path: str) -> pygame.Surface:
    path = asset_path(relative_path)
    if not path.exists():
        raise FileNotFoundError(path)
    return pygame.image.load(str(path)).convert_alpha()


@safe_asset_loader(default=None)
def load_optional_image(relative_path: str) -> pygame.Surface | None:
    return load_image(relative_path)


def make_checker_pixels_transparent(surface: pygame.Surface) -> pygame.Surface:
    converted = surface.convert_alpha()
    width, height = converted.get_size()
    for y in range(height):
        for x in range(width):
            r, g, b, alpha = converted.get_at((x, y))
            if alpha == 0:
                continue
            if (
                r >= 220
                and g >= 220
                and b >= 220
                and max(r, g, b) - min(r, g, b) <= 18
            ):
                converted.set_at((x, y), (r, g, b, 0))
    return converted


def trim_transparent(surface: pygame.Surface) -> pygame.Surface:
    bounds = surface.get_bounding_rect(min_alpha=1)
    if bounds.width <= 0 or bounds.height <= 0:
        return surface
    trimmed = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
    trimmed.blit(surface, (0, 0), bounds)
    return trimmed


def prepare_frame(surface: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    transparent = make_checker_pixels_transparent(surface)
    trimmed = trim_transparent(transparent)
    return pygame.transform.smoothscale(trimmed, size)


def load_grid_frames(
    relative_path: Path,
    columns: int,
    rows: int,
    size: tuple[int, int],
    frame_count: int | None = None,
) -> list[pygame.Surface]:
    sheet = SpriteSheet(load_image(str(relative_path)))
    return [
        prepare_frame(frame, size)
        for frame in sheet.get_grid_frames(columns, rows, frame_count)
    ]


def load_manual_frames(
    relative_path: Path,
    rects: list[FrameRect],
    size: tuple[int, int],
) -> list[pygame.Surface]:
    sheet = SpriteSheet(load_image(str(relative_path)))
    return [prepare_frame(sheet.get_frame(rect), size) for rect in rects]


def create_fallback_background() -> pygame.Surface:
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surface.fill((7, 9, 24))
    for index in range(140):
        x = (index * 73) % SCREEN_WIDTH
        y = (index * 131) % SCREEN_HEIGHT
        shade = 110 + (index * 37) % 145
        radius = 1 if index % 6 else 2
        pygame.draw.circle(surface, (shade, shade, min(255, shade + 25)), (x, y), radius)
    for index in range(12):
        x = (index * 97) % SCREEN_WIDTH
        y = (index * 181) % SCREEN_HEIGHT
        pygame.draw.circle(surface, (28, 55, 86), (x, y), 22, 1)
    return surface.convert()


def load_background(relative_path: Path) -> pygame.Surface:
    image = load_optional_image(str(relative_path))
    if image is None:
        return create_fallback_background()
    ratio = SCREEN_WIDTH / image.get_width()
    scaled_height = max(SCREEN_HEIGHT, int(image.get_height() * ratio))
    return pygame.transform.smoothscale(image, (SCREEN_WIDTH, scaled_height)).convert()
