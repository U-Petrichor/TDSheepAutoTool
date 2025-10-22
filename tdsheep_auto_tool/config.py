from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# 兼容可执行文件（PyInstaller）与源码运行的路径策略：
# - 源码运行：使用项目根目录
# - EXE 运行：使用可执行文件所在目录（与 EXE 同级），保证可读写

def _detect_base_dir() -> Path:
    if getattr(sys, "frozen", False):  # 被打包为 EXE
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = _detect_base_dir()
CONFIG_PATH = BASE_DIR / "config.json"
# 为了与文档一致，模板目录保持在 BASE_DIR/tdsheep_auto_tool/templates
TEMPLATES_DIR = BASE_DIR / "tdsheep_auto_tool" / "templates"
DEBUG_DIR = BASE_DIR / "debug"

DEFAULT_CONFIG: Dict[str, Any] = {
    "loop_interval_secs": 1.5,
    "screen_scale": 1.0,
    "upgrade": {
        "positions": [],  # 例如 [[x, y], [x, y], ...]
        "template_path": None,  # 例如 "tdsheep_auto_tool/templates/upgrade_icon.png"
        "region": None,  # 例如 {"left": 1600, "top": 900, "width": 300, "height": 150}
        "threshold": 0.85,
        "max_clicks_per_loop": 3
    },
    "next_wave": {
        "position": None,  # 例如 [x, y]
        "template_path": None,
        "region": None,
        "threshold": 0.85,
        "cooldown_secs": 3.0
    },
    "breach": {
        "template_path": None,  # 例如 "tdsheep_auto_tool/templates/game_over.png"
        "region": None,
        "threshold": 0.88,
        "check_interval_secs": 1.0
    },
    "restart": {
        "close_hotkey": ["alt", "f4"],
        "start_command": "",  # 可填写启动游戏的命令或脚本路径
        "post_wait_secs": 5.0,
        "menu_hotkeys": []
    },
    "diagnostics": {
        "save_debug_images": False,
        "debug_dir": str(DEBUG_DIR)
    }
}


def ensure_dirs() -> None:
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    ensure_dirs()
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(cfg: Dict[str, Any]) -> None:
    ensure_dirs()
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def resolve_path(p: Optional[str]) -> Optional[Path]:
    if not p:
        return None
    path = Path(p)
    if path.is_absolute():
        return path
    # 相对路径基于运行根目录（源码：项目根；EXE：与可执行同级）
    return (BASE_DIR / path).resolve()


def get_templates_dir() -> Path:
    return TEMPLATES_DIR