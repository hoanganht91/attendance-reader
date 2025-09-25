#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test kết nối đơn giản để kiểm tra máy chấm công
"""

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
from zk import ZK

def get_status_name(status):
    """Chuyển đổi mã trạng thái thành tên"""
    status_map = {
        0: "Vào",
        1: "Ra", 
        2: "Nghỉ ra",
        3: "Nghỉ vào",
        4: "Tăng ca vào",
        5: "Tăng ca ra"
    }
    return status_map.get(status, f"Không xác định ({status})")

def get_verify_name(punch):
    """Chuyển đổi mã xác thực thành tên"""
    verify_map = {
        0: "Mật khẩu",
        1: "Vân tay", 
        2: "Mật khẩu",
        3: "Thẻ",
        4: "Mật khẩu+Vân tay",
        5: "Vân tay",
        15: "Khuôn mặt",
        25: "Lòng bàn tay"
    }
    return verify_map.get(punch, f"Khác ({punch})")

def get_privilege_name(privilege):
    """Chuyển đổi mã quyền thành tên"""
    privilege_map = {
        0: "Người dùng",
        14: "Quản trị viên"
    }
    return privilege_map.get(privilege, f"Không xác định ({privilege})")

def test_connection():
    """Test kết nối cơ bản tới máy chấm công"""
    
    # Load cấu hình
    load_dotenv()
    
    device_ip = os.getenv('DEVICE_IP', '192.168.1.100')
    device_port = int(os.getenv('DEVICE_PORT', 4370))
    device_password = int(os.getenv('DEVICE_PASSWORD', 0))
    
    print("🧪 TEST KẾT NỐI MÁY CHẤM CÔNG")
    print("=" * 50)
    print(f"IP: {device_ip}")
    print(f"Port: {device_port}")
    print(f"Password: {device_password}")
    print("=" * 50)
    
    # Tạo kết nối
    zk = ZK(device_ip, port=device_port, timeout=5, password=device_password)
    
    try:
        print("🔄 Đang kết nối...")
        conn = zk.connect()
        
        if conn:
            print("✅ Kết nối thành công!")
            
            # Test một số thông tin cơ bản
            try:
                firmware = conn.get_firmware_version()
                print(f"📋 Firmware: {firmware}")
                
                users = conn.get_users()
                print(f"👥 Số người dùng: {len(users)}")
                
                device_time = conn.get_time()
                print(f"🕐 Thời gian thiết bị: {device_time}")
                
                # Hiển thị danh sách người dùng
                print(f"\n👥 DANH SÁCH NGƯỜI DÙNG:")
                print("=" * 70)
                print(f"{'ID':<8} {'Tên':<25} {'Card':<15} {'Quyền':<15}")
                print("-" * 70)
                
                for user in users:
                    privilege_name = get_privilege_name(user.privilege)
                    card_id = user.card if user.card else "Không có"
                    print(f"{user.user_id:<8} {user.name:<25} {card_id:<15} {privilege_name:<15}")
                
                # Lấy tất cả bản ghi chấm công
                attendances = conn.get_attendance()
                print(f"📊 Tổng số bản ghi chấm công: {len(attendances)}")
                
                # Lọc bản ghi chấm công ngày hôm nay
                today = date.today()
                today_attendances = []
                
                for att in attendances:
                    if att.timestamp.date() == today:
                        today_attendances.append(att)
                
                print(f"\n📅 BẢN GHI CHẤM CÔNG NGÀY HÔM NAY ({today.strftime('%d/%m/%Y')}):")
                print("=" * 80)
                
                if today_attendances:
                    print(f"{'User ID':<10} {'Tên người dùng':<20} {'Thời gian':<20} {'Trạng thái':<15} {'Phương thức':<12}")
                    print("-" * 82)
                    
                    # Tạo dictionary để map user ID với tên
                    user_map = {user.user_id: user.name for user in users}
                    
                    # Sắp xếp theo thời gian
                    today_attendances.sort(key=lambda x: x.timestamp)
                    
                    for att in today_attendances:
                        user_name = user_map.get(att.user_id, "Không xác định")
                        status = get_status_name(att.status)
                        punch_method = get_verify_name(att.punch)
                        time_str = att.timestamp.strftime("%H:%M:%S")
                        
                        print(f"{att.user_id:<10} {user_name:<20} {time_str:<20} {status:<15} {punch_method:<12}")
                    
                    print(f"\n📈 Tổng số lần chấm công hôm nay: {len(today_attendances)}")
                else:
                    print("❌ Không có bản ghi chấm công nào trong ngày hôm nay.")
                
                print("\n🎉 Test thành công! Thiết bị hoạt động bình thường.")
                
            except Exception as e:
                print(f"⚠️ Kết nối OK nhưng có lỗi khi đọc dữ liệu: {e}")
            
            finally:
                conn.disconnect()
                print("🔌 Đã ngắt kết nối")
                
        else:
            print("❌ Không thể kết nối!")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        print("\n💡 Gợi ý khắc phục:")
        print("- Kiểm tra địa chỉ IP trong file .env")
        print("- Đảm bảo máy chấm công đã bật và kết nối mạng")
        print("- Kiểm tra firewall/antivirus")
        print("- Thử ping tới máy chấm công: ping", device_ip)
        return False
    
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 