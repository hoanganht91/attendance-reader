@echo off
chcp 65001 >nul

echo 🚀 Thiết lập môi trường cho chương trình đọc máy chấm công
echo ============================================================

REM Kiểm tra Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python chưa được cài đặt. Vui lòng cài đặt Python 3.6+ trước.
    pause
    exit /b 1
)

echo ✅ Tìm thấy Python
python --version

REM Tạo virtual environment
echo 📦 Tạo virtual environment...
python -m venv venv

REM Kích hoạt virtual environment
echo 🔄 Kích hoạt virtual environment...
call venv\Scripts\activate.bat

REM Nâng cấp pip
echo ⬆️ Nâng cấp pip...
python -m pip install --upgrade pip

REM Cài đặt dependencies
echo 📥 Cài đặt dependencies...
pip install -r requirements.txt

REM Tạo file .env từ template
if not exist ".env" (
    echo ⚙️ Tạo file cấu hình .env...
    copy .env.example .env
    echo ✅ Đã tạo file .env. Vui lòng chỉnh sửa với thông tin máy chấm công của bạn.
) else (
    echo ℹ️ File .env đã tồn tại.
)

echo.
echo 🎉 Thiết lập hoàn tất!
echo.
echo Các bước tiếp theo:
echo 1. Chỉnh sửa file .env với thông tin máy chấm công
echo 2. Kích hoạt virtual environment: venv\Scripts\activate.bat
echo 3. Chạy chương trình: python attendance_reader.py
echo.
echo Để xem hướng dẫn chi tiết, đọc file README.md
pause 