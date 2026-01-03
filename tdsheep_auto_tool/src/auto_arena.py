from __future__ import annotations

"""
    auto_arena.py
    - 功能：自动竞技场脚本
    - 逻辑：
        1. 检查是否在 HOME 页
        2. 点击 1_1 进入竞技场，检查 1_2 确认打开
        3. 循环：
            - 检查 2_1，不存在则结束
            - 点击 2_1，等待 3s
            - 检查 3_1 (确认跳转)
            - 等待 4_1 出现
            - 点击 4_1 右下偏移位置 (48, 164) 直到 4_2 出现
            - 点击 4_2
            - 回到循环开头
"""

import time
import pyautogui
from pathlib import Path
from typing import Optional, Tuple, Any

# 导入项目模块
from .page_manager import is_target_page, PAGE_HOME
from .match import (
    get_assets_dir,
    load_scale_state,
    match_with_scales,
    find_template_path,
    click_template,
    clamp_scale,
    ordered_scales,
    check_image_exists
)

# 常量定义
ASSETS_DIR_NAME = "auto_arena"

def _get_assets_path() -> Path:
    return get_assets_dir() / ASSETS_DIR_NAME

def _find_and_click(
    stem: str, 
    confidence: float = 0.7, 
    grayscale: bool = True,
    click_duration: float = 0.05
) -> bool:
    """
    查找并点击图片（支持自动缩放）。
    返回是否成功点击。
    """
    assets_dir = _get_assets_path()
    if not assets_dir.exists():
        print(f"[arena] 资源目录不存在: {assets_dir}")
        return False

    state = load_scale_state()
    recommended_scale = state.get("recommended_scale", 100)

    match_res, used_scale = match_with_scales(
        assets_a=assets_dir,
        stem=stem,
        recommended_scale=recommended_scale,
        confidence=confidence,
        grayscale=grayscale,
        region=None
    )

    if match_res and used_scale:
        tpl_path = find_template_path(assets_dir, stem, used_scale)
        if tpl_path:
            print(f"[arena] 点击 {stem} (scale={used_scale})")
            click_template(
                template_path=str(tpl_path),
                region=None,
                confidence=confidence,
                grayscale=grayscale,
                move_duration=click_duration
            )
            return True
            
    return False

def _check_exists(
    stem: str,
    confidence: float = 0.7,
    grayscale: bool = True
) -> Tuple[bool, Optional[Any], Optional[int]]:
    """
    检查图片是否存在（支持自动缩放）。
    返回: (exists, match_info, used_scale)
    """
    assets_dir = _get_assets_path()
    if not assets_dir.exists():
        return False, None, None

    state = load_scale_state()
    recommended_scale = state.get("recommended_scale", 100)

    match_res, used_scale = match_with_scales(
        assets_a=assets_dir,
        stem=stem,
        recommended_scale=recommended_scale,
        confidence=confidence,
        grayscale=grayscale,
        region=None
    )

    return (match_res is not None), match_res, used_scale

def run_auto_arena():
    print("[arena] 启动自动竞技场脚本...")

    # 1. 判断当前是否为 HOME 页
    if not is_target_page(PAGE_HOME):
        print("[arena] 当前不在主页 (HOME)，脚本停止")
        return

    # 2. 点击 1_1 (入口)，判断 1_2 (确认打开)
    print("[arena] 尝试进入竞技场 (点击 1_1)...")
    if not _find_and_click("1_1"):
        print("[arena] 未找到入口 1_1，脚本停止")
        return

    # 等待 1_2 出现
    print("[arena] 等待竞技场界面加载 (检测 1_2)...")
    max_retries = 10
    opened = False
    for _ in range(max_retries):
        exists, _, _ = _check_exists("1_2")
        if exists:
            opened = True
            break
        time.sleep(1)
    
    if not opened:
        print("[arena] 无法确认进入竞技场 (未找到 1_2)，脚本停止")
        return
    print("[arena] 成功进入竞技场")

    # 3. 循环逻辑
    round_count = 0
    while True:
        round_count += 1
        print(f"\n[arena] --- 第 {round_count} 轮循环 ---")

        # 检查 2_1 (对手)，如果不存在则结束
        # 2_1 有灰色(不可挑战)和橙色(可挑战)两种状态，需关闭灰度匹配以区分颜色
        exists_2_1, match_2_1, scale_2_1 = _check_exists("2_1", grayscale=False)
        if not exists_2_1:
            print("[arena] 无可进行对局，结束脚本")
            break
        
        # 点击 2_1
        print("[arena] 还有可进行对局，点击进入")
        # 这里需要点击，我们直接复用 _find_and_click 或者利用查找到的信息点击
        # 为了保险再次调用 _find_and_click (或者手动点击 match_2_1 的中心)
        # _find_and_click 内部会重新 match 一次，为了效率可以使用 match_2_1
        # 但 match_2_1 是字典信息，我们需要 center
        if match_2_1:
            center = match_2_1["center"]
            pyautogui.click(center[0], center[1])
            print(f"[arena] 已点击坐标 {center}")
        
        # 等待 3 秒
        print("[arena] 等待 3 秒...")
        time.sleep(3)

        # 4. 判断 3_1 (是否跳转成功/在战斗中)
        # 优先判断是不是3_1，不是的话 判断是不是3_2
        # 如果是3_2那就点击3_2，等三秒，找3_3然后点击，等3秒，找3_1然后点击
        print("[arena] 检测当前是什么战斗 (3_1 或 3_2)...")
        exists_3_1, _, _ = _check_exists("3_1")
        if exists_3_1:
            print("[arena] 确认为防守")
            if _find_and_click("3_1"):
                print("[arena] 点击‘开始战斗’")
        else:
            print("[arena] 确认为进攻")
            exists_3_2, _, _ = _check_exists("3_2")
            if exists_3_2:
                print("[arena] 寻找‘挑战’")
                if _find_and_click("3_2"):
                    print("[arena] 点击‘挑战’，等待3秒加载窗口")
                    time.sleep(3)
                    
                    # 找 3_3 并点击
                    print("[arena] 寻找‘自动排列’")
                    if _find_and_click("3_3"):
                        print("[arena] 点击‘自动排列’")
                        time.sleep(3)
                        
                        # 找 3_1 并点击
                        print("[arena] 寻找‘开始战斗’")
                        if _find_and_click("3_1"):
                            print("[arena] 点击‘开始战斗’")
                        else:
                            print("[arena] 警告: 点击‘开始战斗’失败")
                    else:
                        print("[arena] 警告: 未找到‘自动排列’")
                else:
                    print("[arena] 警告: 点击‘挑战’")
            else:
                print("[arena] 警告: 出现了意料之外的错误，auto_arena.py——204")

        # 5. 结算流程：等待 4_1
        print("[arena] 等待结算")
        pyautogui.moveTo(20, 20)  # 移动鼠标到左上角，防止遮挡 (避免 (0,0) 触发 FailSafe)
        while True:
            exists_4_1, match_4_1, scale_4_1 = _check_exists("4_1")
            if exists_4_1:
                break
            time.sleep(3)
        
        print("[arena] 结算界面已出现")
        
        # 计算 4_1 右 48, 下 164 的位置 (需根据 scale 缩放偏移量)
        # 假设 48, 164 是基于 100% 缩放的数值
        if match_4_1 and scale_4_1:
            center_4_1 = match_4_1["center"]
            # 注意：locate_on_screen 返回的 center 是屏幕绝对坐标
            # 偏移量需要根据当前缩放比例调整
            scale_factor = scale_4_1 / 100.0
            offset_x = int(48 * scale_factor)
            offset_y = int(164 * scale_factor)
            
            target_x = center_4_1[0] + offset_x
            target_y = center_4_1[1] + offset_y
            
            print(f"[arena] 模拟点击位置: ({target_x}, {target_y}) (基准偏移 48,164 -> 缩放后 {offset_x},{offset_y})")

            # 模拟点击直到 4_2 出现
            print("[arena] 连续点击直到抽奖完成")
            while True:
                exists_4_2, _, _ = _check_exists("4_2")
                if exists_4_2:
                    print("[arena] 4_2 已出现，等待 3 秒待文字消失...")
                    time.sleep(3)
                    break
                pyautogui.click(target_x, target_y)
                time.sleep(0.5) # 点击频率
            
            print("[arena] 准备点击退出结算")
            
            # 点击 4_2 正中央
            if _find_and_click("4_2"):
                print("[arena] 点击完成")
            else:
                print("[arena] 警告: 点击失败")
        
        # 循环回到步骤 3，继续检查 2_1
        print("[arena] 本轮结束，等待 3 秒加载页面...")
        time.sleep(3)

    print("[arena] 自动竞技场脚本执行完毕")

if __name__ == "__main__":
    # 测试运行
    try:
        run_auto_arena()
    except KeyboardInterrupt:
        print("\n[arena] 用户终止")
