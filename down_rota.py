import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext
import aiohttp
import os
import sys
import time
from dotenv import load_dotenv
import botpy
from botpy.message import GroupMessage

# ==================== 加载配置 ====================
load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
ROTABOT_OPENID = os.getenv("ROTABOT_OPENID", "").strip()

# 图片保存配置
SAVE_PATH_B40 = os.getenv("SAVE_PATH_B40", "b40_latest.png")
# 其它图片的前缀，例如填 img_ ，最终会保存为 img_1730824321.png
SAVE_PATH_OTHER_PREFIX = os.getenv("SAVE_PATH_OTHER", "img_")

if not all([APP_ID, APP_SECRET]):
    print("❌ 错误: 缺少必要的环境变量配置（APP_ID / APP_SECRET）。请检查 .env 文件。")
    sys.exit(1)
# ================================================


class DownRotaBot(botpy.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_running = True

    async def on_ready(self):
        print(f"✅ DownRota 已启动，机器人: {self.robot.name}")
        if not ROTABOT_OPENID:
            print("⚠️ 尚未配置 ROTABOT_OPENID。请在群里发消息，通过终端打印的日志抓取！")
        else:
            print(f"👀 正在全量监听群消息，静候 RotaBOT ({ROTABOT_OPENID}) 发送图片...")

    async def on_group_message_create(self, message: GroupMessage):
        # ================== 核心功能：自动抓取 OpenID ==================
        # 如果没有配置 ROTABOT_OPENID，就把收到的所有消息打印出来，方便用户抓包
        if not ROTABOT_OPENID:
            sender_id = message.author.member_openid
            # 不打印自己机器人发的消息（如果机器人也开了全量，有时候会收到自己发的心跳等）
            if sender_id != self.robot.id:
                print(f"🔥 [抓包] 群号={message.group_openid} | 发送者={sender_id} | 内容={message.content}")
            return  # 未配置 ID 前，不执行后续下载逻辑
        # ================================================================

        # 1. 过滤：只处理 RotaBOT 发的消息
        if message.author.member_openid != ROTABOT_OPENID:
            return

        text = message.content or ""
        
        # 2. 处理图片附件
        if message.attachments:
            if "Best40" in text:
                success = await self.download_image(message.attachments[0].url, SAVE_PATH_B40)
                if success:
                    print(f"🖼️ 捕捉到 B40 图片，已更新至: {SAVE_PATH_B40}")
            else:
                timestamp = int(time.time())
                filename = f"{SAVE_PATH_OTHER_PREFIX}{timestamp}.png"
                success = await self.download_image(message.attachments[0].url, filename)
                if success:
                    print(f"🖼️ 捕捉到其它图片，已保存至: {filename}")
        
        # 3. 处理纯文本回显（如 /r update 的 Rating 提示）
        elif "Rating:" in text:
            clean_text = text.split(">", 1)[-1].strip()
            print(f"📊 [RotaBOT] {clean_text}")

    async def download_image(self, url, filename):
        try:
            # 自动创建文件夹（如果目录存在则不报错）
            dir_path = os.path.dirname(filename)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(filename, "wb") as f:
                            async for chunk in resp.content.iter_chunked(8192):
                                f.write(chunk)
                        return True
                    else:
                        print(f"❌ 图片下载失败 ({filename}): HTTP {resp.status}")
                        return False
        except Exception as e:
            print(f"❌ 图片下载失败 ({filename}): {e}")
            return False


# ==================== Tkinter GUI ====================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
bot_client = None

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("DownRota - Rotaeno 自动存图器")
        self.root.geometry("700x450")

        self.status_var = tk.StringVar(value="等待连接...")
        self.status_label = tk.Label(root, textvariable=self.status_var, fg="green", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, height=15, state="disabled", font=("Consolas", 10))
        self.log_area.pack(padx=10, pady=5, fill="both", expand=True)

        self.update_status()

    def log(self, msg):
        self.log_area.config(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def update_status(self):
        if bot_client:
            if not ROTABOT_OPENID:
                self.status_var.set("🟡 等待获取 OpenID (请在群里随意发条消息，查看日志)")
                self.status_label.config(fg="orange")  # 注意这里改成了 status_label
            else:
                self.status_var.set("🟢 监听中 (请在群里手动 @RotaBOT 触发图片)")
                self.status_label.config(fg="green")   # 注意这里改成了 status_label
        self.root.after(500, self.update_status)

def start_bot():
    global bot_client
    intents = botpy.Intents(public_messages=True)
    bot_client = DownRotaBot(intents=intents)

    async def _run():
        def custom_print(*args, **kwargs):
            msg = " ".join(map(str, args))
            app.log(msg)
            # 保留终端打印，方便调试
            print_orig(msg)
            
        # 备份原始 print，防止无限递归
        print_orig = __builtins__.print
        __builtins__.print = custom_print
        
        try:
            await bot_client.start(appid=APP_ID, secret=APP_SECRET)
        except Exception as e:
            custom_print(f"❌ 机器人启动失败: {e}")

    asyncio.run_coroutine_threadsafe(_run(), loop)

if __name__ == "__main__":
    threading.Thread(target=loop.run_forever, daemon=True).start()
    
    root = tk.Tk()
    app = App(root)
    
    root.after(500, start_bot)
    
    root.mainloop()