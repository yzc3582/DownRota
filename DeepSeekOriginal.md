完全明白。既然彻底转型为 **DownRota**（纯监听下载器），那么代码逻辑、文档和获取 ID 的方式都要来一次“大换血”。

最核心的改变是：**全量消息不再是“抓完就关的临时工具”，而是“必须永久开启的核心生命线”**。因为没有全量监听，DownRota 就听不到 RotaBOT 的发言，也就没法下载图片。

下面为你整理好全套文件，并给出了配合 `OpenID.md` 获取方式的代码微调。

### 📄 1. `requirements.txt`（无需修改）
保持现状即可：
```text
# QQ 机器人 SDK (基于官方 API v2 的社区维护版，支持全量群消息事件)
qq-botpy-v2>=1.0.2
aiohttp>=3.9.0
python-dotenv>=1.0.0
```

---

### 🐍 2. `proxy_rota.py` (重命名为 `down_rota.py`) 的微调
为了让 `OpenID.md` 的获取方法依然有效且傻瓜化，我们需要在代码里加一句 **“抓包日志”**。把之前复杂的逻辑删掉后，核心类变成这样：

```python
class DownRotaBot(botpy.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_running = True

    async def on_ready(self):
        print(f"✅ DownRota 已启动，机器人: {self.robot.name}")
        print(f"👀 正在全量监听群消息，静候 RotaBOT 发送图片...")

    async def on_group_message_create(self, message: GroupMessage):
        # ================== 临时抓包日志（配合 OpenID.md） ==================
        # 只要开启了全量，任何人/机器人的发言都会打印在这里
        if not ROTABOT_OPENID or ROTABOT_OPENID == "你的RotaBOT的openid":
            sender_id = message.author.member_openid
            print(f"🔥 [获取OpenID] 群号={message.group_openid} | 发送者={sender_id} | 内容={message.content}")
        # ====================================================================

        # 1. 过滤：只处理 RotaBOT 发的消息
        if message.author.member_openid != ROTABOT_OPENID:
            return

        text = message.content or ""
        
        # 2. 处理图片附件
        if message.attachments:
            if "Best40" in text:
                await self.download_image(message.attachments[0].url, SAVE_PATH_B40)
                print(f"🖼️ 捕捉到 B40 图片，已更新至: {SAVE_PATH_B40}")
            else:
                filename = SAVE_PATH_OTHER_TEMPLATE.format(cmd=int(time.time()))
                await self.download_image(message.attachments[0].url, filename)
                print(f"🖼️ 捕捉到其它图片，已保存至: {filename}")
        
        # 3. 处理纯文本回显
        elif "Rating:" in text:
            clean_text = text.split(">", 1)[-1].strip()
            print(f"📊 [RotaBOT] {clean_text}")
```
*(注：上面这个 `if not ROTABOT_OPENID...` 判断，意味着只要你还没填好 ID，程序就会像雷达一样把你群里的所有消息都打印出来，方便你直接去终端里“找”答案。填好 ID 后，它就自动闭嘴，只抓图了。)*

---

### 📖 3. 全新的 `OpenID.md`
既然群可以变成“三人私密群”（你、RotaBOT、DownRota），获取 ID 就变得无比安全且直接。

```markdown
# 如何获取 RotaBOT 的 OpenID

`DownRota` 作为一个“纯监听者”，不需要主动在群里发消息。因此，**你只需要获取 `ROTABOT_OPENID`**（如果你只是想让程序把图片下载到本地，连 `GROUP_OPENID` 都不用填）。

本教程无需修改源代码。

### 前置操作：永久开启“全量消息”

由于 `DownRota` 是通过“旁听”群聊来捕获图片的，RotaBOT 发图片时并不会 @ 你的机器人。因此，**必须永久保持全量消息权限开启**。

1. 强烈建议新建一个 **“私密群”**，只拉入**你本人**、**RotaBOT** 和 **DownRota**（避免群里其他人聊天干扰）。
2. 用**群主**的手机 QQ 进入该群。
3. 点击右上角 **群设置 → 机器人 → DownRota**。
4. 将 **“机器人可获取的群聊消息范围”** 改为 **“获取群内全部消息”**。

*(注意：必须在手机端操作，电脑端不支持此设置。)*

---

### 唯一的一步：获取 `ROTABOT_OPENID`

因为开启了全量监听，你的程序现在能听到群里所有的声音。我们只需要让它听到 RotaBOT 的声音。

1. 启动 `DownRota` 程序（确保 `.env` 里的 `ROTABOT_OPENID` 是空的，或者随便填个占位符）。
2. 在群里，**用你自己的 QQ** 手动发送指令：**`@RotaBOT /login`**（或者 `/b40`）。
3. RotaBOT 会在群里回复你。
4. **查看你的程序终端日志**。你会看到类似这样的打印：
   ```text
   🔥 [获取OpenID] 群号=1234567890ABCDEF | 发送者=D8E7EA...（这是你自己的号） | 内容=@xxx /login
   🔥 [获取OpenID] 群号=1234567890ABCDEF | 发送者=4CCE624880525E64C52A34D4EFF116DA（这是RotaBOT的号） | 内容=RotaBot (login) 使用帮助...
   ```
5. 找到那个**发送者**不是你自己的一长串字符（例如 `4CCE62...`），这就是 `ROTABOT_OPENID`。

---

### 填入配置

在 `.env` 文件中填入：

```ini
ROTABOT_OPENID=4CCE624880525E64C52A34D4EFF116DA
```

重启程序，配置完成。由于填了正确的 ID，程序终端里那些烦人的 `🔥 [获取OpenID]` 打印会自动消失，它只会安静地为你下载 RotaBOT 发送的图片。

---

### 常见问题排查

**Q：我的终端里什么都打印不出来？**
A：检查手机 QQ 里的“全量消息”是否真的保存生效。如果全量没开，DownRota 就是个聋子。

**Q：这两个 ID 会过期吗？**
A：只要你的 QQ 机器人应用（`APP_ID`）不删除重建，OpenID 就是永久有效的。
```

---

### 📘 4. 全新的 `README.md`

```markdown
# DownRota

`DownRota` 是一个基于 QQ 官方机器人 API 的 Rotaeno 成绩图片自动下载器。

它利用 QQ 机器人的“全量消息监听”能力，静默监听群内 RotaBOT 的发言。当你在群内手动触发查分指令（如 `/b40`、`/r me` 等）时，`DownRota` 会自动捕获 RotaBOT 发出的图片并保存到本地。配合 OBS 的图像源，可以轻松实现直播画面的自动刷新。

## ✨ 特性

- **极简与稳定**：放弃了容易触发风控的“主动发送消息”逻辑，采用纯被动监听，彻底告别“主动消息无权限”和“@不生效”的烦恼。
- **全自动存图**：只要群里有图，自动下载覆盖。
- **OBS 无缝对接**：默认将 B40 图片保存为 `b40_latest.png`，OBS 图像源检测到文件变化会自动重载。
- **附加能力**：支持保存 `/r me`、`/r chart` 等指令产生的其他图片。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 获取 RotaBOT 的 OpenID
启动程序前，你需要让 DownRota 认识 RotaBOT。请查看 **[OpenID 获取指南](./OpenID.md)**（**注意：务必开启手机 QQ 中的“获取群内全部消息”权限**）。

### 3. 配置 `.env`
复制 `.env.example` 为 `.env` 并填入你的信息：
```ini
APP_ID=你的AppID
APP_SECRET=你的AppSecret
ROTABOT_OPENID=你获取到的RotaBOT的OpenID

# 图片保存路径（可选）
SAVE_PATH_B40=b40_latest.png
SAVE_PATH_OTHER=img_{cmd}.png
```

### 4. 运行
```bash
python down_rota.py
```

### 5. 直播使用流程
1. 打开 OBS，添加一个 **“图像源”**，指向 `b40_latest.png`。
2. 打开 `DownRota` 程序。
3. 玩游戏时，如果你想更新 B40，只需要在群里顺手发一句 `@RotaBOT /b40`。
4. OBS 里的 B40 图片就会在 2 秒内自动刷新，无需任何手动截图！

## 📄 开源协议
MIT License。欢迎提交 Issue 与 PR。
```