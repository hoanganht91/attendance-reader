#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kết nối máy chấm công sử dụng pyzk
Đọc và hiển thị thông tin người dùng
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from zk import ZK, const

class AttendanceReader:
    def __init__(self, ip, port=4370, password=0):
        """
        Khởi tạo kết nối máy chấm công
        
        Args:
            ip (str): Địa chỉ IP của máy chấm công
            port (int): Port kết nối (mặc định 4370)
            password (int): Mật khẩu thiết bị (mặc định 0)
        """
        self.ip = ip
        self.port = port
        self.password = password
        self.zk = ZK(ip, port=port, timeout=5, password=password, force_udp=False, ommit_ping=False)
        self.conn = None
        
    def connect(self):
        """Kết nối tới máy chấm công"""
        try:
            print(f"Đang kết nối tới máy chấm công tại {self.ip}:{self.port}...")
            self.conn = self.zk.connect()
            print("✅ Kết nối thành công!")
            return True
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
            return False
    
    def disconnect(self):
        """Ngắt kết nối"""
        if self.conn:
            self.conn.disconnect()
            print("🔌 Đã ngắt kết nối")
    
    def get_device_info(self):
        """Lấy thông tin thiết bị"""
        if not self.conn:
            print("❌ Chưa có kết nối")
            return None
            
        try:
            print("\n📊 THÔNG TIN THIẾT BỊ:")
            print("-" * 50)
            
            # Thông tin cơ bản
            firmware_version = self.conn.get_firmware_version()
            print(f"Firmware version: {firmware_version}")
            
            # Số lượng người dùng và bản ghi
            users_count = len(self.conn.get_users())
            attendance_count = len(self.conn.get_attendance())
            
            print(f"Số người dùng: {users_count}")
            print(f"Số bản ghi chấm công: {attendance_count}")
            
            # Thời gian thiết bị
            device_time = self.conn.get_time()
            print(f"Thời gian thiết bị: {device_time}")
            
            return {
                'firmware': firmware_version,
                'users_count': users_count,
                'attendance_count': attendance_count,
                'device_time': device_time
            }
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin thiết bị: {e}")
            return None
    
    def get_users(self):
        """Lấy danh sách người dùng"""
        if not self.conn:
            print("❌ Chưa có kết nối")
            return []
            
        try:
            print("\n👥 DANH SÁCH NGƯỜI DÙNG:")
            print("-" * 80)
            print(f"{'ID':<8} {'Tên':<20} {'Card':<15} {'Quyền':<15} {'Mật khẩu':<10}")
            print("-" * 80)
            
            users = self.conn.get_users()
            for user in users:
                privilege_name = self.get_privilege_name(user.privilege)
                card_id = user.card if user.card else "Không có"
                password = "Có" if user.password else "Không"
                
                print(f"{user.uid:<8} {user.name:<20} {card_id:<15} {privilege_name:<15} {password:<10}")
                
            print(f"\n📈 Tổng số người dùng: {len(users)}")
            return users
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách người dùng: {e}")
            return []
    
    def get_privilege_name(self, privilege):
        """Chuyển đổi mã quyền thành tên"""
        privilege_map = {
            0: "Người dùng",
            14: "Quản trị viên"
        }
        return privilege_map.get(privilege, f"Không xác định ({privilege})")
    
    def get_attendance_logs(self, limit=10):
        """Lấy log chấm công gần nhất"""
        if not self.conn:
            print("❌ Chưa có kết nối")
            return []
            
        try:
            print(f"\n⏰ {limit} BẢN GHI CHẤM CÔNG GẦN NHẤT:")
            print("-" * 80)
            print(f"{'User ID':<10} {'Thời gian':<20} {'Trạng thái':<15} {'Verify':<10}")
            print("-" * 80)
            
            attendances = self.conn.get_attendance()
            # Sắp xếp theo thời gian giảm dần và lấy n bản ghi gần nhất
            recent_attendances = sorted(attendances, key=lambda x: x.timestamp, reverse=True)[:limit]
            
            for att in recent_attendances:
                status = self.get_status_name(att.status)
                verify_name = self.get_verify_name(att.verify)
                time_str = att.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"{att.user_id:<10} {time_str:<20} {status:<15} {verify_name:<10}")
                
            return recent_attendances
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy log chấm công: {e}")
            return []
    
    def get_status_name(self, status):
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
    
    def get_verify_name(self, verify):
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
    
    def search_user(self, search_term):
        """Tìm kiếm người dùng theo ID hoặc tên"""
        if not self.conn:
            print("❌ Chưa có kết nối")
            return []
            
        try:
            users = self.conn.get_users()
            search_term = str(search_term).lower()
            
            matching_users = []
            for user in users:
                if (search_term in str(user.uid).lower() or 
                    search_term in user.name.lower()):
                    matching_users.append(user)
            
            if matching_users:
                print(f"\n🔍 KẾT QUẢ TÌM KIẾM CHO '{search_term}':")
                print("-" * 80)
                print(f"{'ID':<8} {'Tên':<20} {'Card':<15} {'Quyền':<15} {'Mật khẩu':<10}")
                print("-" * 80)
                
                for user in matching_users:
                    privilege_name = self.get_privilege_name(user.privilege)
                    card_id = user.card if user.card else "Không có"
                    password = "Có" if user.password else "Không"
                    
                    print(f"{user.uid:<8} {user.name:<20} {card_id:<15} {privilege_name:<15} {password:<10}")
            else:
                print(f"❌ Không tìm thấy người dùng nào với từ khóa '{search_term}'")
                
            return matching_users
            
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm: {e}")
            return []

def main():
    """Hàm chính"""
    # Load cấu hình từ file .env
    load_dotenv()
    
    # Lấy thông tin kết nối
    device_ip = os.getenv('DEVICE_IP', '192.168.1.100')
    device_port = int(os.getenv('DEVICE_PORT', 4370))
    device_password = int(os.getenv('DEVICE_PASSWORD', 0))
    
    print("🔄 CHƯƠNG TRÌNH ĐỌC THÔNG TIN MÁY CHẤM CÔNG")
    print("=" * 60)
    print(f"IP: {device_ip}")
    print(f"Port: {device_port}")
    print("=" * 60)
    
    # Tạo đối tượng reader
    reader = AttendanceReader(device_ip, device_port, device_password)
    
    try:
        # Kết nối
        if not reader.connect():
            sys.exit(1)
        
        # Lấy thông tin thiết bị
        reader.get_device_info()
        
        # Lấy danh sách người dùng
        users = reader.get_users()
        
        # Lấy log chấm công gần nhất
        reader.get_attendance_logs(10)
        
        # Menu tương tác
        while True:
            print(f"\n{'='*60}")
            print("MENU TƯƠNG TÁC:")
            print("1. Hiển thị lại danh sách người dùng")
            print("2. Tìm kiếm người dùng")
            print("3. Hiển thị log chấm công gần nhất")
            print("4. Thông tin thiết bị")
            print("0. Thoát")
            print("="*60)
            
            choice = input("Chọn chức năng (0-4): ").strip()
            
            if choice == '1':
                reader.get_users()
            elif choice == '2':
                search_term = input("Nhập ID hoặc tên để tìm kiếm: ").strip()
                if search_term:
                    reader.search_user(search_term)
                else:
                    print("❌ Vui lòng nhập từ khóa tìm kiếm")
            elif choice == '3':
                try:
                    limit = input("Số bản ghi muốn hiển thị (mặc định 10): ").strip()
                    limit = int(limit) if limit else 10
                    reader.get_attendance_logs(limit)
                except ValueError:
                    print("❌ Vui lòng nhập số hợp lệ")
            elif choice == '4':
                reader.get_device_info()
            elif choice == '0':
                print("👋 Tạm biệt!")
                break
            else:
                print("❌ Lựa chọn không hợp lệ")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Chương trình bị dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {e}")
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main() 