from typing import List, Tuple, Dict, Any, Optional
import random
import pygame
from src.assets import AssetManager


DIFFICULTY_CONFIGS: Dict[str, Dict[str, Any]] = {
    "EASY": {
        "spawn_interval": 1.5,
        "meteor_speed_min": 170.0,
        "meteor_speed_max": 230.0,
        "fire_speed_min": 190.0,
        "fire_speed_max": 250.0,
        "fire_chance": 0.20,
    },
    "MEDIUM": {
        "spawn_interval": 1.0,
        "meteor_speed_min": 250.0,
        "meteor_speed_max": 330.0,
        "fire_speed_min": 280.0,
        "fire_speed_max": 360.0,
        "fire_chance": 0.30,
    },
    "HARD": {
        "spawn_interval": 0.6,
        "meteor_speed_min": 350.0,
        "meteor_speed_max": 440.0,
        "fire_speed_min": 380.0,
        "fire_speed_max": 490.0,
        "fire_chance": 0.35,
    },
}


class FallingObject:

    METEOR = "meteor"
    FIRE = "api"

    def __init__(
        self,
        obj_type: str,
        x: float,
        y: float,
        speed: float,
        width: int,
        height: int,
    ):
        self.obj_type = obj_type
        self.x = float(x)
        self.y = float(y)
        self.speed = float(speed)
        self.width = width
        self.height = height
        self.active = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, dt: float):
        if self.active:
            self.y += self.speed * dt

    def draw(self, surface: pygame.Surface, asset_manager: AssetManager):
        if not self.active:
            return

        filename = "meteor.png" if self.obj_type == self.METEOR else "api.png"
        sprite = asset_manager.get_image(filename, (self.width, self.height))
        surface.blit(sprite, (int(self.x), int(self.y)))


class Sword:

    def __init__(self, width: int = 56, height: int = 130):
        self.width = width
        self.height = height
        self.x = 400.0
        self.y = 450.0
        self.is_active = False

    def update_position(self, hand_x: int, hand_y: int, is_active: bool):
        self.x = float(hand_x - self.width // 2)
        self.y = float(hand_y - int(self.height * 0.75))
        self.is_active = is_active

    @property
    def rect(self) -> pygame.Rect:
        blade_height = int(self.height * 0.85)
        return pygame.Rect(int(self.x + 4), int(self.y), self.width - 8, blade_height)

    def draw(self, surface: pygame.Surface, asset_manager: AssetManager):
        base_sprite = asset_manager.get_image("pedang.png", (self.width, self.height))

        if self.is_active:
            surface.blit(base_sprite, (int(self.x), int(self.y)))
        else:
            faded = base_sprite.copy()
            faded.set_alpha(110)
            surface.blit(faded, (int(self.x), int(self.y)))


class GameEngine:

    INITIAL_HP = 6

    def __init__(self, screen_width: int = 800, screen_height: int = 600):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.score = 0
        self.hp = self.INITIAL_HP
        self.mode = "EASY"
        self.game_over = False

        self.objects: List[FallingObject] = []
        self.spawn_timer = 0.0

        self.meteor_size = (54, 54)
        self.fire_size = (48, 62)

    def reset(self, mode: Optional[str] = None):
        self.score = 0
        self.hp = self.INITIAL_HP
        if mode in DIFFICULTY_CONFIGS:
            self.mode = mode
        self.objects.clear()
        self.spawn_timer = 0.0
        self.game_over = False

    def update(
        self,
        dt: float,
        sword: Sword,
        asset_manager: AssetManager,
    ):
        if self.game_over:
            return

        config = DIFFICULTY_CONFIGS.get(self.mode, DIFFICULTY_CONFIGS["EASY"])

        self.spawn_timer += dt
        if self.spawn_timer >= config["spawn_interval"]:
            self.spawn_timer = 0.0
            self._spawn_random_object(config)

        for obj in self.objects:
            obj.update(dt)

        sword_box = sword.rect
        for obj in self.objects:
            if not obj.active:
                continue

            if sword.is_active and sword_box.colliderect(obj.rect):
                obj.active = False

                if obj.obj_type == FallingObject.METEOR:
                    self.score += 1
                    sfx = asset_manager.get_sound("sound_meteor_hit.mp3")
                    if sfx:
                        sfx.play()
                elif obj.obj_type == FallingObject.FIRE:
                    self.score += 2
                    sfx = asset_manager.get_sound("sound_fire_hit.mp3")
                    if sfx:
                        sfx.play()

        bottom_threshold = self.screen_height - 20
        for obj in self.objects:
            if not obj.active:
                continue

            if (obj.y + obj.height) >= bottom_threshold:
                obj.active = False

                if obj.obj_type == FallingObject.METEOR:
                    self.hp -= 1
                elif obj.obj_type == FallingObject.FIRE:
                    self.hp -= 2

        self.objects = [o for o in self.objects if o.active]

        if self.hp <= 0:
            self.hp = 0
            self.game_over = True

    def _spawn_random_object(self, config: Dict[str, Any]):
        is_fire = (random.random() < config["fire_chance"])

        if is_fire:
            obj_type = FallingObject.FIRE
            w, h = self.fire_size
            speed = random.uniform(config["fire_speed_min"], config["fire_speed_max"])
        else:
            obj_type = FallingObject.METEOR
            w, h = self.meteor_size
            speed = random.uniform(config["meteor_speed_min"], config["meteor_speed_max"])

        margin = 35
        x = random.randint(margin, max(margin + 10, self.screen_width - margin - w))
        y = -float(h)

        self.objects.append(FallingObject(obj_type, x, y, speed, w, h))

    def draw(
        self,
        surface: pygame.Surface,
        sword: Sword,
        asset_manager: AssetManager,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ):
        bg = asset_manager.get_image("backgroundmain.png", (self.screen_width, self.screen_height))
        surface.blit(bg, (0, 0))

        for obj in self.objects:
            obj.draw(surface, asset_manager)

        sword.draw(surface, asset_manager)

        self._draw_hud(surface, sword, font, small_font)

    def _draw_hud(
        self,
        surface: pygame.Surface,
        sword: Sword,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ):
        hud_bar = pygame.Surface((self.screen_width, 48), pygame.SRCALPHA)
        hud_bar.fill((10, 15, 25, 190))
        surface.blit(hud_bar, (0, 0))

        score_surf = font.render(f"SKOR: {self.score}", True, (255, 230, 80))
        surface.blit(score_surf, (20, 10))

        hp_text = font.render(f"HP: {self.hp}/{self.INITIAL_HP}", True, (255, 255, 255))
        surface.blit(hp_text, (200, 10))

        bar_x = 310
        bar_y = 15
        box_w = 20
        box_h = 16
        gap = 4
        for i in range(self.INITIAL_HP):
            bx = bar_x + i * (box_w + gap)
            if i < self.hp:
                color = (46, 204, 113) if self.hp > 2 else (231, 76, 60)
                pygame.draw.rect(surface, color, (bx, bar_y, box_w, box_h), border_radius=3)
            else:
                pygame.draw.rect(surface, (60, 65, 75), (bx, bar_y, box_w, box_h), border_radius=3)
            pygame.draw.rect(surface, (20, 25, 30), (bx, bar_y, box_w, box_h), 1, border_radius=3)

        mode_surf = small_font.render(f"MODE: {self.mode}", True, (180, 210, 255))
        surface.blit(mode_surf, (470, 15))

        if sword.is_active:
            status_text = "TANGAN: AKTIF"
            status_color = (46, 204, 113)
            indicator_color = (46, 204, 113)
        else:
            status_text = "TANGAN: HILANG"
            status_color = (231, 76, 60)
            indicator_color = (231, 76, 60)

        status_surf = small_font.render(status_text, True, status_color)
        surface.blit(status_surf, (self.screen_width - 150, 15))
        pygame.draw.circle(surface, indicator_color, (self.screen_width - 165, 24), 6)
