#                    _ooOoo_
#                   o8888888o
#                   88" . "88
#                   (| -_- |)
#                   O\  =  /O
#                ____/`---'\____
#              .'  \\|     |//  `.
#             /  \\|||  :  |||//  \
#            /  _||||| -:- |||||-  \
#            |   | \\\  -  /// |   |
#            | \_|  ''\---/''  |   |
#            \  .-\__  `-`  ___/-. /
#          ___`. .'  /--.--\  `. . __
#       ."" '<  `.___\_<|>_/___.'  >'"".
#      | | :  `- \`.;`\ _ /`;.`/ - ` : | |
#      \  \ `-.   \_ __\ /__ _/   .-` /  /
# ======`-.____`-.___\_____/___.-`____.-'======
#                    `=---='
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#             佛祖保佑       永无BUG

from __future__ import annotations

import sys
import time
from pathlib import Path
from .window import (
    detect_window_assets_a,
    compute_window_size_and_visualize,
)
from .auto_arena import run_auto_arena

USER_INFO = """
=== === === === === === === === === === === === === === === === === === === === === === === === ===
= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
===================================================================================================
作者: Petrichor

联系方式
- QQ : 1841770898
- 邮箱 : u_petrichor@163.com
- Bilibili : https://space.bilibili.com/442831003?spm_id_from=333.1007.0.0
- Github : https://github.com/U-Petrichor

说明: 
1. 目前这个只是雏形，也是我自己边学边做，可以看到交互方式还是有点简陋，不人性化，这也是个人水平不够导致的
2. 最新的进度会优先在博客与Github上更新，如果有看Q群也会跟大家分享最新的进度
3. 如果你觉得有用，希望可以多多支持，比如Github点下star，博客留言，社交媒体点点关注这种TAT，这对我真的很重要
4. 有Bug或者建议请联系我！！！
===================================================================================================
= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
=== === === === === === === === === === === === === === === === === === === === === === === === ===
"""


def print_user_info() -> None:
    print(USER_INFO.strip())


def main(argv: list[str] | None = None) -> None:
    # 这里打算后面加个人的信息和LOGO，但是目前最重要的是实现功能
    print_user_info()

    # 主函数判断逻辑（预留，当前为空）
    # TODO: 在此添加入口参数判断或前置校验

    # 等待用户输入后再开始检测窗口
    # 这里其实应该做进一步修改，如果想要实现完全的自动化，需要检测多个窗口
    print("脚本启动成功，欢迎使用 Petrichor 的工具，喜欢的话还请多多支持")
    print("请输入指令：start 启动自动竞技场，detect 检测窗口，exit 退出程序\n")
    try:
        while True:
            cmd = input("> ").strip().lower()
            # 这个我打算作为挂机模式，后面再精修
            if cmd == "start":
                run_auto_arena()
            elif cmd == "detect":
                result = detect_window_assets_a(
                    confidence=0.7,
                    grayscale=True,
                    region=None,
                )
                rec = result.get("recommended_scale", None)
                if result.get("success"):
                    print("[detect] 窗口匹配完成")
                    if rec is not None:
                        print(f"[scale] 推荐比例已更新为 {rec}%")
                    rect = compute_window_size_and_visualize(result.get("matches", {}), rec)
                    if rect is None:
                        print("[size] 窗口位置计算失败")
                else:
                    print("[detect] 窗口匹配未完成")
                    if rec is not None:
                        print(f"[scale] 当前推荐比例为 {rec}%（匹配失败）")
            elif cmd in ("exit", "quit", "q"):
                print("[main] 用户终止，退出。")
                break
            elif cmd == "":
                continue
            else:
                print("未知指令，请输入 start 或 exit")
    except KeyboardInterrupt:
        print("\n[main] 用户终止，退出。")


if __name__ == "__main__":
    main()