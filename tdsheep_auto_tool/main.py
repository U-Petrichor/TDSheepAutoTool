from __future__ import annotations

import argparse
import sys
from typing import Tuple
from pathlib import Path

import cv2
import pyautogui

from tdsheep_auto_tool.runner import AutoRunner
from tdsheep_auto_tool.config import load_config, save_config, get_templates_dir, resolve_path
from tdsheep_auto_tool.vision import Screen, Region
from tdsheep_auto_tool.petrichor.petrichor import print_branding


def get_point(prompt: str) -> Tuple[int, int]:
    input(prompt + "\n  将鼠标移动到目标位置后按 Enter...")
    x, y = pyautogui.position()
    print(f"  记录坐标: ({x}, {y})")
    return int(x), int(y)


def get_region(prompt: str) -> Region:
    print(prompt)
    input("  将鼠标移动到区域左上角后按 Enter...")
    x1, y1 = pyautogui.position()
    input("  将鼠标移动到区域右下角后按 Enter...")
    x2, y2 = pyautogui.position()
    left, top = min(x1, x2), min(y1, y2)
    width, height = abs(x2 - x1), abs(y2 - y1)
    print(f"  记录区域: left={left}, top={top}, width={width}, height={height}")
    return Region(left=int(left), top=int(top), width=int(width), height=int(height))


def _path_ok(p: str | None) -> bool:
    if not p:
        return False
    try:
        path = resolve_path(p)
        return Path(path).exists()
    except Exception:
        return False


def preflight_check(verbose: bool = True) -> bool:
    """检查配置是否满足运行的最低要求。
    要求：
    - next_wave: 需要坐标或模板路径（二选一，至少其一存在）
    - upgrade: 建议提供坐标或模板路径（缺失不阻止运行）
    - 所有已设置的 template_path 均应存在
    返回 True 表示可运行；False 表示缺失关键项。
    """
    cfg = load_config()
    msgs: list[str] = []
    critical = False

    # next_wave 要求至少有坐标或模板
    nw = cfg.get("next_wave", {})
    nw_ok = (isinstance(nw.get("position"), list) and len(nw.get("position") or []) >= 2) or _path_ok(nw.get("template_path"))
    if not nw_ok:
        critical = True
        msgs.append("[preflight] 缺少 next_wave: 需要坐标或模板路径（二选一）")

    # upgrade 建议提供（不阻断）
    up = cfg.get("upgrade", {})
    up_ok = (isinstance(up.get("positions"), list) and len(up.get("positions") or []) >= 1) or _path_ok(up.get("template_path"))
    if not up_ok:
        msgs.append("[preflight] 建议配置 upgrade: 提供坐标或模板路径（非必需）")

    # 任意设置了 template_path 的项必须存在
    for section in ("next_wave", "upgrade", "breach"):
        tp = cfg.get(section, {}).get("template_path")
        if tp and not _path_ok(tp):
            critical = True
            msgs.append(f"[preflight] 模板文件不存在: {section}.template_path = {tp}")

    ok = not critical
    if verbose:
        if ok:
            print("[preflight] 配置检查通过。")
        else:
            for m in msgs:
                print(m)
            print("[preflight] 检查未通过，需先校准或补齐模板。")
    return ok


def cmd_run(_: argparse.Namespace) -> None:
    if not preflight_check():
        print("[run] 预检失败，进入交互式校准（按 Ctrl+C 可中断）...")
        try:
            cmd_calibrate(argparse.Namespace())
        except KeyboardInterrupt:
            print("\n[run] 校准被中断，退出运行。")
            return
        if not preflight_check():
            print("[run] 校准后仍未通过预检，请检查模板路径或重新校准。")
            return
    AutoRunner().run()


def cmd_calibrate(_: argparse.Namespace) -> None:
    cfg = load_config()
    print("[calibrate] 开始校准：next_wave坐标与升级点击坐标")

    # next_wave position
    nx, ny = get_point("[next_wave] 采集下一波按钮坐标")
    cfg.setdefault("next_wave", {})["position"] = [nx, ny]

    # upgrade positions
    print("[upgrade] 采集升级点击坐标，可采集多个，输入 q 结束")
    up_positions = []
    while True:
        s = input("  输入 Enter 采集一个坐标，或输入 q 结束: ")
        if s.strip().lower() == "q":
            break
        x, y = pyautogui.position()
        print(f"  记录坐标: ({x}, {y})")
        up_positions.append([int(x), int(y)])
    cfg.setdefault("upgrade", {})["positions"] = up_positions

    save_config(cfg)
    print("[calibrate] 完成，已写入 config.json。")


def cmd_capture_template(ns: argparse.Namespace) -> None:
    name = ns.name
    if not name:
        print("[capture-template] 需要 --name 指定模板名称，如 next_wave")
        return
    templates_dir = get_templates_dir()
    region = get_region("[template] 采集模板区域")
    screen = Screen()
    img = screen.grab(region)
    out_path = templates_dir / f"{name}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(out_path), img)
    if ok:
        print(f"[capture-template] 已保存模板到: {out_path}")
    else:
        print("[capture-template] 保存失败")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="TD Sheep Auto Tool - 自动塔防脚本框架")
    sub = p.add_subparsers(dest="cmd")

    r = sub.add_parser("run", help="运行自动脚本")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("calibrate", help="交互式校准点击坐标")
    c.set_defaults(func=cmd_calibrate)

    t = sub.add_parser("capture-template", help="采集屏幕区域保存为模板PNG")
    t.add_argument("--name", required=True, help="模板名称，如 next_wave 或 game_over")
    t.set_defaults(func=cmd_capture_template)

    return p


def main(argv: list[str] | None = None) -> None:
    print_branding()  # 打印品牌与横幅
    argv = argv if argv is not None else sys.argv[1:]
    # 确保任意启动都初始化配置与目录（会在缺失时生成 config.json）
    try:
        _ = load_config()
        print("[init] 已初始化配置与目录。")
    except Exception as e:
        print(f"[init] 初始化配置失败: {e}")
    parser = build_parser()
    ns = parser.parse_args(argv)

    # 未指定子命令：执行预检 -> 必要时自动校准 -> 死循环运行
    if not hasattr(ns, "func"):
        print("[runner] 未指定子命令，进入自动运行模式。")
        if not preflight_check():
            print("[preflight] 配置不完整，自动进入校准（按 Ctrl+C 可中断）...")
            try:
                cmd_calibrate(argparse.Namespace())
            except KeyboardInterrupt:
                print("\n[runner] 校准被中断，退出运行。")
                return
            if not preflight_check():
                print("[runner] 校准后仍未通过预检，请检查模板路径或重新校准。")
                return
        print("[runner] 进入自动运行（按 Ctrl+C 停止）...")
        AutoRunner().run()
        return

    # 指定子命令时，保持原有行为
    ns.func(ns)


if __name__ == "__main__":
    main()