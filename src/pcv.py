from typing import Optional, Tuple, Dict, Any, List
import sys
import cv2
import numpy as np


class CameraManager:

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_opened = False

    def start(self) -> bool:
        if self.cap is not None and self.cap.isOpened():
            return True

        if sys.platform.startswith("win"):
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)
        else:
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            self.is_opened = False
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        self.is_opened = True
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_opened or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None

        frame_flipped = cv2.flip(frame, 1)
        return True, frame_flipped

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_opened = False


class PCVPipeline:

    LOWER_SKIN_1 = np.array([0, 30, 60], dtype=np.uint8)
    UPPER_SKIN_1 = np.array([20, 255, 255], dtype=np.uint8)

    LOWER_SKIN_2 = np.array([160, 30, 60], dtype=np.uint8)
    UPPER_SKIN_2 = np.array([180, 255, 255], dtype=np.uint8)

    PROC_WIDTH = 160
    PROC_HEIGHT = 120

    MIN_AREA = 35
    MAX_AREA = 8000

    @staticmethod
    def bgr_to_hsv(bgr_frame: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)

    @classmethod
    def threshold_skin(cls, hsv_frame: np.ndarray) -> np.ndarray:
        mask1 = cv2.inRange(hsv_frame, cls.LOWER_SKIN_1, cls.UPPER_SKIN_1)
        mask2 = cv2.inRange(hsv_frame, cls.LOWER_SKIN_2, cls.UPPER_SKIN_2)
        combined_mask = cv2.bitwise_or(mask1, mask2)
        return combined_mask

    @staticmethod
    def numpy_erode_3x3(binary_mask: np.ndarray) -> np.ndarray:
        h, w = binary_mask.shape
        padded = np.pad(binary_mask, pad_width=1, mode='constant', constant_values=0)

        eroded = np.ones((h, w), dtype=bool)

        for dy in range(3):
            for dx in range(3):
                eroded &= (padded[dy:dy + h, dx:dx + w] > 0)

        return (eroded.astype(np.uint8) * 255)

    @staticmethod
    def numpy_dilate_3x3(binary_mask: np.ndarray) -> np.ndarray:
        h, w = binary_mask.shape
        padded = np.pad(binary_mask, pad_width=1, mode='constant', constant_values=0)

        dilated = np.zeros((h, w), dtype=bool)

        for dy in range(3):
            for dx in range(3):
                dilated |= (padded[dy:dy + h, dx:dx + w] > 0)

        return (dilated.astype(np.uint8) * 255)

    @classmethod
    def numpy_opening(cls, binary_mask: np.ndarray) -> np.ndarray:
        eroded = cls.numpy_erode_3x3(binary_mask)
        opened = cls.numpy_dilate_3x3(eroded)
        return opened

    @classmethod
    def numpy_closing(cls, binary_mask: np.ndarray) -> np.ndarray:
        dilated = cls.numpy_dilate_3x3(binary_mask)
        closed = cls.numpy_erode_3x3(dilated)
        return closed

    @classmethod
    def connected_components_dfs(
        cls, mask: np.ndarray
    ) -> Tuple[Optional[Tuple[float, float]], int, np.ndarray]:
        h, w = mask.shape
        visited = np.zeros((h, w), dtype=bool)
        fg_y, fg_x = np.nonzero(mask > 0)

        largest_area = 0
        best_centroid: Optional[Tuple[float, float]] = None
        best_component_pixels: List[Tuple[int, int]] = []

        for sy, sx in zip(fg_y, fg_x):
            if visited[sy, sx]:
                continue

            stack = [(sy, sx)]
            visited[sy, sx] = True
            comp_pixels = []
            sum_x = 0
            sum_y = 0
            area = 0

            while stack:
                cy, cx = stack.pop()
                area += 1
                sum_x += cx
                sum_y += cy
                comp_pixels.append((cy, cx))

                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        if not visited[ny, nx] and mask[ny, nx] > 0:
                            visited[ny, nx] = True
                            stack.append((ny, nx))

            if cls.MIN_AREA <= area <= cls.MAX_AREA:
                if area > largest_area:
                    largest_area = area
                    best_centroid = (sum_x / area, sum_y / area)
                    best_component_pixels = comp_pixels

        comp_mask = np.zeros((h, w), dtype=np.uint8)
        if best_component_pixels:
            for py, px in best_component_pixels:
                comp_mask[py, px] = 255

        return best_centroid, largest_area, comp_mask


class HandTracker:

    def __init__(
        self,
        screen_width: int = 800,
        screen_height: int = 600,
        smoothing_alpha: float = 0.35,
        lost_timeout: float = 0.5,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.alpha = smoothing_alpha
        self.lost_timeout = lost_timeout

        self.x = float(screen_width // 2)
        self.y = float(screen_height // 2)

        self.is_detected = False
        self.sword_active = False
        self.lost_duration = 0.0
        self.current_area = 0

    def update(
        self,
        raw_centroid: Optional[Tuple[float, float]],
        proc_w: int,
        proc_h: int,
        area: int,
        dt: float,
    ) -> Tuple[int, int, bool, bool]:
        self.current_area = area

        if raw_centroid is not None:
            target_x = (raw_centroid[0] / proc_w) * self.screen_width
            target_y = (raw_centroid[1] / proc_h) * self.screen_height

            target_x = max(20.0, min(self.screen_width - 20.0, target_x))
            target_y = max(20.0, min(self.screen_height - 20.0, target_y))

            self.x = self.alpha * target_x + (1.0 - self.alpha) * self.x
            self.y = self.alpha * target_y + (1.0 - self.alpha) * self.y

            self.is_detected = True
            self.sword_active = True
            self.lost_duration = 0.0
        else:
            self.is_detected = False
            self.lost_duration += dt

            if self.lost_duration >= self.lost_timeout:
                self.sword_active = False

        return int(self.x), int(self.y), self.is_detected, self.sword_active
