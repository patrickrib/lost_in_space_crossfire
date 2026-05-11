from __future__ import annotations

from pathlib import Path

import pygame

from .assets import asset_path
from .constants import SOUND_FILES


class SoundManager:
    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_path: Path | None = None

        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error as exc:
            print(f"Aviso de som: áudio desativado: {exc}")
            return

        self._load_sounds()

    def _load_sounds(self) -> None:
        for name, relative_path in SOUND_FILES.items():
            path = asset_path(relative_path)
            if not path.exists():
                print(f"Aviso de som: arquivo não encontrado: {path}")
                continue
            if name == "stage_theme":
                self.music_path = path
                continue
            try:
                self.sounds[name] = pygame.mixer.Sound(str(path))
            except pygame.error as exc:
                print(f"Aviso de som: não foi possível carregar {path}: {exc}")

    def play(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def play_music(self) -> None:
        if not self.enabled or self.music_path is None:
            return
        try:
            pygame.mixer.music.load(str(self.music_path))
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)
        except pygame.error as exc:
            print(f"Aviso de som: não foi possível tocar a música: {exc}")

    def stop_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.stop()
