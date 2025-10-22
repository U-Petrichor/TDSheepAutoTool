from __future__ import annotations

"""
    match.py
    - 功能：负责读取用户配置的规则然后执行匹配
    - 配置信息地址：tdsheep_auto_tool/data/match.json
"""

from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import json
import time
import pyautogui

from .calc_locate import locate_on_screen, click_template

# 功能：获取 assets 目录路径
def get_assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"

# 新增：比例列表与持久化状态路径
SCALES: List[int] = [50, 67, 75, 80, 90, 100, 110, 125]
SCALE_STATE_PATH: Path = Path(__file__).resolve().parent.parent / "data" / "scale_state.json"

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


def _clamp_scale(scale: int) -> int:
    if scale in SCALES:
        return scale
    return min(SCALES, key=lambda s: abs(s - scale))


def compute_window_geometry(matches: Dict[str, Any], recommended_scale: Optional[int]) -> Optional[Dict[str, int]]:
    """根据锚点与比例计算游戏窗口的屏幕坐标与尺寸。"""
    cfg = _load_window_config()
    anchor_stem = cfg["anchor"]
    off_x, off_y = cfg["anchor_offset"]
    base_w, base_h = cfg["base_size"]

    rec = _clamp_scale(int(recommended_scale or 100))
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


def _clamp_scale(scale: int) -> int:
    """将比例限制在合法集合内。"""
    if scale in SCALES:
        return scale
    # 就近取值
    return min(SCALES, key=lambda s: abs(s - scale))


def _load_scale_state() -> Dict[str, Any]:
    """读取比例状态，若不存在则返回默认。"""
    try:
        if SCALE_STATE_PATH.exists():
            with SCALE_STATE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # 基本纠偏
                data["recommended_scale"] = _clamp_scale(int(data.get("recommended_scale", 100)))
                data["fail_count"] = int(data.get("fail_count", 0))
                data.setdefault("per_template", {})
                return data
    except Exception:
        pass
    return {"recommended_scale": 100, "fail_count": 0, "per_template": {}}


def _save_scale_state(state: Dict[str, Any]) -> None:
    """写入比例状态。"""
    SCALE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with SCALE_STATE_PATH.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[scale] 状态保存失败: {e}")


def _ordered_scales(preferred: int) -> List[int]:
    """根据用户要求的遍历顺序，优先尝试当前推荐比例。"""
    base_order = [50, 67, 75, 80, 90, 100, 110, 125]
    preferred = _clamp_scale(preferred)
    # 首次尝试推荐比例，其次按固定顺序遍历（避免重复）
    seen = set()
    order: List[int] = []
    for s in [preferred] + base_order:
        if s not in seen:
            seen.add(s)
            order.append(s)
    return order


def _find_template_path(assets_a: Path, stem: str, scale: int) -> Optional[Path]:
    """返回给定比例的模板路径，100% 允许回退至 stem.png。"""
    # 优先带比例后缀
    p = assets_a / f"{stem}_{scale}.png"
    if p.exists():
        return p
    # 回退：100%时尝试无后缀文件（兼容历史）
    if scale == 100:
        p2 = assets_a / f"{stem}.png"
        if p2.exists():
            return p2
    return None


def _match_with_scales(
    assets_a: Path,
    stem: str,
    recommended_scale: int,
    confidence: float,
    grayscale: bool,
    region: Optional[Tuple[int, int, int, int]],
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    """按动态比例尝试匹配，成功则短路返回 (match, used_scale)。"""
    for s in _ordered_scales(recommended_scale):
        tpl = _find_template_path(assets_a, stem, s)
        if not tpl:
            continue
        m = locate_on_screen(
            template_path=str(tpl),
            region=region,
            confidence=confidence,
            grayscale=grayscale,
        )
        if m:
            print(f"[match] {tpl.name} 命中 (scale={s}, score={m['score']:.3f})")
            return m, s
    print(f"[match] {stem} 所有比例未命中")
    return None, None


# 功能：获取 assets 目录路径

def get_assets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"


# 功能：加载匹配配置（tdsheep_auto_tool/data/match.json）
def load_match_config() -> Optional[Dict[str, Any]]:
    cfg_path = get_assets_dir() / "match.json"
    if not cfg_path.exists():
        print(f"[config] 未找到配置文件: {cfg_path}")
        return None
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[config] 读取配置失败: {e}")
        return None


# 功能：执行一次匹配与点击；打印日志，未命中或文件不存在直接返回 False

def match_once(
    image: str,
    confidence: float = 0.7,
    grayscale: bool = True,
    region: Optional[Tuple[int, int, int, int]] = None,
    click_move_duration: float = 0.05,
    pause_after_detect_sec: float = 2.0,
) -> bool:
    img_path = Path(image)
    if not img_path.exists():
        print(f"[detect] 模板文件不存在: {img_path}")
        return False

    match = locate_on_screen(
        template_path=str(img_path),
        region=region,
        confidence=confidence,
        grayscale=grayscale,
    )
    name = img_path.name
    if match:
        center = match["center"]
        score = match["score"]
        print(f"[detect] 找到 {name}: center={center}, score={score:.3f}")
        # 部分服务器或画面卡顿时，点击前停顿
        time.sleep(max(0.0, pause_after_detect_sec))
        clicked = click_template(
            template_path=str(img_path),
            region=region,
            confidence=confidence,
            grayscale=grayscale,
            move_duration=click_move_duration,
        )
        if clicked:
            print(f"[click] 已点击 {name} 中心")
        return bool(clicked)
    else:
        print(f"[detect] 未找到 {name}")
        return False


# 功能：基于配置执行一次匹配（无兜底；配置缺失或错误即返回 False）

def match_once_from_config() -> bool:
    cfg = load_match_config()
    if cfg is None:
        return False

    img = str(cfg.get("image", "")).strip()
    if not img:
        print("[config] 配置缺少 'image' 字段")
        return False

    return match_once(
        image=img,
        confidence=float(cfg.get("confidence", 0.7)),
        grayscale=bool(cfg.get("grayscale", True)),
        region=cfg.get("region", None),
    )


def detect_window_assets_a(
    confidence: float = 0.7,
    grayscale: bool = True,
    region: Optional[Tuple[int, int, int, int]] = None,
    click: bool = False,
    click_move_duration: float = 0.05,
):
    # 目录修正：使用 assets/a
    assets_a = get_assets_dir() / 'a'

    # 加载比例状态
    state = _load_scale_state()
    recommended = int(state.get("recommended_scale", 100))
    recommended = _clamp_scale(recommended)

    results: Dict[str, Any] = {}
    success = True

    # 可替代的左下角切换好友（a_5 灰 或 a_6 亮）
    friend_match = None
    friend_scale_used = None
    for stem in ["a_5", "a_6"]:
        m, used_scale = _match_with_scales(
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
                tpl = _find_template_path(assets_a, stem, used_scale or recommended)
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
        m, used_scale = _match_with_scales(
            assets_a, stem, recommended, confidence, grayscale, region
        )
        if m:
            ui_match = {"name": stem, "data": m}
            if used_scale is not None:
                recommended = used_scale
                state["recommended_scale"] = used_scale
                state.setdefault("per_template", {})[stem] = used_scale
            if click:
                tpl = _find_template_path(assets_a, stem, used_scale or recommended)
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
        m, used_scale = _match_with_scales(
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
                tpl = _find_template_path(assets_a, stem, used_scale or recommended)
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
        _save_scale_state(state)
    else:
        state["fail_count"] = int(state.get("fail_count", 0)) + 1
        _save_scale_state(state)
        # 指数退避提示（不硬性等待，交互式流程下仅提示）
        base_wait = 0.5
        wait_sec = min(5.0, base_wait * (2 ** (state["fail_count"] - 1)))
        print(f"[backoff] 连续失败 {state['fail_count']} 次，建议等待 {wait_sec:.1f}s 后重试")

    return {"success": success, "matches": results, "recommended_scale": recommended}


# 计算窗口大小占位：匹配完成后调用，留待你实现

def compute_window_size_placeholder(matches: Dict[str, Any]) -> None:
    print("[size] 已完成窗口匹配，待计算窗口大小（占位）")


__all__ = [
    "get_assets_dir",
    "get_default_image",
    "load_match_config",
    "match_once",
    "match_once_from_config",
    "detect_window_assets_a",
    "compute_window_size_placeholder",
]