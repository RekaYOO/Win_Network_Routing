# Windows 网络路由配置工具

这是一个用于管理 Windows 系统网络路由配置的 Python 工具。它可以帮助你轻松地配置和管理网络路由规则，特别适用于需要同时使用校园网和用户网的用户。

## 功能特点

- 自动检测和显示所有可用的网络连接
- 支持配置校园网和用户网的跃点数
- 支持添加和管理自定义路由规则
- 支持重置所有设置到默认值
- 支持测试路由规则格式
- 配置文件持久化存储
- 详细的日志记录

## 系统要求

- Windows 10 或更高版本
- Python 3.6 或更高版本
- 管理员权限

## 安装

1. 克隆或下载本项目到本地
2. 确保已安装 Python 3.6 或更高版本
3. 以管理员身份运行命令提示符或 PowerShell

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

1. 运行程序：
```bash
python app.py
```

2. 程序会显示所有可用的网络连接，并提示你选择：
   - 用户网连接编号
   - 校园网连接编号

3. 选择完成后，程序会自动：
   - 设置校园网 IPv6 跃点数为 1
   - 设置用户网 IPv4 跃点数为 1
   - 添加配置文件中的路由规则

### 命令行参数

- `--list`: 列出所有网络连接
```bash
python app.py --list
```

- `--routes`: 显示当前路由表
```bash
python app.py --routes
```

- `--user <编号>`: 指定用户网连接编号
- `--campus <编号>`: 指定校园网连接编号
```bash
python app.py --user 1 --campus 2
```

- `--config <路径>`: 指定配置文件路径
```bash
python app.py --config custom_routes.json
```

- `--reset`: 重置所有设置到默认值
```bash
python app.py --reset
```

- `--test`: 测试路由规则格式
```bash
python app.py --test
```

### 配置文件

配置文件默认为 `routes.json`，格式如下：

```json
{
    "routes": [
        "IP-CIDR,192.168.1.0/24,DIRECT",
        "IP-CIDR,10.0.0.0/8,DIRECT"
    ],
    "default_metrics": {
        "campus": {
            "ipv6": 1
        },
        "user": {
            "ipv4": 1
        }
    }
}
```

- `routes`: 路由规则列表，每条规则格式为 "IP-CIDR,IP/MASK,DIRECT"
- `default_metrics`: 默认跃点数设置
  - `campus.ipv6`: 校园网 IPv6 跃点数
  - `user.ipv4`: 用户网 IPv4 跃点数

### 测试路由规则

使用 `--test` 参数可以测试配置文件中的路由规则格式是否正确：

```bash
python app.py --test
```

如果所有规则格式正确，会显示：
```
正在测试路由规则格式...
所有路由规则格式正确
```

如果发现错误，会显示具体的错误信息，例如：
```
正在测试路由规则格式...
发现以下错误:
  - 规则 1: 格式错误，应为 'IP-CIDR,IP/MASK,DIRECT'
  - 规则 2: IP地址格式错误，缺少掩码
  - 规则 3: 掩码值错误，应在 0-32 之间
```

## 注意事项

1. 需要管理员权限运行
2. 配置文件中的路由规则格式必须正确
3. 建议在修改配置前先测试规则格式
4. 如果遇到问题，可以使用 `--reset` 参数重置所有设置

## 日志

程序运行日志保存在 `network_routing.log` 文件中，包含详细的操作记录和错误信息。

## 许可证

MIT License 