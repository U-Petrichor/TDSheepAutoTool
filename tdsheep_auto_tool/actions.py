from __future__ import annotations

import time
from typing import Tuple, Sequence

import pyautogui as pag

# 适当减小默认停顿以提高动作连贯性
pag.PAUSE = 0.05
# 保留 FAILSAFE，鼠标移到屏幕左上角可触发异常以快速停止（可按需设为 False）
# pag.FAILSAFE = True


def sleep(sec: float) -> None:
    time.sleep(max(sec, 0.0))


def move_to(x: int, y: int, duration: float = 0.0) -> None:
    pag.moveTo(x, y, duration=duration)


def click(x: int, y: int, duration: float = 0.0) -> None:
    pag.moveTo(x, y, duration=duration)
    pag.click(x=x, y=y)


def click_center(match_xy: Tuple[int, int], size_wh: Tuple[int, int], duration: float = 0.0) -> None:
    mx, my = match_xy
    w, h = size_wh
    cx, cy = mx + w // 2, my + h // 2
    click(cx, cy, duration=duration)


def press(key: str) -> None:
    pag.press(key)


def hotkey(keys: Sequence[str]) -> None:
    if not keys:
        return
    pag.hotkey(*keys)