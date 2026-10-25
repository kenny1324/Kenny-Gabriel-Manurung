import sys
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
import pygame

from src.assets import AssetManager
from src.pcv import CameraManager, PCVPipeline, HandTracker
from src.game import GameEngine, Sword, DIFFICULTY_CONFIGS


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_DEMO = "demo"
STATE_GAMEOVER = "gameover"


class SwordDefenderApp:

    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Sword Defender - PCV Hand Tracking Game")
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("Arial", 42, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.tiny_font = pygame.font.SysFont("Arial", 12)

        self.assets = AssetManager()
        self.assets.play_music("music_result.mp3", volume=0.45)

        self.camera = CameraManager(camera_index=0, width=640, height=480)
        self.camera.start()

        self.tracker = HandTracker(
            screen_width=SCREEN_WIDTH,
            screen_height=SCREEN_HEIGHT,
            smoothing_alpha=0.35,
            lost_timeout=0.6,
        )

        self.engine = GameEngine(screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT)
        self.sword = Sword()

        self.state = STATE_MENU
        self.selected_mode = "EASY"
        self.camera_error_msg: Optional[str] = None
        self.running = True
        self._first_game_frame = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    break

            if not self.running:
                break

            if self.state == STATE_MENU:
                self._handle_menu_events(events)
                self._render_menu()
            elif self.state == STATE_GAME:
                self._handle_game_events(events)
                self._update_and_render_game(dt)
            elif self.state == STATE_DEMO:
                self._handle_demo_events(events)
                self._update_and_render_demo(dt)
            elif self.state == STATE_GAMEOVER:
                self._handle_gameover_events(events)
                self._render_gameover()

            pygame.display.flip()

        self._cleanup()

    def _handle_menu_events(self, events):
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_play.collidepoint(mouse_pos):
                    self._start_game_session()

                elif self.rect_demo.collidepoint(mouse_pos):
                    if not self.camera.is_opened:
                        if not self.camera.start():
                            self.camera_error_msg = "Kamera tidak terdeteksi! Hubungkan webcam untuk membuka demonstrasi."
                            continue
                    self.camera_error_msg = None
                    self.state = STATE_DEMO

                elif self.rect_mode_easy.collidepoint(mouse_pos):
                    self.selected_mode = "EASY"
                elif self.rect_mode_med.collidepoint(mouse_pos):
                    self.selected_mode = "MEDIUM"
                elif self.rect_mode_hard.collidepoint(mouse_pos):
                    self.selected_mode = "HARD"

                elif self.rect_exit.collidepoint(mouse_pos):
                    self.running = False

    def _start_game_session(self):
        if not self.camera.is_opened:
            if not self.camera.start():
                self.camera_error_msg = (
                    "Webcam gagal dibuka! Pastikan kamera terhubung dan tidak sedang digunakan aplikasi lain."
                )
                return

        self.camera_error_msg = None
        self.engine.reset(mode=self.selected_mode)
        self.sword.update_position(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120, is_active=False)
        self._first_game_frame = True
        self.state = STATE_GAME

    def _render_menu(self):
        bg = self.assets.get_image("backgroundmenu.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(bg, (0, 0))

        title_surf = self.title_font.render("SWORD DEFENDER", True, (255, 235, 120))
        title_shadow = self.title_font.render("SWORD DEFENDER", True, (30, 20, 10))
        self.screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + 2, 52))
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 50))

        subtitle = self.small_font.render(
            "Project Pengolahan Citra dan Video (PCV) - Hand Tracking Defense", True, (200, 220, 245)
        )
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 102))

        menu_card = pygame.Surface((460, 420), pygame.SRCALPHA)
        menu_card.fill((15, 20, 35, 210))
        self.screen.blit(menu_card, (SCREEN_WIDTH // 2 - 230, 140))
        pygame.draw.rect(self.screen, (70, 90, 130), (SCREEN_WIDTH // 2 - 230, 140, 460, 420), 2, border_radius=8)

        mouse_pos = pygame.mouse.get_pos()

        self.rect_play = pygame.Rect(SCREEN_WIDTH // 2 - 180, 165, 360, 52)
        is_hover_play = self.rect_play.collidepoint(mouse_pos)
        play_color = (46, 175, 110) if is_hover_play else (38, 145, 90)
        pygame.draw.rect(self.screen, play_color, self.rect_play, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), self.rect_play, 2 if is_hover_play else 1, border_radius=6)
        play_txt = self.button_font.render(f"PLAY ({self.selected_mode})", True, (255, 255, 255))
        self.screen.blit(play_txt, (self.rect_play.centerx - play_txt.get_width() // 2, self.rect_play.centery - play_txt.get_height() // 2))

        self.rect_demo = pygame.Rect(SCREEN_WIDTH // 2 - 180, 235, 360, 48)
        is_hover_demo = self.rect_demo.collidepoint(mouse_pos)
        demo_color = (60, 110, 190) if is_hover_demo else (45, 85, 150)
        pygame.draw.rect(self.screen, demo_color, self.rect_demo, border_radius=6)
        pygame.draw.rect(self.screen, (200, 220, 255), self.rect_demo, 2 if is_hover_demo else 1, border_radius=6)
        demo_txt = self.button_font.render("DEMONSTRATION (PCV)", True, (255, 255, 255))
        self.screen.blit(demo_txt, (self.rect_demo.centerx - demo_txt.get_width() // 2, self.rect_demo.centery - demo_txt.get_height() // 2))

        mode_label = self.font.render("PILIH TINGKAT KESULITAN (MODE):", True, (220, 230, 250))
        self.screen.blit(mode_label, (SCREEN_WIDTH // 2 - 180, 305))

        btn_w = 110
        btn_h = 42
        gap = 15
        start_x = SCREEN_WIDTH // 2 - 180

        self.rect_mode_easy = pygame.Rect(start_x, 335, btn_w, btn_h)
        self.rect_mode_med = pygame.Rect(start_x + btn_w + gap, 335, btn_w, btn_h)
        self.rect_mode_hard = pygame.Rect(start_x + (btn_w + gap) * 2, 335, btn_w, btn_h)

        modes = [
            ("EASY", self.rect_mode_easy, (46, 204, 113)),
            ("MEDIUM", self.rect_mode_med, (241, 196, 15)),
            ("HARD", self.rect_mode_hard, (231, 76, 60)),
        ]

        for name, rect, active_color in modes:
            is_active = (self.selected_mode == name)
            is_hover = rect.collidepoint(mouse_pos)

            if is_active:
                box_color = active_color
                border_color = (255, 255, 255)
                text_color = (20, 20, 20)
                border_width = 3
            else:
                box_color = (35, 45, 65) if is_hover else (25, 30, 45)
                border_color = (80, 95, 125)
                text_color = (200, 210, 225)
                border_width = 1

            pygame.draw.rect(self.screen, box_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, rect, border_width, border_radius=5)
            txt = self.font.render(name, True, text_color)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        self.rect_exit = pygame.Rect(SCREEN_WIDTH // 2 - 180, 475, 360, 44)
        is_hover_exit = self.rect_exit.collidepoint(mouse_pos)
        exit_color = (180, 50, 50) if is_hover_exit else (140, 40, 40)
        pygame.draw.rect(self.screen, exit_color, self.rect_exit, border_radius=6)
        pygame.draw.rect(self.screen, (255, 180, 180), self.rect_exit, 2 if is_hover_exit else 1, border_radius=6)
        exit_txt = self.button_font.render("EXIT", True, (255, 255, 255))
        self.screen.blit(exit_txt, (self.rect_exit.centerx - exit_txt.get_width() // 2, self.rect_exit.centery - exit_txt.get_height() // 2))

        if self.camera_error_msg:
            err_box = pygame.Rect(50, SCREEN_HEIGHT - 60, SCREEN_WIDTH - 100, 40)
            pygame.draw.rect(self.screen, (220, 50, 50), err_box, border_radius=5)
            pygame.draw.rect(self.screen, (255, 255, 255), err_box, 1, border_radius=5)
            err_txt = self.small_font.render(self.camera_error_msg, True, (255, 255, 255))
            self.screen.blit(err_txt, (err_box.centerx - err_txt.get_width() // 2, err_box.centery - err_txt.get_height() // 2))

    def _handle_game_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = STATE_MENU

    def _update_and_render_game(self, dt: float):
        if self._first_game_frame:
            self._first_game_frame = False
            dt = 0.0

        ret, frame = self.camera.read_frame()
        if ret and frame is not None:
            proc_frame = cv2.resize(
                frame,
                (PCVPipeline.PROC_WIDTH, PCVPipeline.PROC_HEIGHT),
                interpolation=cv2.INTER_LINEAR,
            )
            hsv = PCVPipeline.bgr_to_hsv(proc_frame)
            skin_mask = PCVPipeline.threshold_skin(hsv)
            opened = PCVPipeline.numpy_opening(skin_mask)
            closed = PCVPipeline.numpy_closing(opened)
            centroid, area, _ = PCVPipeline.connected_components_dfs(closed)

            hand_x, hand_y, is_detected, sword_active = self.tracker.update(
                centroid,
                PCVPipeline.PROC_WIDTH,
                PCVPipeline.PROC_HEIGHT,
                area,
                dt,
            )
            self.sword.update_position(hand_x, hand_y, is_active=sword_active)
        else:
            hand_x, hand_y, is_detected, sword_active = self.tracker.update(
                None,
                PCVPipeline.PROC_WIDTH,
                PCVPipeline.PROC_HEIGHT,
                0,
                dt,
            )
            self.sword.update_position(hand_x, hand_y, is_active=sword_active)

        self.engine.update(dt, self.sword, self.assets)

        self.engine.draw(self.screen, self.sword, self.assets, self.font, self.small_font)

        if self.engine.game_over:
            self.state = STATE_GAMEOVER

    def _handle_demo_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_m):
                self.state = STATE_MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_demo_back.collidepoint(mouse_pos):
                    self.state = STATE_MENU

    def _update_and_render_demo(self, dt: float):
        self.screen.fill((18, 22, 32))

        top_bar = pygame.Surface((SCREEN_WIDTH, 48))
        top_bar.fill((12, 16, 24))
        self.screen.blit(top_bar, (0, 0))

        title_demo = self.button_font.render(
            "DEMONSTRASI TAHAPAN METODE PCV SECARA REALTIME", True, (255, 230, 100)
        )
        self.screen.blit(title_demo, (20, 12))

        self.rect_demo_back = pygame.Rect(SCREEN_WIDTH - 170, 8, 150, 32)
        mouse_pos = pygame.mouse.get_pos()
        is_hover_back = self.rect_demo_back.collidepoint(mouse_pos)
        pygame.draw.rect(
            self.screen,
            (50, 75, 120) if is_hover_back else (35, 55, 90),
            self.rect_demo_back,
            border_radius=4,
        )
        pygame.draw.rect(self.screen, (200, 220, 255), self.rect_demo_back, 1, border_radius=4)
        back_txt = self.small_font.render("MENU UTAMA [ESC]", True, (255, 255, 255))
        self.screen.blit(back_txt, (self.rect_demo_back.centerx - back_txt.get_width() // 2, self.rect_demo_back.centery - back_txt.get_height() // 2))

        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            err_box = self.font.render("Gagal membaca frame kamera!", True, (240, 80, 80))
            self.screen.blit(err_box, (SCREEN_WIDTH // 2 - err_box.get_width() // 2, 250))
            return

        p_w, p_h = 240, 165
        proc_w, proc_h = PCVPipeline.PROC_WIDTH, PCVPipeline.PROC_HEIGHT

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        panel1_img = cv2.resize(rgb_frame, (p_w, p_h), interpolation=cv2.INTER_LINEAR)

        proc_frame = cv2.resize(frame, (proc_w, proc_h), interpolation=cv2.INTER_LINEAR)
        hsv = PCVPipeline.bgr_to_hsv(proc_frame)
        skin_mask = PCVPipeline.threshold_skin(hsv)
        panel2_img = cv2.resize(skin_mask, (p_w, p_h), interpolation=cv2.INTER_NEAREST)
        panel2_rgb = cv2.cvtColor(panel2_img, cv2.COLOR_GRAY2RGB)

        opened = PCVPipeline.numpy_opening(skin_mask)
        panel3_img = cv2.resize(opened, (p_w, p_h), interpolation=cv2.INTER_NEAREST)
        panel3_rgb = cv2.cvtColor(panel3_img, cv2.COLOR_GRAY2RGB)

        closed = PCVPipeline.numpy_closing(opened)
        panel4_img = cv2.resize(closed, (p_w, p_h), interpolation=cv2.INTER_NEAREST)
        panel4_rgb = cv2.cvtColor(panel4_img, cv2.COLOR_GRAY2RGB)

        centroid, area, comp_mask = PCVPipeline.connected_components_dfs(closed)

        panel5_rgb = np.zeros((proc_h, proc_w, 3), dtype=np.uint8)
        if area > 0:
            panel5_rgb[comp_mask > 0] = [30, 220, 160]

        if centroid is not None:
            cx_int, cy_int = int(centroid[0]), int(centroid[1])
            cv2.circle(panel5_rgb, (cx_int, cy_int), 6, (255, 60, 60), -1)
            cv2.drawMarker(panel5_rgb, (cx_int, cy_int), (255, 255, 255), cv2.MARKER_CROSS, 12, 1)

        panel5_img = cv2.resize(panel5_rgb, (p_w, p_h), interpolation=cv2.INTER_NEAREST)

        screen_x, screen_y, is_detected, sword_active = self.tracker.update(
            centroid, proc_w, proc_h, area, dt
        )

        panels = [
            ("1. Kamera Asli (RGB Flipped)", panel1_img, 20, 65),
            ("2. Thresholding HSV Kulit", panel2_rgb, 280, 65),
            ("3. Morfologi Opening (Erosi->Dilasi)", panel3_rgb, 540, 65),
            ("4. Morfologi Closing (Dilasi->Erosi)", panel4_rgb, 260, 270),
            ("5. Connected Component (DFS) & Centroid", panel5_img, 20, 270),
        ]

        for label, img_arr, px, py in panels:
            surf = pygame.image.frombuffer(img_arr.tobytes(), (p_w, p_h), "RGB")
            self.screen.blit(surf, (px, py))
            pygame.draw.rect(self.screen, (70, 95, 140), (px, py, p_w, p_h), 1)
            lbl_bg = pygame.Surface((p_w, 22))
            lbl_bg.fill((20, 28, 45))
            self.screen.blit(lbl_bg, (px, py - 22))
            lbl_txt = self.tiny_font.render(label, True, (220, 235, 255))
            self.screen.blit(lbl_txt, (px + 5, py - 18))

        card_x, card_y = 520, 270
        card_w, card_h = 260, 310
        card_surf = pygame.Surface((card_w, card_h))
        card_surf.fill((14, 20, 32))
        self.screen.blit(card_surf, (card_x, card_y))
        pygame.draw.rect(self.screen, (80, 110, 160), (card_x, card_y, card_w, card_h), 2, border_radius=4)

        card_title = self.font.render("TELEMETRI SISTEM PCV", True, (255, 215, 80))
        self.screen.blit(card_title, (card_x + 15, card_y + 12))

        status_str = "TERDETEKSI" if is_detected else "TIDAK TERDETEKSI / HILANG"
        status_col = (46, 204, 113) if is_detected else (231, 76, 60)
        self.screen.blit(self.tiny_font.render("Status Deteksi Tangan:", True, (180, 195, 220)), (card_x + 15, card_y + 40))
        self.screen.blit(self.font.render(status_str, True, status_col), (card_x + 15, card_y + 55))

        coord_str = f"X: {screen_x} px,  Y: {screen_y} px" if is_detected else "X: --- ,  Y: ---"
        self.screen.blit(self.tiny_font.render("Koordinat Layar Pedang:", True, (180, 195, 220)), (card_x + 15, card_y + 85))
        self.screen.blit(self.font.render(coord_str, True, (240, 245, 255)), (card_x + 15, card_y + 100))

        area_str = f"{area} piksel" if is_detected else "0 piksel"
        self.screen.blit(self.tiny_font.render("Luas Komponen (DFS Area):", True, (180, 195, 220)), (card_x + 15, card_y + 130))
        self.screen.blit(self.font.render(area_str, True, (240, 245, 255)), (card_x + 15, card_y + 145))

        self.screen.blit(self.tiny_font.render("Ambang Batas Rentang HSV Kulit:", True, (180, 195, 220)), (card_x + 15, card_y + 175))
        self.screen.blit(self.tiny_font.render("Rentang 1 : H:[0-20], S:[30-255], V:[60-255]", True, (200, 215, 240)), (card_x + 15, card_y + 195))
        self.screen.blit(self.tiny_font.render("Rentang 2 : H:[160-180], S:[30-255], V:[60-255]", True, (200, 215, 240)), (card_x + 15, card_y + 215))

        fps_val = int(self.clock.get_fps())
        self.screen.blit(self.tiny_font.render(f"Kecepatan Render: {fps_val} FPS (Realtime)", True, (100, 220, 100)), (card_x + 15, card_y + 245))
        self.screen.blit(self.tiny_font.render("Metode: NumPy Morphology & Stack DFS", True, (160, 175, 200)), (card_x + 15, card_y + 270))

        footer = self.tiny_font.render(
            "Gunakan latar belakang kontras dan pencahayaan merata untuk hasil segmentasi kulit terbaik.",
            True,
            (140, 155, 180),
        )
        self.screen.blit(footer, (20, SCREEN_HEIGHT - 22))

    def _handle_gameover_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect_retry.collidepoint(mouse_pos):
                    self._start_game_session()
                elif self.rect_menu_btn.collidepoint(mouse_pos):
                    self.state = STATE_MENU

    def _render_gameover(self):
        bg = self.assets.get_image("backgroundskor.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.blit(bg, (0, 0))

        card_w, card_h = 480, 420
        cx = SCREEN_WIDTH // 2 - card_w // 2
        cy = SCREEN_HEIGHT // 2 - card_h // 2
        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((12, 16, 26, 225))
        self.screen.blit(card, (cx, cy))
        pygame.draw.rect(self.screen, (180, 50, 50), (cx, cy, card_w, card_h), 2, border_radius=8)

        go_title = self.title_font.render("GAME OVER", True, (240, 60, 60))
        self.screen.blit(go_title, (SCREEN_WIDTH // 2 - go_title.get_width() // 2, cy + 30))

        sub_go = self.small_font.render("Benteng Pertahanan Telah Runtuh!", True, (200, 160, 160))
        self.screen.blit(sub_go, (SCREEN_WIDTH // 2 - sub_go.get_width() // 2, cy + 85))

        score_label = self.font.render("SKOR AKHIR", True, (210, 220, 240))
        self.screen.blit(score_label, (SCREEN_WIDTH // 2 - score_label.get_width() // 2, cy + 130))

        score_val = self.title_font.render(str(self.engine.score), True, (255, 230, 80))
        self.screen.blit(score_val, (SCREEN_WIDTH // 2 - score_val.get_width() // 2, cy + 160))

        mode_info = self.small_font.render(f"Tingkat Kesulitan: {self.engine.mode}", True, (170, 190, 220))
        self.screen.blit(mode_info, (SCREEN_WIDTH // 2 - mode_info.get_width() // 2, cy + 225))

        mouse_pos = pygame.mouse.get_pos()

        self.rect_retry = pygame.Rect(cx + 40, cy + 270, card_w - 80, 48)
        is_hover_retry = self.rect_retry.collidepoint(mouse_pos)
        retry_col = (46, 175, 110) if is_hover_retry else (38, 145, 90)
        pygame.draw.rect(self.screen, retry_col, self.rect_retry, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), self.rect_retry, 2 if is_hover_retry else 1, border_radius=6)
        retry_txt = self.button_font.render("PLAY AGAIN", True, (255, 255, 255))
        self.screen.blit(retry_txt, (self.rect_retry.centerx - retry_txt.get_width() // 2, self.rect_retry.centery - retry_txt.get_height() // 2))

        self.rect_menu_btn = pygame.Rect(cx + 40, cy + 335, card_w - 80, 44)
        is_hover_menu = self.rect_menu_btn.collidepoint(mouse_pos)
        menu_col = (60, 90, 140) if is_hover_menu else (45, 70, 110)
        pygame.draw.rect(self.screen, menu_col, self.rect_menu_btn, border_radius=6)
        pygame.draw.rect(self.screen, (200, 220, 255), self.rect_menu_btn, 2 if is_hover_menu else 1, border_radius=6)
        menu_txt = self.button_font.render("MAIN MENU", True, (255, 255, 255))
        self.screen.blit(menu_txt, (self.rect_menu_btn.centerx - menu_txt.get_width() // 2, self.rect_menu_btn.centery - menu_txt.get_height() // 2))

    def _cleanup(self):
        self.camera.release()
        cv2.destroyAllWindows()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    app = SwordDefenderApp()
    app.run()
