@echo off
echo 工程预算管理系统启动脚本
echo ========================

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo 正在安装依赖包...
pip install -r requirements.txt

echo 正在启动后端服务...
echo 服务将在 http://localhost:5000 启动
echo 请在浏览器中打开 index.html 文件
echo 按 Ctrl+C 停止服务
echo.

python budget-b.py
