from __future__ import annotations

import os
from typing import Optional, Tuple, Dict, Any

import cv2
import numpy as np
import pyautogui

# PyAutoGUI 交互安全设置：移动到屏幕左上角可触发 FailSafe 异常
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.02


# 功能：将输入图像转换为灰度，统一匹配的颜色空间。
def _to_gray(img: np.ndarray) -> np.ndarray:
    """将 BGR/RGB 图像转换为灰度。"""
    if len(img.shape) == 2:
        return img
    # 允许既可能是 RGB（来自 PIL）也可能是 BGR（来自 cv2）
    try:
        # 优先按 RGB 处理
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    except Exception:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# 功能：截取屏幕（可选区域），返回灰度或BGR图像。
def grab_screen(region: Optional[Tuple[int, int, int, int]] = None, grayscale: bool = True) -> np.ndarray:
    """
    截取屏幕区域为 np.ndarray。
    - region: (left, top, width, height)；None 表示全屏
    - grayscale: 是否返回灰度图
    返回：np.ndarray（灰度或 BGR）
    """
    pil_img = pyautogui.screenshot(region=region)
    img = np.array(pil_img)  # PIL -> RGB ndarray
    if grayscale:
        return _to_gray(img)
    else:
        # 保留为 BGR，便于与 cv2 算法统一
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


# 功能：从磁盘读取模板图像，支持灰度或彩色。
def _load_template(template_path: str, grayscale: bool = True) -> np.ndarray:
    """读取模板图片为 ndarray。"""
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    tpl = cv2.imread(template_path, flag)
    if tpl is None:
        raise ValueError(f"无法读取模板: {template_path}")
    return tpl


# 功能：在屏幕上进行模板匹配，返回命中位置与置信度。
def locate_on_screen(
    template_path: str,
    region: Optional[Tuple[int, int, int, int]] = None,
    confidence: float = 0.1,
    grayscale: bool = True,
    method: int = cv2.TM_CCOEFF_NORMED,
) -> Optional[Dict[str, Any]]:
    """
    使用 OpenCV 模板匹配在屏幕上定位目标。
    - template_path: 模板图片路径
    - region: (left, top, width, height)，限制搜索范围；None 为全屏
    - confidence: 置信度阈值（TM_CCOEFF_NORMED 模式下范围 0~1）
    - grayscale: 是否以灰度进行匹配（建议 True，提高速度与稳定性）
    - method: 匹配方法，默认归一化相关系数

    返回字典：{"left", "top", "width", "height", "center", "score"}；未命中返回 None。
    """
    screen = grab_screen(region=region, grayscale=grayscale)
    tpl = _load_template(template_path, grayscale=grayscale)

    if screen.shape[0] < tpl.shape[0] or screen.shape[1] < tpl.shape[1]:
        # 模板尺寸不能大于截屏区域
        return None

    res = cv2.matchTemplate(screen, tpl, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # TM_CCOEFF_NORMED：max_val 越接近 1 越匹配
    score = max_val
    if score < confidence:
        return None

    top_left = max_loc
    h, w = tpl.shape[:2]
    left = int(top_left[0]) + (region[0] if region else 0)
    top = int(top_left[1]) + (region[1] if region else 0)
    center = (left + w // 2, top + h // 2)

    return {
        "left": left,
        "top": top,
        "width": w,
        "height": h,
        "center": center,
        "score": float(score),
    }


# 功能：移动到指定坐标并执行点击操作。
def click_point(
    x: int,
    y: int,
    clicks: int = 1,
    interval: float = 0.1,
    button: str = "left",
    move_duration: float = 0.1,
) -> None:
    """移动到指定坐标并点击。"""
    pyautogui.moveTo(x, y, duration=move_duration)
    pyautogui.click(x=x, y=y, clicks=clicks, interval=interval, button=button)


# 功能：在屏幕上查找模板并点击命中中心（可偏移）。
def click_template(
    template_path: str,
    region: Optional[Tuple[int, int, int, int]] = None,
    confidence: float = 0.7,
    grayscale: bool = True,
    move_duration: float = 0.1,
    button: str = "left",
    clicks: int = 1,
    interval: float = 0.1,
    offset: Tuple[int, int] = (0, 0),
) -> bool:
    """
    在屏幕上定位模板并点击其中心（可加偏移）。
    返回是否点击成功。
    """
    match = locate_on_screen(
        template_path=template_path,
        region=region,
        confidence=confidence,
        grayscale=grayscale,
    )
    if not match:
        print(f"未找到模板 {template_path}")
        return False
    cx, cy = match["center"]
    ox, oy = offset
    click_point(cx + ox, cy + oy, clicks=clicks, interval=interval, button=button, move_duration=move_duration)
    return True


__all__ = [
    "grab_screen",
    "locate_on_screen",
    "click_point",
    "click_template",
]