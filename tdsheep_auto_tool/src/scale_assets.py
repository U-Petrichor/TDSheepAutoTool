from __future__ import annotations

"""
scale_assets.py
- 功能：为 a_1 到 a_6 基础图片批量生成不同缩放比例的 PNG 文件
- 质量：使用 OpenCV 的 Lanczos4（高质量）重采样
- 路径：读取与写入目录为 tdsheep_auto_tool/assets/a
- 命名：a_{i}_{scale}.png（示例：a_1_80.png 表示 80%）

用法：
1) 将 6 张基础图片命名为 a_1.png ... a_6.png，放置在 assets/a/
2) 在项目根目录运行：python -m tdsheep_auto_tool.src.scale_assets
3) 输出文件将生成在 assets/a/ 下
"""

from pathlib import Path
from typing import List
import cv2
import numpy as np

# 复用 match.py 的 assets 目录获取逻辑（保持一致）
from .match import get_assets_dir

# 按需求生成的缩放档
SCALES: List[int] = [50, 67, 75, 80, 90, 100, 110, 125]


def _read_image_unicode(path: Path) -> np.ndarray:
    """以保留透明通道的方式读取图片，兼容中文路径。"""
    if not path.exists():
        raise FileNotFoundError(f"源图片不存在: {path}")
    data = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)  # 保留 alpha 通道（RGBA）
    if img is None:
        raise ValueError(f"无法读取图片: {path}")
    return img


def _write_png_unicode(path: Path, img: np.ndarray) -> None:
    """以 PNG 格式写入图片，兼容中文路径与透明通道。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode('.png', img)
    if not ok:
        raise ValueError(f"PNG 编码失败: {path}")
    buf.tofile(str(path))


def _resize_lanczos(img: np.ndarray, scale_percent: int) -> np.ndarray:
    """使用 Lanczos4 高质量缩放（保持宽高比、保留通道）。"""
    h, w = img.shape[:2]
    new_w = max(1, int(round(w * scale_percent / 100.0)))
    new_h = max(1, int(round(h * scale_percent / 100.0)))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)


def generate_scaled_variants(base_path: Path, scales: List[int]) -> None:
    """为单个基础图片生成多尺度版本。"""
    try:
        img = _read_image_unicode(base_path)
    except Exception as e:
        print(f"[skip] {base_path.name}: {e}")
        return
    stem = base_path.stem  # a_1
    out_dir = base_path.parent
    for s in scales:
        scaled = _resize_lanczos(img, s)
        out_path = out_dir / f"{stem}_{s}.png"
        _write_png_unicode(out_path, scaled)
        print(f"[gen] {out_path.name} ({scaled.shape[1]}x{scaled.shape[0]})")


def process_directory(dir_path: Path, scales: List[int]) -> None:
    """递归处理目录下的所有 PNG 图片（跳过已生成的缩放版本）。"""
    if not dir_path.exists():
        print(f"[skip] 目录不存在: {dir_path}")
        return

    # 获取所有 png 文件
    for file_path in dir_path.glob("*.png"):
        # 跳过文件名中包含 _数字.png 的文件（认为是已生成的缩放图）
        # 简单判断：检查最后一部分是否为 _数字
        stem = file_path.stem
        parts = stem.split('_')
        if len(parts) > 1 and parts[-1].isdigit() and int(parts[-1]) in scales:
            continue
        
        print(f"[proc] 处理原图: {file_path.name}")
        generate_scaled_variants(file_path, scales)

def main() -> None:
    print("[scale] 开始批量生成多尺度图片...")
    assets_dir = get_assets_dir()
    
    # 需要处理的子文件夹列表
    target_dirs = [
        "a", 
        "page_home", 
        "page_frontline", 
        "page_defenseline", 
        "page_wolfpack",
        "auto_arena"
    ]
    
    for d in target_dirs:
        p = assets_dir / d
        print(f"\n--- Scanning {d} ---")
        process_directory(p, SCALES)
        
    print("\n[done] 所有任务完成")


if __name__ == '__main__':
    main()