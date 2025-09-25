#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test kết nối đơn giản để kiểm tra máy chấm công
"""

import os
import sys
from dotenv import load_dotenv
from zk import ZK

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
                
                attendances = conn.get_attendance()
                print(f"⏰ Số bản ghi chấm công: {len(attendances)}")
                
                device_time = conn.get_time()
                print(f"🕐 Thời gian thiết bị: {device_time}")
                
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