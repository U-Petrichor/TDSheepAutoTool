from __future__ import annotations

f"""
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
    find_template_path,
    click_template
)

# 页面常量定义
PAGE_HOME = 0
PAGE_FRONTLINE = 1
PAGE_DEFENSE_LINE = 2
PAGE_WOLF_PACK = 3


def _find_and_click_with_scaling(
    folder_name: str,
    stem: str,
    confidence: float = 0.7,
    grayscale: bool = True
) -> bool:
    """
    查找并点击图片（支持多比例缩放）。
    """
    assets_dir = get_assets_dir() / folder_name
    if not assets_dir.exists():
        print(f"[page] 资源目录不存在: {assets_dir}")
        return False

    state = load_scale_state()
    recommended_scale = state.get("recommended_scale", 100)

    for s in ordered_scales(recommended_scale):
        tpl_path = find_template_path(assets_dir, stem, s)
        if not tpl_path:
            continue
        
        # 尝试点击
        clicked = click_template(
            template_path=str(tpl_path),
            confidence=confidence,
            grayscale=grayscale
        )
        if clicked:
            print(f"[page] 点击成功: {stem} (scale={s}%)")
            return True
            
    return False


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
    如果不是目标页面，会自动尝试刷新并跳转，然后返回 False。
    """
    is_match = False
    if page_id == PAGE_HOME:
        is_match = _check_page_home()
    elif page_id == PAGE_FRONTLINE:
        is_match = _check_page_frontline()
    elif page_id == PAGE_DEFENSE_LINE:
        is_match = _check_page_defenseline()
    elif page_id == PAGE_WOLF_PACK:
        is_match = _check_page_wolfpack()
    else:
        print(f"[page] 未知页面ID: {page_id}")
        return False
        
    if is_match:
        return True
        
    # 如果不匹配，执行刷新和跳转逻辑
    print(f"[page] 页面检测不匹配 (ID={page_id})，开始刷新并跳转...")
    _refresh_page()
    # 刷新后默认回到 PAGE_HOME，所以尝试从 HOME 跳转到目标页面
    return _jump_to_page(PAGE_HOME, page_id)


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
    # 注意：is_target_page 现在包含了自动刷新和跳转尝试
    if is_target_page(target_page_id):
        print(f"[page] 当前已在 {page_name}")
        return True
        
    # 如果 is_target_page 返回 False，说明第一次检测失败，并且已经尝试了一次刷新和跳转
    # 我们进入重试循环
    
    for i in range(max_retries):
        print(f"[page] 页面校验重试 {i+1}/{max_retries}...")
        time.sleep(retry_interval)
        
        # 再次调用 is_target_page
        # 如果还是不匹配，它会再次尝试刷新和跳转
        if is_target_page(target_page_id):
            print(f"[page] 跳转成功，已到达 {page_name}")
            return True
        
    print(f"[page] 无法到达 {page_name}")
    return False

# 内部辅助函数
def _jump_to_page(cur_page_id: int, target_page_id: int) -> bool:
    """
    跳转到指定页面。
    根据当前页面和目标页面，执行对应的点击操作。
    返回 bool 表示是否执行了跳转操作（或无需跳转）且未报错。
    """
    if cur_page_id == target_page_id:
        print(f"[jump] 起点与终点相同 ({cur_page_id})，无需跳转")
        return True

    print(f"[jump] 尝试跳转: {cur_page_id} -> {target_page_id}")

    # 逻辑：从 HOME (0) -> FRONTLINE (1)
    if cur_page_id == PAGE_HOME and target_page_id == PAGE_FRONTLINE:
        print("[jump] 执行 HOME -> FRONTLINE 跳转...")
        if _find_and_click_with_scaling("a", "home_to_frontline"):
            print("[jump] 点击 home_to_frontline 成功，等待页面加载...")
            time.sleep(2)  # 等待跳转动画
            return True
        else:
            print("[jump] 未找到 home_to_frontline 按钮")
            return False
    
    # 后续可以添加更多跳转逻辑
    # elif cur_page_id == PAGE_HOME and target_page_id == PAGE_DEFENSE_LINE:
    #     ...
    
    else:
        print(f"[jump] 尚未实现从 {cur_page_id} 到 {target_page_id} 的跳转路径")
        return False

def _refresh_page():
    """刷新页面：点击 page_refresh 并等待 10 秒"""
    print("[page] 正在刷新页面...")
    # 查找并点击 page_refresh (位于 assets/a 目录)
    if _find_and_click_with_scaling("a", "page_refresh"):
        print("[page] 刷新按钮点击成功，等待 10 秒...")
        time.sleep(10)
    else:
        print("[page] 未找到刷新按钮 (page_refresh)")
