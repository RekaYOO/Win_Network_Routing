# NEU校园网路由配置助手

这是一个自动可以配置 Windows 系统网络路由的 Python 脚本，特别适用于需要同时使用东北大学校园网和普通网络的场景。  

使用本脚本后你可以：
- 同时以手机热点 + 有线校园网 或者 手机USB网络共享 + 无线校园网等方式连接网络，并且能正确的访问的校园内网或外网
- 访问ipv4地址时默认使用外部网络，访问ipv6时默认使用校园网络，用于使用ipv6免费的校园网
- 自带配置的NEU的内网路由，因此仍然可以正常访问内网
- 支持从 V2Ray 和 Clash 配置文件中导入路由规则


## 系统要求

- 操作系统：仅测试过Windows 11 (version 24H2)
- Python 版本：Python 3.x
- 管理员权限：需要以管理员身份运行脚本
- 依赖库：pyyaml (用于解析 Clash 配置文件)

## 功能

- 自动检测系统网络连接
- 支持设置网络跃点数
- 支持添加校园网路由规则
- 配置信息本地保存
- 支持一键重置所有设置
- 支持从 V2Ray 和 Clash 配置文件中导入路由规则
- 支持导出路由规则到 V2Ray 和 Clash 格式

## 使用方法

### 安装和配置

> 仅当你需要使用config_parser来导入或导出v2ray和clash路由规则时，才需要第2和第3步

1. 克隆仓库：
   ```bash
   git clone https://github.com/RekaYOO/Win_Network_Routing.git
   cd Win_Network_Routing
   ```

2. 创建并激活虚拟环境（推荐）：
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 首次配置

1. 以**管理员身份**打开命令提示符或 PowerShell
2. 进入项目目录并激活虚拟环境（如果使用）：
   ```bash
   cd Win_Network_Routing
   .\venv\Scripts\activate  # Windows，如果使用虚拟环境
   ```
3. 运行脚本：
   ```bash
   python app.py
   ```
4. 根据提示选择网络连接：
   - 选择你的普通网络连接
   - 选择校园网连接
5. 确认选择后，脚本会自动：
   - 设置网络跃点数
   - 添加校园网路由规则
   - 保存配置信息到 `config/network_config.json`

### 重置设置

如果需要重置所有网络设置，运行：
```bash
python app.py --reset
```

这将：
- 恢复网络的自动跃点设置
- 删除所有添加的路由规则
- 保留配置文件以便下次使用

### 再次配置
1. 以**管理员身份**打开命令提示符或 PowerShell
2. 进入项目目录并激活虚拟环境（如果使用）：
   ```bash
   cd Win_Network_Routing
   .\venv\Scripts\activate  # Windows，如果使用虚拟环境
   ```
3. 运行脚本：
   ```bash
   python app.py
   ```
4. 你可以选择使用旧的配置文件，或是重新配置

### 导入/导出路由规则

使用 `config_parser.py` 可以导入和导出路由规则：

1. 运行配置解析器：
   ```bash
   python config_parser.py
   ```

2. 导入 V2Ray 规则：
   - 在 v2rayN 中导出配置文件，或将将规则集导出至剪贴板而后保存为 JSON 文件
   - 选择选项 2，然后选择导出的配置文件
   - 程序会自动解析并显示找到的 IP-CIDR 规则
   - 选择是否保存到配置文件

3. 导出 V2Ray 规则：
   - 选择选项 4
   - 输入导出文件路径
   - 打开导出的 JSON 文件，复制 `rules` 数组中的内容
   - 在 v2rayN 中从剪贴板导入规则集

4. 导入 Clash 规则：
   - 选择选项 1
   - 选择 Clash 配置文件
   - 程序会自动解析并显示找到的 IP-CIDR 规则
   - 选择是否保存到配置文件

5. 导出 Clash 规则：
   - 选择选项 3
   - 输入导出文件路径
   - 导出的 YAML 文件可以直接用于 Clash 配置

## 修改配置

如果需要修改校园网路由规则，编辑 `app.py` 文件中的 `ip_cidrs` 列表：

```python
ip_cidrs = [
    "IP-CIDR,202.118.0.0/19,DIRECT",
    "IP-CIDR,202.199.0.0/20,DIRECT",
    # ... 其他路由规则
]
```

尽管只是用路由地址，但是为了明确目的和方便后期还未增加的一些功能，所以这么配置..

## 注意事项

1. 运行脚本需要管理员权限
2. 修改网络设置可能会影响网络连接，请谨慎操作
3. 建议在修改配置前备份重要数据
4. 如果遇到问题，可以使用 `--reset` 参数重置设置
5. 导入 V2Ray 规则时，确保配置文件格式正确
6. 导出 V2Ray 规则后，需要手动复制 `rules` 数组内容到剪贴板
7. 配置文件保存在 `config` 目录下，该目录不会被 Git 追踪

## 文件说明

- `app.py`: 主程序文件
- `config_parser.py`: 路由规则导入导出工具
- `config/`: 配置文件目录
  - `network_config.json`: 配置文件（自动生成，包含用户设置）
- `.gitignore`: Git 忽略文件配置
- `requirements.txt`: 项目依赖文件

## 技术支持

如果在使用过程中遇到问题，请检查：
1. 是否以管理员身份运行脚本
2. 网络连接是否正常
3. 系统版本是否符合要求
4. 是否已安装所需依赖库（运行 `pip install -r requirements.txt`） 