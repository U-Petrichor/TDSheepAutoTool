# TD Sheep Auto Tool

一个基于图像识别（OpenCV + PyAutoGUI）的塔防自动化脚本。现已支持单文件 EXE 分发，无需安装 Python 或依赖，开箱即用。

**两种使用方式**
- 推荐：直接使用打包好的 `tdsheep.exe`（无需环境）
- 备选：作为命令行工具（pip 安装）

**快速开始（EXE）**
- 获取 `tdsheep.exe`：在 `dist/tdsheep.exe`（或 Release 附件）中获取，放到可写目录。
- 首次运行会在 EXE 同级生成 `config.json` 与 `tdsheep_auto_tool/templates/`。
- 常用命令：
  - `tdsheep.exe calibrate` 交互式采集坐标并写入 `config.json`
  - `tdsheep.exe capture-template --name next_wave` 采集屏幕区域保存为模板 PNG
  - `tdsheep.exe run` 启动自动化脚本
- 模板与配置：将模板 PNG 放在 `tdsheep_auto_tool/templates/`，`config.json` 中的相对路径以 EXE 同级为基准。

**克隆仓库后直接运行 EXE**
- 若你已将 `dist/tdsheep.exe`（或 `bin/tdsheep.exe`）随仓库/Release 一并提供，别人克隆后可直接运行该 EXE，无需安装依赖。
- 推荐做法：通过 GitHub Release 附件分发 EXE（更轻量），或在仓库提供 `dist/tdsheep.exe`。
- 如无 EXE，其他人可在仓库根目录运行 `build_exe.bat` 一键生成。

**从源码构建（开发者）**
- 安装依赖（使用系统 Python，无需虚拟环境）：
  - `python -m pip install --user -r requirements.txt`
  - `python -m pip install --user pyinstaller`
- 生成 EXE：
  - `python -m PyInstaller --onefile -n tdsheep tdsheep_auto_tool/main.py --hidden-import=cv2 --hidden-import=pyscreeze --hidden-import=pymsgbox --hidden-import=mouseinfo --hidden-import=pygetwindow`
  - 或执行 `build_exe.bat`
- 生成结果：`dist/tdsheep.exe`

**路径与资源说明（EXE 模式）**
- 配置文件：`config.json` 位于 EXE 同级目录（首次运行自动生成）。
- 模板目录：`tdsheep_auto_tool/templates/` 位于 EXE 同级目录（首次运行自动创建）。
- 相对路径：`config.json` 中所有相对路径均以 EXE 同级为基准。

**使用建议**
- 将 EXE 放在有写权限的目录（桌面/文档），避免放在系统保护目录。
- 多显示器：默认使用主显示器坐标；请确保游戏在主屏或根据实际分辨率采集坐标与模板。
- 如需自动重启游戏，在 `config.json` 的 `restart.start_command` 填写启动命令并设置热键序列。

**故障排查**
- 启动 EXE 报导入错误：重建 EXE 时保留上面的 `--hidden-import` 参数。
- EXE 被系统阻止：右键文件属性，勾选“解除阻止”。
- 识别不稳定：
  - 提高阈值（`threshold`）或缩小 `region` 提升准确度。
  - 模板采集时保持无 UI 遮挡、相同缩放与分辨率。

**命令行工具（可选）**
- 构建并安装：`pip wheel .` → `pip install dist/*.whl`
- 使用命令：`tdsheep run` / `tdsheep calibrate` / `tdsheep capture-template --name xxx`

现在已满足“别人克隆后可直接运行 EXE”的分发需求；如需我替你发布 GitHub Release 并附带 EXE，请告诉我仓库权限与版本号。
