import os
import json
import yaml
from typing import List, Dict, Union, Optional

def parse_clash_config(file_path: str) -> List[str]:
    """
    解析 Clash 配置文件，提取 IP-CIDR 规则
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'rules' not in config:
            print("未找到 rules 部分")
            return []
            
        ip_cidr_rules = []
        for rule in config['rules']:
            if isinstance(rule, str) and rule.startswith('IP-CIDR,') and rule.endswith(',DIRECT'):
                ip_cidr_rules.append(rule)
                
        return ip_cidr_rules
    except Exception as e:
        print(f"解析 Clash 配置文件时出错: {e}")
        return []

def parse_v2ray_config(file_path: str) -> List[str]:
    """
    解析 V2Ray 配置文件，提取 IP-CIDR 规则
    支持两种格式：
    1. 完整的 V2Ray 配置文件
    2. 仅包含路由规则的 JSON 文件
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        ip_cidr_rules = []
        
        # 检查是否是完整的 V2Ray 配置
        if 'routings' in config:
            for routing in config['routings']:
                if not routing.get('enabled', False):
                    continue
                    
                for rule in routing.get('rules', []):
                    if not rule.get('enabled', False):
                        continue
                        
                    if rule.get('outboundTag') != 'direct':
                        continue
                        
                    ip_list = rule.get('ip', [])
                    if not ip_list:
                        continue
                        
                    for ip in ip_list:
                        if ip.startswith('geoip:'):
                            continue
                        ip_cidr_rules.append(f"IP-CIDR,{ip},DIRECT")
        # 检查是否是仅包含路由规则的配置
        elif isinstance(config, list):
            for rule in config:
                if not rule.get('enabled', False):
                    continue
                    
                if rule.get('outboundTag') != 'direct':
                    continue
                    
                ip_list = rule.get('ip', [])
                if not ip_list:
                    continue
                    
                for ip in ip_list:
                    if ip.startswith('geoip:'):
                        continue
                    ip_cidr_rules.append(f"IP-CIDR,{ip},DIRECT")
        else:
            print("未找到有效的路由规则")
            return []
            
        return ip_cidr_rules
    except Exception as e:
        print(f"解析 V2Ray 配置文件时出错: {e}")
        return []

def export_clash_config(rules: List[str], output_path: str) -> bool:
    """
    导出 Clash 配置规则
    """
    try:
        config = {
            'rules': rules
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        print(f"导出 Clash 配置时出错: {e}")
        return False

def export_v2ray_config(rules: List[str], output_path: str) -> bool:
    """
    导出 V2Ray 配置规则
    """
    try:
        config = {
            'routings': [
                {
                    'remarks': 'Custom Rules',
                    'rules': [
                        {
                            'outboundTag': 'direct',
                            'ip': [rule.split(',')[1] for rule in rules],
                            'enabled': True
                        }
                    ],
                    'enabled': True
                }
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"导出 V2Ray 配置时出错: {e}")
        return False

def get_output_path(default_name: str, file_type: str) -> str:
    """
    获取输出文件路径，确保包含正确的文件扩展名
    """
    while True:
        path = input(f"请输入导出文件路径 (默认: {default_name}): ").strip()
        if not path:
            path = default_name
            
        # 确保路径是绝对路径
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # 检查是否是目录
        if os.path.isdir(path):
            path = os.path.join(path, default_name)
            
        # 确保文件扩展名正确
        if not path.endswith(file_type):
            path = f"{path}{file_type}"
            
        # 检查目录是否存在
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            create = input(f"目录 {dir_path} 不存在，是否创建？(y/n): ")
            if create.lower() == 'y':
                os.makedirs(dir_path, exist_ok=True)
            else:
                print("请重新输入有效的路径")
                continue
                
        return path

def get_file_path(prompt: str) -> str:
    """
    获取文件路径，支持相对路径和绝对路径
    """
    while True:
        path = input(prompt).strip()
        if not path:
            print("路径不能为空")
            continue
            
        # 处理相对路径
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # 检查文件是否存在
        if not os.path.exists(path):
            print(f"文件不存在: {path}")
            print("当前工作目录:", os.getcwd())
            continue
            
        return path

def main():
    print("1. 导入 Clash 配置")
    print("2. 导入 V2Ray 配置")
    print("3. 导出 Clash 配置")
    print("4. 导出 V2Ray 配置")
    
    choice = input("请选择操作 (1-4): ")
    
    if choice in ['1', '2']:
        # 导入配置
        file_path = get_file_path("请输入配置文件路径: ")
            
        if choice == '1':
            rules = parse_clash_config(file_path)
        else:
            rules = parse_v2ray_config(file_path)
            
        if not rules:
            print("未找到有效的 IP-CIDR 规则")
            return
            
        print(f"\n找到 {len(rules)} 条 IP-CIDR 规则:")
        for rule in rules:
            print(rule)
            
        save = input("\n是否保存这些规则到配置文件？(y/n): ")
        if save.lower() == 'y':
            # 确保配置目录存在
            os.makedirs('config', exist_ok=True)
            config_path = os.path.join('config', 'network_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['ip_cidrs'] = rules
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print("规则已保存到配置文件")
            
    elif choice in ['3', '4']:
        # 导出配置
        try:
            config_path = os.path.join('config', 'network_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            rules = config.get('ip_cidrs', [])
            
            if not rules:
                print("未找到可导出的规则")
                return
                
            if choice == '3':
                output_path = get_output_path('clash_rules.yaml', '.yaml')
                success = export_clash_config(rules, output_path)
            else:
                output_path = get_output_path('v2ray_rules.json', '.json')
                success = export_v2ray_config(rules, output_path)
                
            if success:
                print(f"配置已成功导出到: {output_path}")
            else:
                print("导出失败")
                
        except Exception as e:
            print(f"导出配置时出错: {e}")
            
    else:
        print("无效的选择")

if __name__ == "__main__":
    main() 