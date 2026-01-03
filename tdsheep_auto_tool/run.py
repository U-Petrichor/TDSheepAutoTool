import sys
import os

# 确保当前目录在 sys.path 中，以便能找到 src 包
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.main import main

if __name__ == '__main__':
    main()