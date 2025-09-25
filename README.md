# Chương trình đọc thông tin máy chấm công

Chương trình Python để kết nối và đọc thông tin từ máy chấm công sử dụng thư viện `pyzk`.

## Tính năng

- ✅ Kết nối tới máy chấm công qua TCP/IP
- 📊 Hiển thị thông tin thiết bị (firmware, số người dùng, số bản ghi)
- 👥 Liệt kê danh sách người dùng trong máy
- 🔍 Tìm kiếm người dùng theo ID hoặc tên
- ⏰ Xem lịch sử chấm công gần nhất
- 🔄 Menu tương tác thân thiện

## Yêu cầu hệ thống

- Python 3.6+
- Máy chấm công hỗ trợ giao thức ZKTeco
- Kết nối mạng tới máy chấm công

## Cài đặt

### 1. Tạo virtual environment

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Trên Windows:
venv\Scripts\activate
# Trên Linux/macOS:
source venv/bin/activate
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình kết nối

Sao chép file cấu hình mẫu:
```bash
cp .env.example .env
```

Chỉnh sửa file `.env` với thông tin máy chấm công của bạn:
```
DEVICE_IP=192.168.1.100    # Địa chỉ IP của máy chấm công
DEVICE_PORT=4370           # Port kết nối (mặc định 4370)
DEVICE_PASSWORD=0          # Mật khẩu thiết bị (mặc định 0)
```

## Sử dụng

Chạy chương trình:
```bash
python attendance_reader.py
```

### Các chức năng chính:

1. **Hiển thị danh sách người dùng**: Liệt kê tất cả người dùng trong máy chấm công
2. **Tìm kiếm người dùng**: Tìm kiếm theo ID hoặc tên người dùng
3. **Xem log chấm công**: Hiển thị các bản ghi chấm công gần nhất
4. **Thông tin thiết bị**: Hiển thị thông tin chi tiết về máy chấm công

## Ví dụ đầu ra

```
🔄 CHƯƠNG TRÌNH ĐỌC THÔNG TIN MÁY CHẤM CÔNG
============================================================
IP: 192.168.1.100
Port: 4370
============================================================
Đang kết nối tới máy chấm công tại 192.168.1.100:4370...
✅ Kết nối thành công!

📊 THÔNG TIN THIẾT BỊ:
--------------------------------------------------
Firmware version: Ver 6.70 Dec 7 2017
Số người dùng: 25
Số bản ghi chấm công: 1534
Thời gian thiết bị: 2024-01-15 14:30:25

👥 DANH SÁCH NGƯỜI DÙNG:
--------------------------------------------------------------------------------
ID       Tên                  Card            Quyền           Mật khẩu  
--------------------------------------------------------------------------------
1        Nguyễn Văn A        123456789       Người dùng      Có        
2        Trần Thị B          987654321       Quản trị viên   Có        
3        Lê Văn C            Không có        Người dùng      Không     

📈 Tổng số người dùng: 25
```

## Xử lý lỗi thường gặp

### Lỗi kết nối
- Kiểm tra địa chỉ IP máy chấm công
- Đảm bảo máy chấm công đã bật và kết nối mạng
- Kiểm tra firewall/antivirus có chặn kết nối không

### Lỗi timeout
- Tăng thời gian timeout trong code
- Kiểm tra tốc độ mạng
- Thử kết nối trực tiếp qua cable

### Lỗi quyền truy cập
- Kiểm tra mật khẩu thiết bị trong file `.env`
- Đảm bảo thiết bị cho phép kết nối từ xa

## Tùy chỉnh

Bạn có thể tùy chỉnh các thông số trong file `attendance_reader.py`:

- `timeout`: Thời gian chờ kết nối (mặc định 5 giây)
- `force_udp`: Bắt buộc sử dụng UDP thay vì TCP
- `ommit_ping`: Bỏ qua ping trước khi kết nối

## Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra log lỗi chi tiết
2. Xác nhận cấu hình mạng
3. Thử nghiệm với các thiết bị khác

## License

MIT License - Xem file LICENSE để biết chi tiết. 