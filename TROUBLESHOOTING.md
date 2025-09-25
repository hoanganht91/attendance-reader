# Troubleshooting Guide

Hướng dẫn xử lý sự cố cho hệ thống đồng bộ dữ liệu chấm công.

## Lỗi thường gặp

### 1. Lỗi kết nối đến máy chấm công

**Triệu chứng:**
- `Connection failed` khi chạy test connection
- `ZKErrorConnection` trong log
- Service không thể sync dữ liệu

**Nguyên nhân và giải pháp:**

#### 1.1 Sai IP hoặc Port
```
Error: Connection test failed: [Errno 10060] A connection attempt failed...
```

**Giải pháp:**
- Kiểm tra IP address trong `config/devices.yaml`
- Ping máy chấm công: `ping 192.168.1.100`
- Kiểm tra port (mặc định 4370)
- Đảm bảo máy chấm công đã bật

#### 1.2 Firewall chặn kết nối
```
Error: Connection timeout
```

**Giải pháp:**
- Tắt Windows Firewall tạm thời để test
- Thêm exception cho port 4370 trong firewall
- Kiểm tra firewall của router/switch

#### 1.3 Máy chấm công đang bận
```
Error: Device busy or locked
```

**Giải pháp:**
- Chờ 1-2 phút rồi thử lại
- Khởi động lại máy chấm công
- Đảm bảo không có ứng dụng khác đang kết nối

### 2. Lỗi Windows Service

#### 2.1 Service không cài đặt được
```
Error installing service: Access is denied
```

**Giải pháp:**
- Chạy script với quyền Administrator
- Click phải → "Run as administrator"
- Kiểm tra UAC settings

#### 2.2 Service không khởi động
```
Error: The service did not respond to the start or control request in a timely fashion
```

**Giải pháp:**
- Kiểm tra log file: `logs/service.log`
- Kiểm tra cấu hình: `config/devices.yaml`
- Chạy manual sync trước: `scripts/manual_sync.bat`

#### 2.3 Service dừng đột ngột
**Giải pháp:**
- Xem Windows Event Viewer → Application logs
- Kiểm tra `logs/service.log` và `logs/app.log`
- Kiểm tra kết nối mạng
- Khởi động lại service

### 3. Lỗi cấu hình

#### 3.1 YAML syntax error
```
Error loading configuration: while parsing a block mapping...
```

**Giải pháp:**
- Kiểm tra indentation (dùng spaces, không dùng tabs)
- Kiểm tra syntax YAML online
- So sánh với file mẫu

#### 3.2 Thiếu thông tin device
```
Error: Device name cannot be empty
```

**Giải pháp:**
- Điền đầy đủ thông tin trong `config/devices.yaml`:
  - name
  - ip
  - device_id
  - port

### 4. Lỗi Python/Dependencies

#### 4.1 Module not found
```
ModuleNotFoundError: No module named 'pyzk'
```

**Giải pháp:**
- Chạy lại `scripts/setup_environment.bat`
- Activate virtual environment: `venv\Scripts\activate.bat`
- Cài đặt thủ công: `pip install -r requirements.txt`

#### 4.2 Python version không tương thích
```
SyntaxError: invalid syntax (f-strings require Python 3.6+)
```

**Giải pháp:**
- Cập nhật Python lên 3.8+
- Chạy lại setup script

### 5. Lỗi dữ liệu

#### 5.1 Không có dữ liệu mới
```
No new records to save
```

**Nguyên nhân:**
- Không có chấm công mới từ lần sync cuối
- Máy chấm công không có dữ liệu
- Lỗi đồng hồ hệ thống

**Giải pháp:**
- Kiểm tra thời gian trên máy chấm công
- Kiểm tra file `data/last_sync.json`
- Test chấm công thử trên máy

#### 5.2 Duplicate records
```
Duplicates detected and skipped
```

**Giải pháp:**
- Đây là hành vi bình thường
- Hệ thống tự động bỏ qua bản ghi trùng

### 6. Lỗi hiệu suất

#### 6.1 Sync chậm
**Nguyên nhân:**
- Mạng chậm
- Quá nhiều dữ liệu
- Máy chấm công phản hồi chậm

**Giải pháp:**
- Tăng timeout trong config
- Giảm tần suất sync
- Kiểm tra băng thông mạng

#### 6.2 File log quá lớn
**Giải pháp:**
- Log tự động rotate (10MB/file)
- Xóa log cũ thủ công nếu cần
- Giảm log level xuống ERROR

## Công cụ debug

### 1. Scripts debug có sẵn
```bash
# Test kết nối
scripts\test_connections.bat

# Xem thống kê
scripts\show_statistics.bat

# Kiểm tra service status
scripts\service_status.bat

# Chạy sync thủ công
scripts\manual_sync.bat
```

### 2. Log files
- `logs/app.log` - Log ứng dụng chính
- `logs/service.log` - Log Windows service
- Windows Event Viewer - System events

### 3. Data files
- `config/devices.yaml` - Cấu hình
- `data/attendance_records.txt` - Dữ liệu chấm công
- `data/last_sync.json` - Tracking sync

## Kiểm tra hệ thống

### 1. Health check cơ bản
```bash
# 1. Kiểm tra Python
python --version

# 2. Kiểm tra dependencies
pip list | findstr pyzk

# 3. Test config
python -c "from src.config_manager import ConfigManager; print('Config OK')"

# 4. Test network
ping 192.168.1.100
telnet 192.168.1.100 4370
```

### 2. Kiểm tra service
```bash
# Service status
sc query AttendanceSystem

# Service config
sc qc AttendanceSystem

# Start service
net start AttendanceSystem

# Stop service
net stop AttendanceSystem
```

## Liên hệ hỗ trợ

Nếu vẫn gặp vấn đề, hãy cung cấp thông tin sau:

1. **Log files** (`logs/` directory)
2. **Configuration** (`config/devices.yaml`)
3. **Error messages** (screenshot hoặc copy text)
4. **System info** (Windows version, Python version)
5. **Network setup** (IP addresses, network topology)

### Log collection script
Chạy script này để thu thập thông tin debug:

```bash
scripts\collect_debug_info.bat
```

## Phục hồi hệ thống

### 1. Reset hoàn toàn
```bash
# Dừng service
scripts\stop_service.bat

# Gỡ service
scripts\uninstall_service.bat

# Xóa dữ liệu (backup trước)
del data\*.* /q

# Cài đặt lại
scripts\setup_environment.bat
scripts\install_service.bat
```

### 2. Backup dữ liệu quan trọng
- `config/devices.yaml` - Cấu hình
- `data/attendance_records.txt` - Dữ liệu chấm công
- `logs/` - Log files để debug

### 3. Factory reset
```bash
# Xóa tất cả trừ source code
rmdir /s venv
rmdir /s logs
rmdir /s data
del config\devices.yaml

# Chạy lại setup
scripts\setup_environment.bat
``` 