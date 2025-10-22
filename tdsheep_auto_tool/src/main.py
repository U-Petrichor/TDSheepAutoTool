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
from .match import (
    detect_window_assets_a,
    compute_window_size_placeholder,
)

USER_INFO = """
=== 用户信息 ===
作者: Petrichor
联系: A / B / C
说明: 这是最简主框架，后续逐步加功能
"""


def print_user_info() -> None:
    print(USER_INFO.strip())


def main(argv: list[str] | None = None) -> None:
    # 这里打算后面加个人的信息和LOGO，但是目前最重要的是实现功能
    print_user_info()

    # 主函数判断逻辑（预留，当前为空）
    # TODO: 在此添加入口参数判断或前置校验

    # 等待用户输入后再开始检测窗口
    print("脚本启动成功，欢迎使用 Petrichor 的工具，喜欢的话还请多多支持")
    print("请输入指令：start 开始检测窗口，exit 退出程序\n")
    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == "start":
                result = detect_window_assets_a(
                    confidence=0.7,
                    grayscale=True,
                    region=None,
                )
                if result.get("success"):
                    print("[detect] 窗口匹配完成")
                    rec = result.get("recommended_scale", None)
                    if rec is not None:
                        print(f"[scale] 推荐比例已更新为 {rec}%")
                    compute_window_size_placeholder(result.get("matches", {}))
                else:
                    print("[detect] 窗口匹配未完成")
                    rec = result.get("recommended_scale", None)
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