from __future__ import annotations

import time
import subprocess
from typing import Any, Dict, Optional, List, Tuple

from .config import load_config, resolve_path
from .vision import Screen, Region, find_one
from .actions import click, click_center, hotkey, sleep


def _region_from_dict(d: Optional[Dict[str, int]]) -> Optional[Region]:
    if not d:
        return None
    return Region(left=int(d["left"]), top=int(d["top"]), width=int(d["width"]), height=int(d["height"]))


class AutoRunner:
    def __init__(self) -> None:
        self.cfg: Dict[str, Any] = load_config()
        self.screen = Screen()
        self.last_wave_ts: float = 0.0
        self.loop_interval: float = float(self.cfg.get("loop_interval_secs", 1.5))
        # 提示相关：间隔打印“按 Ctrl + C 停止脚本”
        self._last_hint_ts: float = 0.0
        self.hint_interval_secs: float = 5.0

    # 升级逻辑：先尝试模板匹配，然后补充固定坐标点击
    def perform_upgrades(self) -> None:
        up_cfg = self.cfg.get("upgrade", {})
        tmpl_path = resolve_path(up_cfg.get("template_path"))
        region_dict = up_cfg.get("region")
        region = _region_from_dict(region_dict)
        threshold = float(up_cfg.get("threshold", 0.85))
        max_clicks = int(up_cfg.get("max_clicks_per_loop", 3))

        clicks_done = 0
        if tmpl_path and tmpl_path.exists():
            img = self.screen.grab(region)
            match = find_one(img, str(tmpl_path), threshold)
            if match:
                (mx, my, score, (w, h)) = match
                click_center((mx, my), (w, h))
                clicks_done += 1
                # 继续尝试在附近再次匹配可扩展，当前点击一次即可

        # 固定坐标点击兜底
        positions: List[List[int]] = up_cfg.get("positions", []) or []
        for pos in positions:
            if clicks_done >= max_clicks:
                break
            if not pos or len(pos) < 2:
                continue
            x, y = int(pos[0]), int(pos[1])
            click(x, y)
            clicks_done += 1

    def start_next_wave(self) -> bool:
        nw = self.cfg.get("next_wave", {})
        cooldown = float(nw.get("cooldown_secs", 3.0))
        now = time.time()
        if now - self.last_wave_ts < cooldown:
            return False

        tmpl_path = resolve_path(nw.get("template_path"))
        region = _region_from_dict(nw.get("region"))
        threshold = float(nw.get("threshold", 0.85))

        # 模板优先
        if tmpl_path and tmpl_path.exists():
            img = self.screen.grab(region)
            match = find_one(img, str(tmpl_path), threshold)
            if match:
                (mx, my, score, (w, h)) = match
                click_center((mx, my), (w, h))
                self.last_wave_ts = now
                return True

        # 坐标兜底
        pos = nw.get("position")
        if pos and len(pos) >= 2:
            x, y = int(pos[0]), int(pos[1])
            click(x, y)
            self.last_wave_ts = now
            return True

        return False

    def detect_breach(self) -> bool:
        br = self.cfg.get("breach", {})
        tmpl_path = resolve_path(br.get("template_path"))
        region = _region_from_dict(br.get("region"))
        threshold = float(br.get("threshold", 0.88))
        if tmpl_path and tmpl_path.exists():
            img = self.screen.grab(region)
            match = find_one(img, str(tmpl_path), threshold)
            return match is not None
        return False

    def restart_game(self) -> None:
        rst = self.cfg.get("restart", {})
        close_hk = rst.get("close_hotkey") or ["alt", "f4"]
        start_cmd = rst.get("start_command") or ""
        post_wait = float(rst.get("post_wait_secs", 5.0))
        menu_hks: List[List[str]] = rst.get("menu_hotkeys", []) or []

        # 关闭当前游戏窗口（通用方式）
        hotkey(close_hk)
        sleep(2.0)

        # 启动游戏
        if start_cmd:
            try:
                subprocess.Popen(start_cmd, shell=True)
            except Exception as e:
                print(f"[restart] 启动命令失败: {e}")
        sleep(post_wait)

        # 进入主界面或开局（可选）
        for seq in menu_hks:
            hotkey(seq)
            sleep(0.5)

    def run(self) -> None:
        print("[runner] 启动自动运行。按 Ctrl + C 停止脚本。")
        self._last_hint_ts = time.time()
        while True:
            try:
                if self.detect_breach():
                    print("[runner] 检测到突破，执行重启...")
                    self.restart_game()
                    # 重启后稍作等待
                    sleep(3.0)
                    continue

                # 升级流程
                self.perform_upgrades()
                # 下一波触发
                started = self.start_next_wave()
                if started:
                    print("[runner] 触发下一波。")

                # 循环提示：定期重申退出方式
                now = time.time()
                if now - self._last_hint_ts >= self.hint_interval_secs:
                    print("[提示] 按 Ctrl + C 停止脚本。")
                    self._last_hint_ts = now

                sleep(self.loop_interval)
            except KeyboardInterrupt:
                print("[runner] 收到退出信号，停止。")
                break
            except Exception as e:
                print(f"[runner] 运行异常: {e}")
                sleep(1.0)