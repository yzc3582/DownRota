# DownRota

`DownRota` 是一个基于 QQ 官方机器人 API 的 RotaBOT 图片消息自动下载器。

它利用 QQ 机器人的“全量消息监听”能力，静默监听群内 RotaBOT 的发言。当你在群内手动触发查分指令（如 `/b40`、`/r me` 等）时，`DownRota` 会自动捕获 RotaBOT 发出的图片并保存到本地。配合 OBS 的图像源，可以轻松实现直播画面的自动刷新。

## ✨ 特性

- **极简与稳定**：放弃了容易触发风控的“主动发送消息”逻辑，采用纯被动监听，彻底告别“主动消息无权限”和“@不生效”的烦恼。
- **全自动存图**：只要群里有图，自动下载覆盖（b40）或按时间戳保存（其它）。
- **OBS 无缝对接**：默认将 B40 图片保存为 `b40_latest.png`，OBS 图像源检测到文件变化会自动重载。
- **附加能力**：支持保存 `/r me`、`/r chart` 等指令产生的其他图片（目前无法区分除 `/b40` 的命令来源）。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 获取 RotaBOT 的 OpenID
启动程序前，你需要让 DownRota 认识 RotaBOT。请查看 **[OpenID 获取指南](./OpenID.md)**（**注意：务必开启手机 QQ 中的“获取群内全部消息”权限**）。

### 3. 配置 `.env`
复制 `.env.example` 为 `.env` 并根据注释填空。

### 4. 运行
```bash
python down_rota.py
```

### 5. 直播使用流程
1. 打开 OBS，添加一个 **“图像源”**，指向 `b40_latest.png`。
2. 打开 `DownRota` 程序。
3. 玩游戏时，如果你想更新 B40，只需要在群里顺手发一句 `@RotaBOT /b40`。（记得先 /r update）
4. OBS 里的 B40 图片就会在 2 秒内自动刷新，无需手动保存！

## 📄 开源协议
MIT License。欢迎提交 Issue 与 PR。
