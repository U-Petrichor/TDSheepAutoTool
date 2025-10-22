from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import numpy as np
import cv2
import pyautogui


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)


class Screen:
    def __init__(self) -> None:
        # pyautogui 默认使用主显示器坐标系；多显示器时请确保游戏在主屏或自行调整坐标
        pyautogui.PAUSE = 0.01

    def grab(self, region: Optional[Region] = None) -> np.ndarray:
        if region is None:
            pil_img = pyautogui.screenshot()
        else:
            pil_img = pyautogui.screenshot(region=region.to_tuple())
        arr = np.array(pil_img)  # RGB 或 RGBA
        if arr.ndim == 2:
            arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        elif arr.shape[2] == 4:
            # RGBA -> RGB -> BGR
            arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        else:
            # RGB -> BGR
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        return arr


def to_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def match_template(image: np.ndarray, template: np.ndarray, threshold: float = 0.85) -> List[Tuple[int, int, float]]:
    """返回匹配到的左上角坐标和相似度列表"""
    img_gray = to_gray(image)
    tmpl_gray = to_gray(template)
    result = cv2.matchTemplate(img_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result >= threshold)
    matches: List[Tuple[int, int, float]] = []
    for pt in zip(*loc[::-1]):
        score = float(result[pt[1], pt[0]])
        matches.append((int(pt[0]), int(pt[1]), score))
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


def load_template(path: str) -> np.ndarray:
    tmpl = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if tmpl is None:
        raise FileNotFoundError(f"模板未找到或无法读取: {path}")
    if tmpl.ndim == 3 and tmpl.shape[2] == 4:
        tmpl = cv2.cvtColor(tmpl, cv2.COLOR_BGRA2BGR)
    return tmpl


def find_one(image: np.ndarray, template_path: str, threshold: float) -> Optional[Tuple[int, int, float, Tuple[int, int]]]:
    """
    在给定图片中查找模板的第一个匹配。
    返回: (x, y, score, (w, h)) 或 None
    """
    tmpl = load_template(template_path)
    matches = match_template(image, tmpl, threshold)
    if not matches:
        return None
    h, w = tmpl.shape[:2]
    x, y, score = matches[0]
    return (x, y, score, (w, h))