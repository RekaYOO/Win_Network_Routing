import subprocess
import re


def get_network_connections():
    try:
        result = subprocess.run(['netsh', 'interface', 'show', 'interface'], capture_output=True, text=True)
        output = result.stdout
        # 使用更精确的正则表达式来匹配网络接口名称
        connections = []
        for line in output.split('\n'):
            if '已启用' in line and '专用' in line:  # 只获取已启用且状态为专用的接口
                parts = line.split()
                if len(parts) >= 4:  # 确保有足够的字段
                    name = parts[3]  # 接口名称通常在第四个位置
                    if name and name != '管理员状态' and name != '类型':
                        connections.append(name)
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
        subprocess.run(['netsh', 'interface', 'ipv6' if protocol == 'ipv6' else 'ipv4', 'set', 'interface', connection,
                        f'metric={metric}', 'store=persistent'], check=True)
        print(f"已将 {connection} 的 {protocol} 跃点数设置为 {metric}")
    except subprocess.CalledProcessError as e:
        print(f"设置 {connection} 的 {protocol} 跃点数时出错: {e}")


def add_routes(gateway, ip_cidrs):
    for ip_cidr in ip_cidrs:
        ip, _ = ip_cidr.split(',')[1].split('/')
        cidr = ip_cidr.split(',')[1].split('/')[1]
        try:
            subprocess.run(['route', 'add', f'{ip}/{cidr}', gateway, '-p'], check=True)
            print(f"已添加路由: {ip}/{cidr} 到 {gateway}")
        except subprocess.CalledProcessError as e:
            print(f"添加路由 {ip}/{cidr} 到 {gateway} 时出错: {e}")


if __name__ == "__main__":
    connections = get_network_connections()
    if not connections:
        print("未找到网络连接，请检查系统设置。")
        exit(1)

    print("可用的网络连接:")
    for i, conn in enumerate(connections, start=1):
        print(f"{i}. {conn}")

    while True:
        try:
            user_choice = int(input("请选择用户网连接的编号: ")) - 1
            campus_choice = int(input("请选择校园网连接的编号: ")) - 1
            if 0 <= user_choice < len(connections) and 0 <= campus_choice < len(connections):
                user_connection = connections[user_choice]
                campus_connection = connections[campus_choice]
                break
            else:
                print("输入的编号无效，请重新输入。")
        except ValueError:
            print("输入无效，请输入有效的编号。")

    print(f"\n选择的连接:")
    print(f"用户网连接: {user_connection}")
    print(f"校园网连接: {campus_connection}")

    user_gateway = get_gateway(user_connection)
    campus_gateway = get_gateway(campus_connection)

    print(f"\n获取到的网关:")
    print(f"用户网网关: {user_gateway}")
    print(f"校园网网关: {campus_gateway}")

    if user_gateway and campus_gateway:
        print("\n开始设置跃点数...")
        set_metric(campus_connection, 'ipv6', 1)
        set_metric(user_connection, 'ipv4', 1)

        print("\n开始添加路由...")
        ip_cidrs = [
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
        add_routes(campus_gateway, ip_cidrs)
        print("\n路由配置完成！")
    else:
        print("\n错误：无法获取网关信息，请检查网络连接配置。")
    