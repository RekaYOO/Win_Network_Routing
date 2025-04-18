import subprocess
import re
import logging
import argparse
from typing import List, Optional, Tuple, Dict, Any
import json
import os
from pathlib import Path
import ipaddress

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_routing.log'),
        logging.StreamHandler()
    ]
)

class ConfigManager:
    def __init__(self, config_path: str = 'routes.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "routes": [],
            "default_metrics": {
                "campus": {
                    "ipv6": 1
                },
                "user": {
                    "ipv4": 1
                }
            }
        }

        if not os.path.exists(self.config_path):
            self.logger.warning(f"配置文件 {self.config_path} 不存在，将使用默认配置")
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 验证配置格式
                if not isinstance(config, dict) or 'routes' not in config:
                    raise ValueError("配置文件格式错误")
                return config
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"加载配置文件时出错: {e}")
            return default_config
        except Exception as e:
            self.logger.error(f"加载配置文件时发生未知错误: {e}")
            return default_config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置文件时出错: {e}")

    def get_routes(self) -> List[str]:
        """获取路由规则列表"""
        return self.config.get('routes', [])

    def get_metrics(self, network_type: str, protocol: str) -> int:
        """获取指定网络类型和协议的跃点数"""
        return self.config.get('default_metrics', {}).get(network_type, {}).get(protocol, 1)

    def test_routes(self) -> Tuple[bool, List[str]]:
        """测试路由规则格式是否正确
        
        Returns:
            Tuple[bool, List[str]]: (是否全部正确, 错误信息列表)
        """
        errors = []
        routes = self.get_routes()
        
        for i, route in enumerate(routes, 1):
            try:
                # 检查格式是否为 "IP-CIDR,IP/MASK,DIRECT"
                parts = route.split(',')
                if len(parts) != 3:
                    errors.append(f"规则 {i}: 格式错误，应为 'IP-CIDR,IP/MASK,DIRECT'")
                    continue
                
                if parts[0] != 'IP-CIDR':
                    errors.append(f"规则 {i}: 类型错误，应为 'IP-CIDR'")
                    continue
                
                if parts[2] != 'DIRECT':
                    errors.append(f"规则 {i}: 目标错误，应为 'DIRECT'")
                    continue
                
                # 检查 IP/MASK 格式
                ip_mask = parts[1]
                if '/' not in ip_mask:
                    errors.append(f"规则 {i}: IP地址格式错误，缺少掩码")
                    continue
                
                ip, mask = ip_mask.split('/')
                try:
                    # 验证 IP 地址格式
                    ipaddress.ip_address(ip)
                    # 验证掩码格式
                    mask = int(mask)
                    if not (0 <= mask <= 32):
                        errors.append(f"规则 {i}: 掩码值错误，应在 0-32 之间")
                except ValueError as e:
                    errors.append(f"规则 {i}: IP地址或掩码格式错误 - {str(e)}")
                
            except Exception as e:
                errors.append(f"规则 {i}: 解析错误 - {str(e)}")
        
        return len(errors) == 0, errors

class NetworkManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = ConfigManager()

    def get_network_connections(self) -> List[Dict[str, str]]:
        """获取所有网络连接"""
        try:
            result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                  capture_output=True, text=True, check=True)
            output = result.stdout
            
            # 解析输出
            connections = []
            lines = output.split('\n')
            headers = []
            
            # 找到表头行
            for line in lines:
                if not line.strip():
                    continue
                if '---' in line:  # 表头分隔线
                    continue
                if '管理员状态' in line and '接口名称' in line:  # 表头行
                    headers = [h.strip() for h in line.split() if h.strip()]
                    break
            
            if not headers:
                self.logger.error("无法找到表头行")
                return []
            
            # 解析数据行
            for line in lines:
                if not line.strip() or '---' in line:
                    continue
                if '管理员状态' in line and '接口名称' in line:  # 跳过表头行
                    continue
                
                values = [v.strip() for v in line.split() if v.strip()]
                if len(values) >= len(headers):
                    conn = dict(zip(headers, values))
                    if conn.get('接口名称'):  # 使用正确的列名
                        connections.append(conn)
            
            return connections
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取网络连接时出错: {e}")
            return []
        except Exception as e:
            self.logger.error(f"获取网络连接时发生未知错误: {e}")
            return []

    def print_network_connections(self):
        """打印网络连接列表"""
        connections = self.get_network_connections()
        if not connections:
            print("未找到网络连接")
            return

        # 计算每列的最大宽度
        headers = ['编号', '接口名称', '状态', '类型', '管理状态']
        widths = [len(h) for h in headers]
        
        for i, conn in enumerate(connections, 1):
            widths[0] = max(widths[0], len(str(i)))
            widths[1] = max(widths[1], len(conn.get('接口名称', '')))
            widths[2] = max(widths[2], len(conn.get('状态', '')))
            widths[3] = max(widths[3], len(conn.get('类型', '')))
            widths[4] = max(widths[4], len(conn.get('管理员状态', '')))

        # 打印表头
        header_format = " | ".join(f"{{:<{w}}}" for w in widths)
        separator = "-+-".join("-" * w for w in widths)
        print(header_format.format(*headers))
        print(separator)

        # 打印数据行
        for i, conn in enumerate(connections, 1):
            row = [
                str(i),
                conn.get('接口名称', ''),
                conn.get('状态', ''),
                conn.get('类型', ''),
                conn.get('管理员状态', '')
            ]
            print(header_format.format(*row))

    def get_gateway(self, connection: str) -> Optional[str]:
        """获取指定网络连接的网关"""
        try:
            result = subprocess.run(['netsh', 'interface', 'ip', 'show', 'config', connection],
                                  capture_output=True, text=True, check=True)
            output = result.stdout
            gateway_match = re.search(r'默认网关\s+:\s+(\S+)', output)
            return gateway_match.group(1) if gateway_match else None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取 {connection} 的网关时出错: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取 {connection} 的网关时发生未知错误: {e}")
            return None

    def set_metric(self, connection: str, protocol: str, metric: int, max_retries: int = 3) -> bool:
        """设置网络接口的跃点数"""
        for attempt in range(max_retries):
            try:
                subprocess.run(['netsh', 'interface', 'ipv6' if protocol == 'ipv6' else 'ipv4',
                              'set', 'interface', connection, f'metric={metric}', 'store=persistent'],
                             check=True)
                self.logger.info(f"已将 {connection} 的 {protocol} 跃点数设置为 {metric}")
                return True
            except subprocess.CalledProcessError as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"设置 {connection} 的 {protocol} 跃点数时出错: {e}")
                    return False
                self.logger.warning(f"第 {attempt + 1} 次尝试设置跃点数失败，正在重试...")
        return False

    def add_route(self, ip: str, cidr: str, gateway: str) -> bool:
        """添加单个路由规则"""
        try:
            subprocess.run(['route', 'add', f'{ip}/{cidr}', gateway, '-p'], check=True)
            self.logger.info(f"已添加路由: {ip}/{cidr} 到 {gateway}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"添加路由 {ip}/{cidr} 到 {gateway} 时出错: {e}")
            return False

    def delete_route(self, ip: str, cidr: str) -> bool:
        """删除路由规则"""
        try:
            subprocess.run(['route', 'delete', f'{ip}/{cidr}'], check=True)
            self.logger.info(f"已删除路由: {ip}/{cidr}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"删除路由 {ip}/{cidr} 时出错: {e}")
            return False

    def get_routes(self) -> List[str]:
        """获取当前路由表"""
        try:
            result = subprocess.run(['route', 'print'], capture_output=True, text=True, check=True)
            return result.stdout.split('\n')
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取路由表时出错: {e}")
            return []

    def reset_metrics(self, connection: str) -> bool:
        """重置网络接口的跃点数为默认值"""
        try:
            # 重置 IPv4 跃点数
            subprocess.run(['netsh', 'interface', 'ipv4', 'set', 'interface', connection,
                          'metric=auto', 'store=persistent'], check=True)
            # 重置 IPv6 跃点数
            subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', connection,
                          'metric=auto', 'store=persistent'], check=True)
            self.logger.info(f"已将 {connection} 的跃点数重置为默认值")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"重置 {connection} 的跃点数时出错: {e}")
            return False

    def reset_all_routes(self) -> bool:
        """删除所有添加的路由规则"""
        try:
            routes = self.get_routes()
            for route in routes:
                if 'DIRECT' in route:  # 只删除我们添加的路由
                    parts = route.split()
                    if len(parts) >= 3:
                        ip_cidr = parts[0]
                        if '/' in ip_cidr:
                            ip, cidr = ip_cidr.split('/')
                            self.delete_route(ip, cidr)
            self.logger.info("已删除所有添加的路由规则")
            return True
        except Exception as e:
            self.logger.error(f"删除路由规则时出错: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='网络路由配置工具')
    parser.add_argument('--list', action='store_true', help='列出所有网络连接')
    parser.add_argument('--routes', action='store_true', help='显示当前路由表')
    parser.add_argument('--user', type=int, help='用户网连接编号')
    parser.add_argument('--campus', type=int, help='校园网连接编号')
    parser.add_argument('--config', type=str, help='配置文件路径', default='routes.json')
    parser.add_argument('--reset', action='store_true', help='重置所有设置到默认值')
    parser.add_argument('--test', action='store_true', help='测试路由规则格式')
    args = parser.parse_args()

    manager = NetworkManager()

    if args.test:
        print("正在测试路由规则格式...")
        success, errors = manager.config.test_routes()
        if success:
            print("所有路由规则格式正确")
        else:
            print("发现以下错误:")
            for error in errors:
                print(f"  - {error}")
        return

    if args.reset:
        print("正在重置所有设置...")
        connections = manager.get_network_connections()
        for conn in connections:
            manager.reset_metrics(conn['接口名称'])
        manager.reset_all_routes()
        print("所有设置已重置完成")
        return

    if args.list:
        print("可用的网络连接:")
        manager.print_network_connections()
        return

    if args.routes:
        routes = manager.get_routes()
        print("当前路由表:")
        for route in routes:
            print(route)
        return

    if args.user is None or args.campus is None:
        connections = manager.get_network_connections()
        if not connections:
            print("未找到网络连接，请检查系统设置。")
            return

        print("可用的网络连接:")
        manager.print_network_connections()

        while True:
            try:
                user_choice = int(input("请选择用户网连接的编号: ")) - 1
                campus_choice = int(input("请选择校园网连接的编号: ")) - 1
                if 0 <= user_choice < len(connections) and 0 <= campus_choice < len(connections):
                    user_connection = connections[user_choice]['接口名称']
                    campus_connection = connections[campus_choice]['接口名称']
                    break
                else:
                    print("输入的编号无效，请重新输入。")
            except ValueError:
                print("输入无效，请输入有效的编号。")
    else:
        connections = manager.get_network_connections()
        if not connections or args.user > len(connections) or args.campus > len(connections):
            print("无效的连接编号")
            return
        user_connection = connections[args.user - 1]['接口名称']
        campus_connection = connections[args.campus - 1]['接口名称']

    user_gateway = manager.get_gateway(user_connection)
    campus_gateway = manager.get_gateway(campus_connection)

    if user_gateway and campus_gateway:
        campus_ipv6_metric = manager.config.get_metrics('campus', 'ipv6')
        user_ipv4_metric = manager.config.get_metrics('user', 'ipv4')

        if manager.set_metric(campus_connection, 'ipv6', campus_ipv6_metric) and \
           manager.set_metric(user_connection, 'ipv4', user_ipv4_metric):
            ip_cidrs = manager.config.get_routes()
            for ip_cidr in ip_cidrs:
                ip, cidr = ip_cidr.split(',')[1].split('/')
                manager.add_route(ip, cidr, campus_gateway)

if __name__ == "__main__":
    main()
    