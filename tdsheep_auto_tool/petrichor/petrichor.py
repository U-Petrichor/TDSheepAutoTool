import os
import sys

try:
    from pyfiglet import Figlet
except Exception:
    Figlet = None


def _candidate_paths():
    paths = []
    # PyInstaller 一文件运行时的临时解包目录
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
        # 显式添加通过 --add-data 打包的两种可能路径
        paths.append(os.path.join(base, "tdsheep_auto_tool", "branding", "banner.txt"))
        paths.append(os.path.join(base, "branding", "banner.txt"))
        paths.append(os.path.join(base, "tdsheep_auto_tool", "branding", "brand.txt"))
        paths.append(os.path.join(base, "branding", "brand.txt"))
    # 源码运行时，相对当前文件查找
    here = os.path.dirname(__file__)
    paths.append(os.path.join(here, "branding", "banner.txt"))
    paths.append(os.path.join(here, "branding", "brand.txt"))
    return paths


def _read_brand_name() -> str:
    # 优先使用 brand.txt 的内容（第一行）
    for p in _candidate_paths():
        if p.endswith("brand.txt") and os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    first = f.readline().strip()
                    if first:
                        return first
            except Exception:
                pass
    return "Petrichor"


def _read_banner_block() -> str:
    for p in _candidate_paths():
        if p.endswith("banner.txt") and os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    # 兜底文案（若 banner.txt 缺失）
    return (
        "//------------------------------ 信息 ----------------------------------\\\n"
        "|| 脚本启动成功                                                     ||\n"
        "|| 本脚本的作者为 Petrichor                                         ||\n"
        "|| 如果碰到什么问题或者有什么意见请联系我                           ||\n"
        "|| 联系方式：                                                      ||\n"
        "|| A：                                                            ||\n"
        "|| B：                                                            ||\n"
        "|| C：                                                            ||\n"
        "\\\\--------------------------------------------------------------------//\n"
    )


def print_branding() -> None:
    name = _read_brand_name()
    # 选择偏斜且包含斜杠的字体
    fig_font = "slant"
    if Figlet:
        try:
            fig = Figlet(font=fig_font)
            art = fig.renderText(name)
            print(art.rstrip())
        except Exception:
            print(name)
    else:
        print(name)
    # 打印信息块
    print(_read_banner_block())