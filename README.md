# 校园网与个人网络路由配置助手

这是一个用于配置 Windows 系统网络路由的 Python 脚本，特别适用于需要同时使用东北大学校园网和普通网络的场景。  

使用本脚本后你可以：
- 同时以手机热点 + 有线校园网 或者 手机USB网络共享 + 无线校园网等方式连接网络，并且能正确的访问的校园内网或外网
- 访问ipv4地址时默认使用外部网络，访问ipv6时默认使用校园网络，用于使用ipv6免费的校园网
- 自带配置的NEU的内网路由，因此仍然可以正常访问内网


## 系统要求

- 操作系统：Windows 11 (version 24H2)
- Python 版本：Python 3.x
- 管理员权限：需要以管理员身份运行脚本

## 功能

- 自动检测系统网络连接
- 支持设置网络跃点数
- 支持添加校园网路由规则
- 配置信息本地保存
- 支持一键重置所有设置

## 使用方法

### 首次配置

1. 以**管理员身份**打开命令提示符或 PowerShell
2. 运行脚本：
   ```bash
   python app.py
   ```
3. 根据提示选择网络连接：
   - 选择你的普通网络连接
   - 选择校园网连接
4. 确认选择后，脚本会自动：
   - 设置网络跃点数
   - 添加校园网路由规则
   - 保存配置信息

### 重置设置

如果需要重置所有网络设置，运行：
```bash
python app.py --reset
```

这将：
- 恢复网络的自动跃点设置
- 删除所有添加的路由规则
- 删除保存的配置文件

## 修改配置

如果需要修改校园网路由规则，编辑 `app.py` 文件中的 `ip_cidrs` 列表：

```python
ip_cidrs = [
    "IP-CIDR,202.118.0.0/19,DIRECT",
    "IP-CIDR,202.199.0.0/20,DIRECT",
    # ... 其他路由规则
]
```

## 注意事项

1. 运行脚本需要管理员权限
2. 修改网络设置可能会影响网络连接，请谨慎操作
3. 建议在修改配置前备份重要数据
4. 如果遇到问题，可以使用 `--reset` 参数重置设置

## 文件说明

- `app.py`: 主程序文件
- `network_config.json`: 配置文件（自动生成，包含用户设置）
- `.gitignore`: Git 忽略文件配置

## 技术支持

如果在使用过程中遇到问题，请检查：
1. 是否以管理员身份运行脚本
2. 网络连接是否正常
3. 系统版本是否符合要求 