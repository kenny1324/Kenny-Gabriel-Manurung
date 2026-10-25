from pathlib import Path
from typing import Dict, Optional, Tuple
import pygame


class AssetManager:

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent
        else:
            self.root_dir = base_dir

        self.assets_dir = self.root_dir / "assets"

        self._image_cache: Dict[str, pygame.Surface] = {}
        self._sound_cache: Dict[str, pygame.mixer.Sound] = {}

        self.music_playing = False
        self._init_audio_system()

    def _init_audio_system(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    def get_image(self, filename: str, target_size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        cache_key = f"{filename}_{target_size}"
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        filepath = self.assets_dir / filename

        image = pygame.image.load(str(filepath)).convert_alpha()
        if target_size is not None:
            image = pygame.transform.smoothscale(image, target_size)
        self._image_cache[cache_key] = image
        return image

    def play_music(self, filename: str = "music_result.mp3", volume: float = 0.5):
        if self.music_playing:
            return

        filepath = self.assets_dir / filename
        pygame.mixer.music.load(str(filepath))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        self.music_playing = True

    def get_sound(self, filename: str) -> pygame.mixer.Sound:
        if filename in self._sound_cache:
            return self._sound_cache[filename]

        filepath = self.assets_dir / filename
        sound = pygame.mixer.Sound(str(filepath))
        self._sound_cache[filename] = sound
        return sound
