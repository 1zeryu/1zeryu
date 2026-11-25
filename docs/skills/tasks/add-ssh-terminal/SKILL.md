---
name: add-ssh-terminal
description: 为新服务器配置 VSCode/Trae 集成终端，打开终端即自动 SSH 登录并进入指定目录。当用户要求「新增一台服务器」「加一个远程终端」「打开终端自动连服务器」「修改服务器地址或端口」时使用。
---

# 新增 SSH 远程终端

在 VSCode / Trae 中新增一台服务器，需要在两个文件各加一段配置：SSH 配置负责「地址 + 端口 + 用户」，编辑器设置负责「打开终端时自动执行 ssh」。

两边靠 **别名** 关联，别名必须完全一致。

## 前置条件

- 本机有 `~/.ssh/config`（没有就新建）
- 已能通过网络访问目标服务器的 SSH 端口

## 步骤

### 1. 在 `~/.ssh/config` 中新增别名

```sshconfig
Host gpu02
  HostName 10.0.0.21
  Port 22
  User ubuntu
  ServerAliveInterval 30
```

- `Host` 后面是别名，推荐用字母、数字、下划线、连字符（如 `devserver`）。较新版本 OpenSSH 也支持直接写 `IP:端口` 并正确解析，但 `scp`、`rsync`、Remote-SSH 等工具对带冒号的主机名支持不一致，仍建议用纯字母别名，端口写在 `Port` 里
- 地址和端口的信息全部收敛到这里，以后服务器换 IP 只改这一处
- `ServerAliveInterval 30` 用于防止长时间无输出被网络设备断开

多台机器共用用户或端口时，用通配符合并：

```sshconfig
Host gpu*
  User ubuntu
  Port 22
  ServerAliveInterval 30

Host gpu01
  HostName 10.0.0.11

Host gpu02
  HostName 10.0.0.21
```

### 2. 配置免密登录

```bash
ssh-copy-id gpu02
```

执行后输入一次密码，之后不再需要密码。验证：

```bash
ssh -o BatchMode=yes gpu02 'echo ok'
```

### 3. 在编辑器设置中新增终端 profile

Trae：`~/Library/Application Support/Trae CN/User/settings.json`
VS Code：`~/Library/Application Support/Code/User/settings.json`（两个都用就都加）

在 `terminal.integrated.profiles.osx` 中加一项，key 与 SSH 别名相同：

```json
"terminal.integrated.profiles.osx": {
  "devserver": { "...": "..." },
  "gpu02": {
    "path": "/usr/bin/ssh",
    "args": ["-t", "gpu02", "cd /data/workspace && exec $SHELL -l"],
    "icon": "remote",
    "color": "terminal.ansiBlue"
  }
}
```

- `args` 第二个元素就是 SSH 别名，**必须与步骤 1 的 `Host` 一致**
- `cd /data/workspace` 是登录后停留的目录，不需要就用 `["-t", "gpu02"]`
- `icon` 可选 `remote` / `terminal`，`color` 用不同颜色区分不同机器
- 多个 profile 之间用逗号分隔

### 4. 选择终端

本项是**可选的**。不配置 `defaultProfile` 时，新终端仍是本地默认 shell（zsh），需要连服务器时从下拉菜单选择对应 profile，日常本地开发不受影响。

若希望打开终端就自动登录某台服务器，才需要按下面设置；它的值必须是**已存在的 profile 名字**，否则打开终端会报错。

```json
"terminal.integrated.defaultProfile.osx": "devserver"
```

只保留一个默认值，其他机器通过终端面板 `+` 右侧的下拉箭头切换，不必每次改配置。

### 5. 验证

- `ssh -G 别名 | grep -E '^(hostname|port|user) '`：检查别名解析出的地址、端口、用户是否正确
- 设置文件必须是合法 JSON：`python3 -m json.tool <settings.json 路径>`
- 新建终端，确认落在预期目录：`pwd`
- 回到本地终端：终端面板 `+` 下拉选 `zsh`

## 常见错误

| 现象 | 原因 |
| --- | --- |
| `could not resolve hostname 1.2.3.4:2222` | 客户端不支持 `主机:端口` 写法，或该 `Host` 段没匹配上；端口应写在 `Port` 里，别名用纯字母 |
| 打开终端报 profile 不存在 | `defaultProfile` 指向了已删除或改名的 profile |
| 改完配置没反应 | profile 只对新建终端生效，需关掉旧终端或重载窗口 |
| 免密不生效 | 未执行 `ssh-copy-id`，或服务器 `authorized_keys` 权限不对 |
| 登录后目录不对 | `cd` 路径不存在会停在 home；也可把 `cd` 写进服务器端 `~/.bashrc`，客户端 profile 只留 `["-t", "别名"]` |

## 修改已有服务器

- 换 IP / 端口：只改 `~/.ssh/config` 中该别名对应段落，profile 不用动
- 换别名：两处都要改，且保持一致
- 删除服务器：删掉 `Host` 段和对应 profile 项，并确认 `defaultProfile` 没有指向它
