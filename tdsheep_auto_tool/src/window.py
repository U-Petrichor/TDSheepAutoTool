from __future__ import annotations

"""
    window.py
    - 功能：负责游戏窗口的初始化、检测、定位与尺寸计算
"""

import json
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pyautogui

from .match import (
    get_assets_dir,
    load_scale_state,
    save_scale_state,
    match_with_scales,
    clamp_scale,
    find_template_path,
    click_template,
)

# 基础窗口尺寸（100% 缩放时）
BASE_WINDOW_SIZE: Tuple[int, int] = (1066, 912)
ANCHOR_TOP_MENU_OFFSET_X_BASE: int = 1  # 100% 缩放时需向右偏移 1px
ANCHOR_TOP_MENU_OFFSET_Y_BASE: int = 42  # 100% 缩放时需向下偏移 42px


def _load_window_config() -> Dict[str, Any]:
    """加载窗口相关配置（可选），包含锚点、偏移与红框时长。"""
    default = {
        "anchor": "a_2",            # 以 a_2 为左上角菜单锚点（你提供的 a_2_100.png）
        "anchor_offset": [0, 0],     # 若锚点不在窗口正左上，可在此配置校正
        "base_size": [BASE_WINDOW_SIZE[0], BASE_WINDOW_SIZE[1]],
        "frame_duration_sec": 5.0,
    }
    try:
        project_root = Path(__file__).resolve().parent.parent.parent
        cfg_path = project_root / "config.json"
        if not cfg_path.exists():
            return default
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        w = data.get("window", {})
        anchor = str(w.get("anchor", default["anchor"])).strip() or default["anchor"]
        offs = w.get("anchor_offset", default["anchor_offset"]) or default["anchor_offset"]
        base = w.get("base_size", default["base_size"]) or default["base_size"]
        dur = float(w.get("frame_duration_sec", default["frame_duration_sec"]))
        # 兜底纠偏（保持健壮）
        if not (isinstance(base, (list, tuple)) and len(base) == 2):
            base = default["base_size"]
        if not (isinstance(offs, (list, tuple)) and len(offs) == 2):
            offs = default["anchor_offset"]
        return {
            "anchor": anchor,
            "anchor_offset": [int(offs[0]), int(offs[1])],
            "base_size": [int(base[0]), int(base[1])],
            "frame_duration_sec": dur,
        }
    except Exception as e:
        print(f"[config] 读取 window 配置失败，使用默认: {e}")
        return default


def compute_window_geometry(matches: Dict[str, Any], recommended_scale: Optional[int]) -> Optional[Dict[str, int]]:
    """根据锚点与比例计算游戏窗口的屏幕坐标与尺寸。"""
    cfg = _load_window_config()
    anchor_stem = cfg["anchor"]
    off_x, off_y = cfg["anchor_offset"]
    base_w, base_h = cfg["base_size"]

    rec = clamp_scale(int(recommended_scale or 100))
    scale = rec / 100.0

    anchor = matches.get(anchor_stem)
    if not isinstance(anchor, dict):
        print(f"[size] 缺少锚点 {anchor_stem} 的匹配结果，无法计算窗口位置")
        return None

    # 按比例缩放的偏移：用户配置的 anchor_offset 与顶部菜单基准下移 40px
    ox = int(round(off_x * scale))
    oy = int(round(off_y * scale))
    menu_ox =int(round(ANCHOR_TOP_MENU_OFFSET_X_BASE * scale))
    menu_oy = int(round(ANCHOR_TOP_MENU_OFFSET_Y_BASE * scale))

    left = int(anchor.get("left", 0)) + ox + menu_ox
    top = int(anchor.get("top", 0)) + oy + menu_oy
    width = int(round(base_w * scale))
    height = int(round(base_h * scale))

    try:
        sw, sh = pyautogui.size()
        left = max(0, min(left, sw - 1))
        top = max(0, min(top, sh - 1))
        width = max(1, min(width, sw - left))
        height = max(1, min(height, sh - top))
    except Exception:
        pass

    return {"left": left, "top": top, "width": width, "height": height}


def show_window_frame(rect: Dict[str, int], duration_sec: float = 5.0, color: str = "red", thickness: int = 4) -> None:
    """在屏幕上以透明叠加方式展示空心红框，持续指定秒数。"""
    try:
        import tkinter as tk
    except Exception as e:
        print(f"[frame] Tkinter 不可用，无法显示红框: {e}")
        return

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    transparent = "#00FF00"  # 用作整窗透明背景色
    try:
        root.wm_attributes("-transparentcolor", transparent)
    except Exception:
        # 在不支持 transparentcolor 的环境下退化为半透明整体窗口
        root.attributes("-alpha", 0.3)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{screen_w}x{screen_h}+0+0")

    canvas = tk.Canvas(root, width=screen_w, height=screen_h, bg=transparent, highlightthickness=0)
    canvas.pack()

    x0 = int(rect["left"]) ; y0 = int(rect["top"]) ; x1 = x0 + int(rect["width"]) ; y1 = y0 + int(rect["height"]) 
    canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=thickness)

    root.after(int(duration_sec * 1000), root.destroy)
    root.mainloop()


def compute_window_size_and_visualize(matches: Dict[str, Any], recommended_scale: Optional[int]) -> Optional[Dict[str, int]]:
    """计算窗口位置并叠加空心红框 5s，返回窗口矩形。"""
    cfg = _load_window_config()
    rect = compute_window_geometry(matches, recommended_scale)
    if rect is None:
        return None
    print(f"[size] 窗口位置: left={rect['left']}, top={rect['top']}, size={rect['width']}x{rect['height']}")
    show_window_frame(rect, duration_sec=float(cfg.get("frame_duration_sec", 5.0)))
    return rect


def detect_window_assets_a(
    confidence: float = 0.7,
    grayscale: bool = True,
    region: Optional[Tuple[int, int, int, int]] = None,
    click: bool = False,
    click_move_duration: float = 0.05,
):
    # 目录
    assets_a = get_assets_dir() / 'a'

    # 加载比例状态
    state = load_scale_state()
    recommended = int(state.get("recommended_scale", 100))
    recommended = clamp_scale(recommended)

    results: Dict[str, Any] = {}
    success = True

    # 可替代的左下角切换好友（a_5 灰 或 a_6 亮）
    friend_match = None
    friend_scale_used = None
    for stem in ["a_5", "a_6"]:
        m, used_scale = match_with_scales(
            assets_a, stem, recommended, confidence, grayscale, region
        )
        if m:
            friend_match = {"name": stem, "data": m}
            friend_scale_used = used_scale
            # 动态更新推荐比例（立即生效，后续优先）
            if used_scale is not None:
                recommended = used_scale
                state["recommended_scale"] = used_scale
                state.setdefault("per_template", {})[stem] = used_scale
            if click:
                tpl = find_template_path(assets_a, stem, used_scale or recommended)
                if tpl:
                    click_template(
                        template_path=str(tpl),
                        region=region,
                        confidence=confidence,
                        grayscale=grayscale,
                        move_duration=click_move_duration,
                    )
            break
    if not friend_match:
        print("[match] 未识别到左下角切换好友，请调整窗口后重试")
        success = False
    results["friend_switch"] = friend_match

    # 右下角 UI（a_3 或 a_4）
    ui_match = None
    for stem in ["a_3", "a_4"]:
        m, used_scale = match_with_scales(
            assets_a, stem, recommended, confidence, grayscale, region
        )
        if m:
            ui_match = {"name": stem, "data": m}
            if used_scale is not None:
                recommended = used_scale
                state["recommended_scale"] = used_scale
                state.setdefault("per_template", {})[stem] = used_scale
            if click:
                tpl = find_template_path(assets_a, stem, used_scale or recommended)
                if tpl:
                    click_template(
                        template_path=str(tpl),
                        region=region,
                        confidence=confidence,
                        grayscale=grayscale,
                        move_duration=click_move_duration,
                    )
            break
    if not ui_match:
        print("[match] 未识别到右下角UI，请调整窗口后重试")
        success = False
    results["ui"] = ui_match

    # 必需模板（顶部与底部菜单）
    for stem in ["a_1", "a_2"]:
        m, used_scale = match_with_scales(
            assets_a, stem, recommended, confidence, grayscale, region
        )
        key = stem
        if m:
            results[key] = m
            if used_scale is not None:
                recommended = used_scale
                state["recommended_scale"] = used_scale
                state.setdefault("per_template", {})[stem] = used_scale
            if click:
                tpl = find_template_path(assets_a, stem, used_scale or recommended)
                if tpl:
                    click_template(
                        template_path=str(tpl),
                        region=region,
                        confidence=confidence,
                        grayscale=grayscale,
                        move_duration=click_move_duration,
                    )
        else:
            print(f"[match] 未识别到 {key}，请调整窗口后重试")
            results[key] = None
            success = False

    # 边界与状态持久化：成功则清零失败次数，失败则指数退避计数 +1
    if success:
        state["fail_count"] = 0
        state["recommended_scale"] = recommended
        save_scale_state(state)
    else:
        state["fail_count"] = int(state.get("fail_count", 0)) + 1
        save_scale_state(state)
        # 指数退避提示（不硬性等待，交互式流程下仅提示）
        base_wait = 0.5
        wait_sec = min(5.0, base_wait * (2 ** (state["fail_count"] - 1)))
        print(f"[backoff] 连续失败 {state['fail_count']} 次，建议等待 {wait_sec:.1f}s 后重试")

    return {"success": success, "matches": results, "recommended_scale": recommended}

