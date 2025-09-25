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

def get_verify_name(verify):
    """Chuyển đổi mã xác thực thành tên"""
    verify_map = {
        1: "Mật khẩu",
        3: "Thẻ",
        4: "Vân tay",
        11: "Mật khẩu",
        12: "Vân tay",
        15: "Khuôn mặt",
        25: "Lòng bàn tay"
    }
    return verify_map.get(verify, f"Khác ({verify})")

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
                    print(f"{'User ID':<10} {'Tên người dùng':<20} {'Thời gian':<20} {'Trạng thái':<15} {'Verify':<10}")
                    print("-" * 80)
                    
                    # Tạo dictionary để map user ID với tên
                    user_map = {user.uid: user.name for user in users}
                    
                    # Sắp xếp theo thời gian
                    today_attendances.sort(key=lambda x: x.timestamp)
                    
                    for att in today_attendances:
                        user_name = user_map.get(att.user_id, "Không xác định")
                        status = get_status_name(att.status)
                        verify = get_verify_name(att.verify)
                        time_str = att.timestamp.strftime("%H:%M:%S")
                        
                        print(f"{att.user_id:<10} {user_name:<20} {time_str:<20} {status:<15} {verify:<10}")
                    
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