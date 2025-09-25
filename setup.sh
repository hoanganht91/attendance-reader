#!/bin/bash

echo "🚀 Thiết lập môi trường cho chương trình đọc máy chấm công"
echo "============================================================"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 chưa được cài đặt. Vui lòng cài đặt Python 3.6+ trước."
    exit 1
fi

echo "✅ Tìm thấy Python: $(python3 --version)"

# Tạo virtual environment
echo "📦 Tạo virtual environment..."
python3 -m venv venv

# Kích hoạt virtual environment
echo "🔄 Kích hoạt virtual environment..."
source venv/bin/activate

# Nâng cấp pip
echo "⬆️ Nâng cấp pip..."
pip install --upgrade pip

# Cài đặt dependencies
echo "📥 Cài đặt dependencies..."
pip install -r requirements.txt

# Tạo file .env từ template
if [ ! -f ".env" ]; then
    echo "⚙️ Tạo file cấu hình .env..."
    cp .env.example .env
    echo "✅ Đã tạo file .env. Vui lòng chỉnh sửa với thông tin máy chấm công của bạn."
else
    echo "ℹ️ File .env đã tồn tại."
fi

echo ""
echo "🎉 Thiết lập hoàn tất!"
echo ""
echo "Các bước tiếp theo:"
echo "1. Chỉnh sửa file .env với thông tin máy chấm công"
echo "2. Kích hoạt virtual environment: source venv/bin/activate"
echo "3. Chạy chương trình: python attendance_reader.py"
echo ""
echo "Để xem hướng dẫn chi tiết, đọc file README.md" 