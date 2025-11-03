import dbus
import time
import threading
from datetime import datetime

class RaspberryPiNetworkManager:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.network_manager = None
        self.connection_priority = {
            '5G': 100,
            '4G': 200, 
            'wifi': 300,
            'ethernet': 400
        }
        self.current_connection = None
        self.monitoring = False
        self._init_network_manager()
    
    def _init_network_manager(self):
        """初始化NetworkManager DBus连接"""
        try:
            proxy = self.bus.get_object(
                "org.freedesktop.NetworkManager", 
                "/org/freedesktop/NetworkManager"
            )
            self.network_manager = dbus.Interface(
                proxy, 
                "org.freedesktop.NetworkManager"
            )
            print("✓ NetworkManager连接成功")
        except Exception as e:
            print(f"✗ NetworkManager连接失败: {e}")
    
    def get_available_connections(self):
        """获取所有可用的网络连接"""
        connections = []
        try:
            connection_paths = self.network_manager.ListConnections()
            
            for path in connection_paths:
                conn_proxy = self.bus.get_object(
                    "org.freedesktop.NetworkManager", 
                    path
                )
                conn_interface = dbus.Interface(
                    conn_proxy,
                    "org.freedesktop.NetworkManager.Settings.Connection"
                )
                settings = conn_interface.GetSettings()
                
                conn_info = {
                    'path': path,
                    'name': settings['connection']['id'],
                    'type': settings['connection']['type'],
                    'timestamp': str(datetime.now())
                }
                
                # 判断连接类型
                if 'gsm' in conn_info['type']:
                    conn_info['category'] = '5G' if '5G' in conn_info['name'] else '4G'
                elif 'wifi' in conn_info['type']:
                    conn_info['category'] = 'wifi'
                elif 'ethernet' in conn_info['type']:
                    conn_info['category'] = 'ethernet'
                else:
                    conn_info['category'] = 'other'
                
                connections.append(conn_info)
                
        except Exception as e:
            print(f"获取连接列表错误: {e}")
        
        return connections
    
    def set_connection_priority(self, connection_name, metric):
        """设置连接优先级（度量值）"""
        try:
            connections = self.get_available_connections()
            target_conn = None
            
            for conn in connections:
                if conn['name'] == connection_name:
                    target_conn = conn
                    break
            
            if target_conn:
                conn_proxy = self.bus.get_object(
                    "org.freedesktop.NetworkManager", 
                    target_conn['path']
                )
                conn_interface = dbus.Interface(
                    conn_proxy,
                    "org.freedesktop.NetworkManager.Settings.Connection"
                )
                
                settings = conn_interface.GetSettings()
                ipv4_settings = settings.get('ipv4', {})
                ipv4_settings['route-metric'] = dbus.UInt32(metric)
                
                settings['ipv4'] = ipv4_settings
                conn_interface.Update(settings)
                
                print(f"✓ 设置连接 {connection_name} 的优先级为 {metric}")
                return True
            else:
                print(f"✗ 未找到连接: {connection_name}")
                return False
                
        except Exception as e:
            print(f"设置优先级错误: {e}")
            return False
    
    def activate_connection(self, connection_name):
        """激活指定连接"""
        try:
            connections = self.get_available_connections()
            target_conn = None
            
            for conn in connections:
                if conn['name'] == connection_name:
                    target_conn = conn
                    break
            
            if target_conn:
                # 获取活动连接列表
                active_connections = self.network_manager.ActiveConnections
                
                # 激活新连接
                self.network_manager.ActivateConnection(
                    target_conn['path'],
                    "/",
                    "/"
                )
                
                self.current_connection = connection_name
                print(f"✓ 已激活连接: {connection_name}")
                return True
            else:
                print(f"✗ 未找到连接: {connection_name}")
                return False
                
        except Exception as e:
            print(f"激活连接错误: {e}")
            return False
    
    def get_network_status(self):
        """获取当前网络状态"""
        status = {
            'timestamp': str(datetime.now()),
            'current_connection': self.current_connection,
            'available_networks': []
        }
        
        try:
            # 获取设备状态
            devices = self.network_manager.GetDevices()
            
            for device_path in devices:
                device_proxy = self.bus.get_object(
                    "org.freedesktop.NetworkManager", 
                    device_path
                )
                device_props = dbus.Interface(
                    device_proxy,
                    "org.freedesktop.DBus.Properties"
                )
                
                device_type = device_props.Get(
                    "org.freedesktop.NetworkManager.Device", 
                    "DeviceType"
                )
                state = device_props.Get(
                    "org.freedesktop.NetworkManager.Device", 
                    "State"
                )
                
                device_info = {
                    'type': self._device_type_to_string(device_type),
                    'state': self._device_state_to_string(state)
                }
                
                # 获取IP地址
                try:
                    ip4_config = device_props.Get(
                        "org.freedesktop.NetworkManager.Device", 
                        "Ip4Config"
                    )
                    if ip4_config != "/":
                        ip_proxy = self.bus.get_object(
                            "org.freedesktop.NetworkManager", 
                            ip4_config
                        )
                        ip_props = dbus.Interface(
                            ip_proxy,
                            "org.freedesktop.DBus.Properties"
                        )
                        addresses = ip_props.Get(
                            "org.freedesktop.NetworkManager.IP4Config",
                            "AddressData"
                        )
                        if addresses:
                            device_info['ip_address'] = addresses[0]['address']
                except:
                    device_info['ip_address'] = 'N/A'
                
                status['available_networks'].append(device_info)
                
        except Exception as e:
            print(f"获取网络状态错误: {e}")
        
        return status
    
    def _device_type_to_string(self, device_type):
        """设备类型转字符串"""
        types = {
            1: "ethernet",
            2: "wifi",
            5: "gsm"  # 5G/4G模块
        }
        return types.get(device_type, "unknown")
    
    def _device_state_to_string(self, state):
        """设备状态转字符串"""
        states = {
            0: "unknown",
            10: "unmanaged",
            20: "unavailable", 
            30: "disconnected",
            40: "prepare",
            50: "config",
            60: "need_auth",
            70: "ip_config",
            80: "ip_check",
            90: "secondaries",
            100: "activated"
        }
        return states.get(state, "unknown")
    
    def auto_switch_network(self):
        """自动切换到最佳可用网络"""
        print("开始自动网络切换...")
        
        available_connections = self.get_available_connections()
        connections_by_priority = sorted(
            available_connections,
            key=lambda x: self.connection_priority.get(
                x['category'], 999
            )
        )
        
        # 尝试按优先级顺序激活连接
        for conn in connections_by_priority:
            print(f"尝试连接: {conn['name']} ({conn['category']})")
            
            if self.activate_connection(conn['name']):
                # 设置优先级度量值
                metric = self.connection_priority[conn['category']]
                self.set_connection_priority(conn['name'], metric)
                
                print(f"✓ 已切换到 {conn['name']}")
                return True
        
        print("✗ 无可用网络连接")
        return False
    
    def start_monitoring(self, interval=30):
        """开始后台网络监控"""
        self.monitoring = True
        
        def monitor():
            while self.monitoring:
                status = self.get_network_status()
                
                # 检查当前连接状态
                active_found = False
                for network in status['available_networks']:
                    if network['state'] == 'activated':
                        active_found = True
                        break
                
                if not active_found:
                    print("检测到网络断开，尝试重新连接...")
                    self.auto_switch_network()
                
                time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        print(f"✓ 开始网络监控，检查间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止网络监控"""
        self.monitoring = False
        print("✓ 网络监控已停止")

# 使用示例
if __name__ == "__main__":
    # 创建网络管理器实例
    net_mgr = RaspberryPiNetworkManager()
    
    # 显示可用连接
    print("=== 可用网络连接 ===")
    connections = net_mgr.get_available_connections()
    for conn in connections:
        print(f"- {conn['name']} ({conn['category']})")
    
    # 自动切换到最佳网络
    print("\n=== 自动网络切换 ===")
    net_mgr.auto_switch_network()
    
    # 显示当前状态
    print("\n=== 当前网络状态 ===")
    status = net_mgr.get_network_status()
    print(f"当前连接: {status['current_connection']}")
    print("设备状态:")
    for network in status['available_networks']:
        print(f"  - {network['type']}: {network['state']} ({network.get('ip_address', 'N/A')})")
    
    # 开始后台监控
    print("\n=== 启动网络监控 ===")
    net_mgr.start_monitoring(interval=30)
    
    # 保持程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        net_mgr.stop_monitoring()
        print("程序已退出")