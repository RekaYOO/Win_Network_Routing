import subprocess
import re
import json
import os

# 配置文件路径
CONFIG_FILE = os.path.join('config', 'network_config.json')

# NEU路由配置列表
IP_CIDRS = [
    "IP-CIDR,202.118.0.0/19,DIRECT",
    "IP-CIDR,202.199.0.0/20,DIRECT",
    "IP-CIDR,210.30.192.0/20,DIRECT",
    "IP-CIDR,219.216.64.0/18,DIRECT",
    "IP-CIDR,58.154.160.0/19,DIRECT",
    "IP-CIDR,58.154.192.0/18,DIRECT",
    "IP-CIDR,118.202.0.0/19,DIRECT",
    "IP-CIDR,118.202.32.0/20,DIRECT",
    "IP-CIDR,172.16.0.0/12,DIRECT",
    "IP-CIDR,100.64.0.0/10,DIRECT",
    "IP-CIDR,192.168.1.1/24,DIRECT"
]

def save_config(user_connection, campus_connection, user_gateway, campus_gateway):
    # 确保配置目录存在
    os.makedirs('config', exist_ok=True)
    config = {
        'user_connection': user_connection,
        'campus_connection': campus_connection,
        'user_gateway': user_gateway,
        'campus_gateway': campus_gateway,
        'ip_cidrs': IP_CIDRS
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def reset_settings():
    config = load_config()
    if not config:
        print("未找到保存的配置，无法重置。")
        return

    print("\n开始重置网络设置...")
    
    # 重置跃点数
    try:
        # 重置 IPv4 跃点数为自动
        subprocess.run(['netsh', 'interface', 'ipv4', 'set', 'interface', 
                       config['user_connection'], 'metric=auto'], check=True)
        print(f"已重置 {config['user_connection']} 的 IPv4 跃点数为自动")
    except subprocess.CalledProcessError as e:
        print(f"重置 {config['user_connection']} 的 IPv4 跃点数时出错: {e}")

    try:
        # 重置 IPv6 跃点数为自动
        subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', 
                       config['user_connection'], 'metric=auto'], check=True)
        print(f"已重置 {config['user_connection']} 的 IPv6 跃点数为自动")
    except subprocess.CalledProcessError as e:
        print(f"重置 {config['user_connection']} 的 IPv6 跃点数时出错: {e}")

    try:
        # 重置 IPv6 跃点数为自动
        subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', 
                       config['campus_connection'], 'metric=auto'], check=True)
        print(f"已重置 {config['campus_connection']} 的 IPv6 跃点数为自动")
    except subprocess.CalledProcessError as e:
        print(f"重置 {config['campus_connection']} 的 IPv6 跃点数时出错: {e}")

    # 删除路由
    for ip_cidr in config['ip_cidrs']:
        try:
            # 解析 IP-CIDR 格式
            parts = ip_cidr.split(',')
            if len(parts) != 3:
                print(f"无效的路由格式: {ip_cidr}")
                continue
                
            ip_cidr_part = parts[1]
            ip, cidr = ip_cidr_part.split('/')
            
            # 将 CIDR 转换为子网掩码
            cidr = int(cidr)
            if not (0 <= cidr <= 32):
                print(f"无效的 CIDR 值: {cidr}")
                continue
                
            # 计算子网掩码
            mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
            mask_parts = [
                (mask >> 24) & 0xff,
                (mask >> 16) & 0xff,
                (mask >> 8) & 0xff,
                mask & 0xff
            ]
            netmask = '.'.join(map(str, mask_parts))
            
            # 检查路由是否存在
            check_result = subprocess.run(['route', 'print', ip], capture_output=True, text=True)
            if check_result.returncode != 0 or ip not in check_result.stdout:
                print(f"路由不存在: {ip} 掩码 {netmask}")
                continue
            
            # 删除路由
            result = subprocess.run(['route', 'delete', ip, 'mask', netmask], 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"已删除路由: {ip} 掩码 {netmask}")
            else:
                error_msg = result.stderr.strip()
                if "找不到元素" in error_msg or "The element was not found" in error_msg:
                    print(f"路由不存在: {ip} 掩码 {netmask}")
                else:
                    print(f"删除路由失败: {ip} 掩码 {netmask}")
                    print(f"错误信息: {error_msg}")
                
        except Exception as e:
            print(f"处理路由 {ip_cidr} 时出错: {e}")

    print("\n重置完成！")
    # 不再删除配置文件
    print("配置已重置，但配置文件保留。")

def get_network_connections():
    try:
        result = subprocess.run(['netsh', 'interface', 'show', 'interface'], capture_output=True, text=True)
        output = result.stdout
        connections = []
        for line in output.split('\n'):
            if '已启用' in line and '专用' in line:  # 只获取已启用且状态为专用的接口
                parts = line.split()  # 使用空格分割
                if len(parts) >= 4:  # 确保有足够的字段
                    name = parts[3]  # 接口名称通常在第四个位置
                    if name and name != '管理员状态' and name != '类型':
                        # 直接从原始行中获取状态
                        admin_status = parts[0]  # 管理员状态
                        conn_status = parts[1]   # 状态
                        
                        connections.append({
                            'name': name,
                            'admin_status': admin_status,
                            'conn_status': conn_status
                        })
        return connections
    except Exception as e:
        print(f"获取网络连接时出错: {e}")
        return []

def get_gateway(connection):
    try:
        print(f"\n正在获取 {connection} 的网关信息...")
        result = subprocess.run(['netsh', 'interface', 'ip', 'show', 'config', connection], capture_output=True, text=True)
        output = result.stdout
        print(f"网关配置信息:\n{output}")
        
        # 尝试多种方式匹配网关
        patterns = [
            r'默认网关\s+:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            r'Default Gateway\s+:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
            r'Gateway\s+:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        ]
        
        for pattern in patterns:
            gateway_match = re.search(pattern, output)
            if gateway_match:
                gateway = gateway_match.group(1)
                print(f"找到网关: {gateway}")
                return gateway
                
        # 如果正则匹配失败，尝试直接查找包含网关的行
        for line in output.split('\n'):
            if '默认网关' in line or 'Default Gateway' in line or 'Gateway' in line:
                parts = line.split(':')
                if len(parts) > 1:
                    gateway = parts[1].strip()
                    if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', gateway):
                        print(f"找到网关: {gateway}")
                        return gateway
                        
        print(f"未找到 {connection} 的网关信息")
        return None
    except Exception as e:
        print(f"获取 {connection} 的网关时出错: {e}")
        return None

def set_metric(connection, protocol, metric):
    try:
        # 先禁用自动跃点
        if protocol == 'ipv4':
            result = subprocess.run(['netsh', 'interface', 'ipv4', 'set', 'interface', connection,
                                  'metric=auto', 'store=persistent'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"禁用自动跃点失败: {result.stderr}")
                return False
            print(f"已禁用 {connection} 的 IPv4 自动跃点")
            
            # 然后设置具体的跃点值
            result = subprocess.run(['netsh', 'interface', 'ipv4', 'set', 'interface', connection,
                                  f'metric={metric}', 'store=persistent'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"设置跃点数失败: {result.stderr}")
                return False
            print(f"已将 {connection} 的 IPv4 跃点数设置为 {metric}")
            
        elif protocol == 'ipv6':
            result = subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', connection,
                                  'metric=auto', 'store=persistent'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"禁用自动跃点失败: {result.stderr}")
                return False
            print(f"已禁用 {connection} 的 IPv6 自动跃点")
            
            # 然后设置具体的跃点值
            result = subprocess.run(['netsh', 'interface', 'ipv6', 'set', 'interface', connection,
                                  f'metric={metric}', 'store=persistent'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"设置跃点数失败: {result.stderr}")
                return False
            print(f"已将 {connection} 的 IPv6 跃点数设置为 {metric}")
            
        return True
    except Exception as e:
        print(f"设置 {connection} 的 {protocol} 跃点数时出错: {e}")
        return False

def add_routes(gateway, ip_cidrs):
    for ip_cidr in ip_cidrs:
        try:
            # 解析 IP-CIDR 格式
            parts = ip_cidr.split(',')
            if len(parts) != 3:
                print(f"无效的路由格式: {ip_cidr}")
                continue
                
            ip_cidr_part = parts[1]
            ip, cidr = ip_cidr_part.split('/')
            
            # 将 CIDR 转换为子网掩码
            cidr = int(cidr)
            if not (0 <= cidr <= 32):
                print(f"无效的 CIDR 值: {cidr}")
                continue
                
            # 计算子网掩码
            mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
            mask_parts = [
                (mask >> 24) & 0xff,
                (mask >> 16) & 0xff,
                (mask >> 8) & 0xff,
                mask & 0xff
            ]
            netmask = '.'.join(map(str, mask_parts))
            
            # 检查路由是否已存在
            check_result = subprocess.run(['route', 'print', ip], capture_output=True, text=True)
            if check_result.returncode == 0 and ip in check_result.stdout:
                print(f"路由已存在: {ip} 掩码 {netmask}")
                continue
            
            # 添加路由
            result = subprocess.run(['route', 'add', ip, 'mask', netmask, gateway, '-p'], 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"已添加路由: {ip} 掩码 {netmask} 到 {gateway}")
            else:
                error_msg = result.stderr.strip()
                if "对象已存在" in error_msg or "The object already exists" in error_msg:
                    print(f"路由已存在: {ip} 掩码 {netmask}")
                else:
                    print(f"添加路由失败: {ip} 掩码 {netmask} 到 {gateway}")
                    print(f"错误信息: {error_msg}")
                
        except Exception as e:
            print(f"处理路由 {ip_cidr} 时出错: {e}")

def show_current_routes():
    """
    显示当前系统中的路由配置
    """
    try:
        # 获取当前路由表
        result = subprocess.run(['route', 'print'], capture_output=True, text=True)
        if result.returncode != 0:
            print("获取路由表失败")
            return

        routes = result.stdout.split('\n')
        
        # 查找IPv4路由表的开始位置
        start_index = -1
        for i, line in enumerate(routes):
            if "IPv4 路由表" in line or "IPv4 Route Table" in line:
                start_index = i
                break
                
        if start_index == -1:
            print("未找到IPv4路由表")
            return
            
        print("\n当前系统路由配置:")
        print("=" * 80)
        print("目标网络          网络掩码          网关              接口              跃点数")
        print("-" * 80)
        
        # 跳过表头
        start_index += 4
        
        # 解析并显示路由
        for line in routes[start_index:]:
            # 跳过空行和分隔线
            if not line.strip() or '=' in line or '-' in line:
                continue
                
            # 如果遇到IPv6路由表，停止处理
            if "IPv6 路由表" in line or "IPv6 Route Table" in line:
                break
                
            # 分割并格式化路由信息
            parts = line.split()
            if len(parts) >= 5:
                network = parts[0]
                netmask = parts[1]
                gateway = parts[2]
                interface = parts[3]
                metric = parts[4] if len(parts) > 4 else "N/A"
                
                # 格式化输出
                print(f"{network:<16} {netmask:<16} {gateway:<16} {interface:<16} {metric}")
                
        print("=" * 80)
        
    except Exception as e:
        print(f"显示路由配置时出错: {e}")

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--reset':
            reset_settings()
            sys.exit(0)
        elif sys.argv[1] == '--show':
            show_current_routes()
            sys.exit(0)
        else:
            print("无效的参数")
            print("可用参数:")
            print("  --reset  重置网络设置")
            print("  --show   显示当前路由配置")
            sys.exit(1)

    # 检查是否存在配置文件
    config = load_config()
    if config:
        print("\n发现已保存的配置：")
        print(f"你的网络连接: {config['user_connection']}")
        print(f"校园网络连接: {config['campus_connection']}")
        use_saved = input("\n是否使用已保存的配置？(y/n): ")
        if use_saved.lower() == 'y':
            user_connection = config['user_connection']
            campus_connection = config['campus_connection']
            user_gateway = config['user_gateway']
            campus_gateway = config['campus_gateway']
            
            print("\n开始设置跃点数...")
            set_metric(campus_connection, 'ipv6', 1)
            set_metric(user_connection, 'ipv4', 1)
            set_metric(user_connection, 'ipv6', 999)

            print("\n开始添加路由...")
            add_routes(campus_gateway, config['ip_cidrs'])
            print("\n路由配置完成！")
            sys.exit(0)

    connections = get_network_connections()
    if not connections:
        print("未找到网络连接，请检查系统设置。")
        exit(1)

    print("\n可用的网络连接:")
    print("序号    管理员状态     状态           接口名称")
    print("--------------------------------------------------")
    for i, conn in enumerate(connections, start=1):
        print(f"{i:<8}{conn['admin_status']:<12}{conn['conn_status']:<12}{conn['name']}")
    print("--------------------------------------------------")
    print("0. 取消设置")

    while True:
        try:
            user_choice = input("\n请选择你的网络连接的编号 (0-{0}): ".format(len(connections)))
            if user_choice == '0':
                print("已取消设置。")
                sys.exit(0)
                
            user_choice = int(user_choice) - 1
            if not (0 <= user_choice < len(connections)):
                print("输入的编号无效，请重新输入。")
                continue
                
            campus_choice = input("请选择校园网络连接的编号 (0-{0}): ".format(len(connections)))
            if campus_choice == '0':
                print("已取消设置。")
                sys.exit(0)
                
            campus_choice = int(campus_choice) - 1
            if not (0 <= campus_choice < len(connections)):
                print("输入的编号无效，请重新输入。")
                continue
                
            if user_choice == campus_choice:
                print("不能选择相同的网络连接，请重新选择。")
                continue
                
            user_connection = connections[user_choice]['name']
            campus_connection = connections[campus_choice]['name']
            break
        except ValueError:
            print("输入无效，请输入有效的编号。")

    print(f"\n选择的连接:")
    print("序号    管理员状态     状态           接口名称")
    print("--------------------------------------------------")
    print(f"1       {connections[user_choice]['admin_status']:<12}{connections[user_choice]['conn_status']:<12}{connections[user_choice]['name']}")
    print(f"2       {connections[campus_choice]['admin_status']:<12}{connections[campus_choice]['conn_status']:<12}{connections[campus_choice]['name']}")
    print("--------------------------------------------------")

    # 获取网关信息
    user_gateway = get_gateway(user_connection)
    campus_gateway = get_gateway(campus_connection)

    print(f"\n获取到的网关:")
    print(f"你的网络网关: {user_gateway}")
    print(f"校园网络网关: {campus_gateway}")

    # 显示完整的配置信息
    print("\n完整的配置信息:")
    print("=" * 50)
    print(f"你的网络连接: {user_connection}")
    print(f"校园网络连接: {campus_connection}")
    print(f"你的网络网关: {user_gateway}")
    print(f"校园网络网关: {campus_gateway}")
    print("\n将添加的路由规则:")
    for ip_cidr in IP_CIDRS:
        print(f"- {ip_cidr}")
    print("=" * 50)

    # 确认选择
    confirm = input("\n是否确认使用这些配置？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消设置。")
        sys.exit(0)

    if user_gateway and campus_gateway:
        print("\n开始设置跃点数...")
        set_metric(campus_connection, 'ipv6', 1)
        set_metric(user_connection, 'ipv4', 1)
        set_metric(user_connection, 'ipv6', 999)

        print("\n开始添加路由...")
        add_routes(campus_gateway, IP_CIDRS)
        
        # 保存配置
        save_config(user_connection, campus_connection, user_gateway, campus_gateway)
        print("\n配置已保存。")
        print("\n路由配置完成！")
    else:
        print("\n错误：无法获取网关信息，请检查网络连接配置。")
    