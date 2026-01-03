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
import sys

from .calc_locate import locate_on_screen, click_template

# 功能：获取 assets 目录路径
def get_base_dir() -> Path:
    """获取基础路径，兼容 PyInstaller 打包环境。"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return Path(sys._MEIPASS)
    # 开发环境：src 的父目录的父目录 (即项目根目录 tdsheep_auto_tool)
    return Path(__file__).resolve().parent.parent

def get_assets_dir() -> Path:
    return get_base_dir() / "assets"

# 新增：比例列表与持久化状态路径
SCALES: List[int] = [50, 67, 75, 80, 90, 100, 110, 125]

def get_scale_state_path() -> Path:
    """获取状态文件路径。在打包模式下，建议放在用户目录下，这里暂存原位或同级data目录。"""
    # 注意：如果是单文件打包，_MEIPASS 是只读的。状态文件不能写在 _MEIPASS 下。
    # 这里我们区分对待：读取资源用 _MEIPASS，写入状态用 executable 所在目录或用户目录。
    # 简单起见，写入状态文件到当前工作目录或 sys.executable 旁边的 data 目录。
    
    if hasattr(sys, '_MEIPASS'):
        # 运行时，使用 exe 所在目录下的 data 文件夹
        return Path(sys.executable).parent / "data" / "scale_state.json"
    
    return get_base_dir() / "data" / "scale_state.json"

SCALE_STATE_PATH: Path = get_scale_state_path()

# 基础窗口尺寸（100% 缩放时）
BASE_WINDOW_SIZE: Tuple[int, int] = (1066, 912)
ANCHOR_TOP_MENU_OFFSET_X_BASE: int = 1  # 100% 缩放时需向右偏移 1px
ANCHOR_TOP_MENU_OFFSET_Y_BASE: int = 42  # 100% 缩放时需向下偏移 42px

def clamp_scale(scale: int) -> int:
    """将比例限制在合法集合内。"""
    if scale in SCALES:
        return scale
    # 就近取值
    return min(SCALES, key=lambda s: abs(s - scale))


def load_scale_state() -> Dict[str, Any]:
    """读取比例状态，若不存在则返回默认。"""
    # 动态获取路径，确保打包后也能正确定位
    state_path = get_scale_state_path()
    try:
        if state_path.exists():
            with state_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # 基本纠偏
                data["recommended_scale"] = clamp_scale(int(data.get("recommended_scale", 100)))
                data["fail_count"] = int(data.get("fail_count", 0))
                data.setdefault("per_template", {})
                return data
    except Exception:
        pass
    return {"recommended_scale": 100, "fail_count": 0, "per_template": {}}


def save_scale_state(state: Dict[str, Any]) -> None:
    """写入比例状态。"""
    state_path = get_scale_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[scale] 状态保存失败: {e}")


def ordered_scales(preferred: int) -> List[int]:
    """根据用户要求的遍历顺序，优先尝试当前推荐比例。"""
    base_order = [50, 67, 75, 80, 90, 100, 110, 125]
    preferred = clamp_scale(preferred)
    # 首次尝试推荐比例，其次按固定顺序遍历（避免重复）
    seen = set()
    order: List[int] = []
    for s in [preferred] + base_order:
        if s not in seen:
            seen.add(s)
            order.append(s)
    return order


def find_template_path(assets_a: Path, stem: str, scale: int) -> Optional[Path]:
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


def match_with_scales(
    assets_a: Path,
    stem: str,
    recommended_scale: int,
    confidence: float,
    grayscale: bool,
    region: Optional[Tuple[int, int, int, int]],
) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    """按动态比例尝试匹配，成功则短路返回 (match, used_scale)。"""
    for s in ordered_scales(recommended_scale):
        tpl = find_template_path(assets_a, stem, s)
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


def check_image_exists(
    image: str,
    confidence: float = 0.7,
    grayscale: bool = True,
    region: Optional[Tuple[int, int, int, int]] = None,
) -> bool:
    """检查图片是否存在于当前屏幕（不点击）。"""
    img_path = Path(image)
    if not img_path.exists():
        return False
        
    match = locate_on_screen(
        template_path=str(img_path),
        region=region,
        confidence=confidence,
        grayscale=grayscale,
    )
    return bool(match)


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



__all__ = [
    "get_assets_dir",
    "load_match_config",
    "check_image_exists",
    "match_once",
    "match_once_from_config",
    "SCALES",
    "load_scale_state",
    "save_scale_state",
    "ordered_scales",
    "find_template_path",
    "clamp_scale",
    "match_with_scales",
    "click_template",
]