import serial
import time

class CellularModuleManager:
    def __init__(self, port='/dev/ttyUSB2', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
    
    def initialize_module(self):
        """初始化4G/5G模块"""
        try:
            self.serial_conn = serial.Serial(
                self.port, 
                self.baudrate, 
                timeout=1
            )
            time.sleep(2)
            
            # 检查模块响应
            self.send_at_command("AT")
            
            # 设置ECM模式[citation:5]
            self.send_at_command('AT+QCFG="usbnet",1')
            
            # 强制5G模式（如果支持）[citation:3]
            self.send_at_command("AT+CNMP=71")
            
            print("✓ 4G/5G模块初始化完成")
            return True
            
        except Exception as e:
            print(f"✗ 4G/5G模块初始化失败: {e}")
            return False
    
    def send_at_command(self, command, timeout=5):
        """发送AT指令"""
        try:
            self.serial_conn.write(f"{command}\r\n".encode())
            time.sleep(0.5)
            
            response = []
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode().strip()
                    if line:
                        response.append(line)
                    if "OK" in line or "ERROR" in line:
                        break
            
            return response
            
        except Exception as e:
            print(f"AT指令错误: {e}")
            return []