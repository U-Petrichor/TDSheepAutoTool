from __future__ import annotations

"""
    page_manager.py
    - 功能：管理游戏页面状态，包含页面检测与跳转逻辑
"""

from typing import Optional, Tuple, List
import time
from pathlib import Path

# 导入 match 中的工具
from .match import (
    check_image_exists,
    get_assets_dir,
    load_scale_state,
    ordered_scales,
    find_template_path
)

# 页面常量定义
PAGE_HOME = 0
PAGE_FRONTLINE = 1
PAGE_DEFENSE_LINE = 2
PAGE_WOLF_PACK = 3


def _check_image_with_scaling(
    folder_name: str, 
    stem: str, 
    confidence: float = 0.7, 
    grayscale: bool = True,
    region: Optional[Tuple[int, int, int, int]] = None
) -> bool:
    """
    检查指定图片是否存在，自动处理多比例缩放。
    优先使用当前记录的推荐比例，若不匹配则遍历所有支持的比例。
    """
    assets_dir = get_assets_dir() / folder_name
    if not assets_dir.exists():
        print(f"[page] 资源目录不存在: {assets_dir}")
        return False
        
    state = load_scale_state()
    recommended_scale = state.get("recommended_scale", 100)
    
    # 按优先级顺序遍历比例
    for s in ordered_scales(recommended_scale):
        tpl_path = find_template_path(assets_dir, stem, s)
        if not tpl_path:
            continue
            
        if check_image_exists(
            image=str(tpl_path),
            confidence=confidence,
            grayscale=grayscale,
            region=region
        ):
            # 找到匹配
            if s != recommended_scale:
                # 仅打印调试信息，暂不自动更新全局状态，以免频繁写入
                print(f"[page] 提示: 图片 {stem} 在 {s}% 比例下匹配成功 (当前推荐: {recommended_scale}%)")
            return True
            
    return False


def _check_page_home() -> bool:
    """检测是否在 PAGE_HOME"""
    # 假设需要匹配该文件夹下所有标号图片
    # page_home: 1.png, 2.png
    stems = ["1", "2"]
    for stem in stems:
        if not _check_image_with_scaling("page_home", stem):
            return False
    return True


def _check_page_frontline() -> bool:
    """检测是否在 PAGE_FRONTLINE"""
    # page_frontline: 1.png ~ 6.png
    stems = [str(i) for i in range(1, 7)]
    for stem in stems:
        if not _check_image_with_scaling("page_frontline", stem):
            return False
    return True


def _check_page_defenseline() -> bool:
    """检测是否在 PAGE_DEFENSE_LINE"""
    # page_defenseline: 1.png
    stems = ["1"]
    for stem in stems:
        if not _check_image_with_scaling("page_defenseline", stem):
            return False
    return True


def _check_page_wolfpack() -> bool:
    """检测是否在 PAGE_WOLF_PACK"""
    # page_wolfpack: 1.png ~ 3.png
    stems = ["1", "2", "3"]
    for stem in stems:
        if not _check_image_with_scaling("page_wolfpack", stem):
            return False
    return True


def is_target_page(page_id: int) -> bool:
    """
    判断当前是否为目标页面。
    根据传入的 page_id 调用对应的检测子函数。
    """
    if page_id == PAGE_HOME:
        return _check_page_home()
    elif page_id == PAGE_FRONTLINE:
        return _check_page_frontline()
    elif page_id == PAGE_DEFENSE_LINE:
        return _check_page_defenseline()
    elif page_id == PAGE_WOLF_PACK:
        return _check_page_wolfpack()
    else:
        print(f"[page] 未知页面ID: {page_id}")
        return False


def ensure_page(
    target_page_id: int,
    max_retries: int = 3,
    retry_interval: float = 1.0
) -> bool:
    """
    确保当前在指定页面，如果不在则尝试跳转。
    """
    # 映射 ID 到名称以便日志显示
    page_names = {
        PAGE_HOME: "HOME",
        PAGE_FRONTLINE: "FRONTLINE",
        PAGE_DEFENSE_LINE: "DEFENSE_LINE",
        PAGE_WOLF_PACK: "WOLF_PACK"
    }
    page_name = page_names.get(target_page_id, f"UNKNOWN({target_page_id})")

    # 1. 检查当前是否已经在目标页面
    if is_target_page(target_page_id):
        print(f"[page] 当前已在 {page_name}")
        return True
        
    print(f"[page] 当前不在 {page_name}，尝试跳转...")
    
    # 2. 尝试跳转逻辑（模板，待实现）
    _jump_to_page(target_page_id)
    
    # 3. 刷新/等待后再次检查
    _refresh_page()
    
    for i in range(max_retries):
        time.sleep(retry_interval)
        if is_target_page(target_page_id):
            print(f"[page] 跳转成功，已到达 {page_name}")
            return True
        print(f"[page] 跳转检测失败，重试 {i+1}/{max_retries}...")
        
    print(f"[page] 无法到达 {page_name}")
    return False

# 内部辅助函数模板（待实现）
def _jump_to_page(page_id: int):
    """跳转到指定页面（待实现）"""
    pass

def _refresh_page():
    """刷新页面（待实现）"""
    pass
