import discord
from discord.ext import commands
from datetime import timedelta
import json
import os

# 直接指定頻道 ID
log_channel_id = 1250768134529482804  # 替換為你的頻道 ID

intents = discord.Intents.default()
intents.message_content = True  # 確保啟用消息內容意圖

bot = commands.Bot(command_prefix="?", intents=intents)

# 讀取配置文件
def load_config(filename='config.json'):
    with open(filename, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config


config = load_config()

# 管理員用戶 ID 列表，初始為空
admin_ids = [1049625838901010453, 805769171496337458, 786387622436143115]

# 讀取代碼庫
def load_codes(filename='code.txt'):
    codes = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(',', 1)
            code = parts[0]
            reward = parts[1] if len(parts) > 1 else "未指定獎勵"
            codes[code] = reward
    return codes

# 保存代碼庫
def save_codes(codes, filename='code.txt'):
    with open(filename, 'w', encoding='utf-8') as file:
        for code, reward in codes.items():
            file.write(f"{code},{reward}\n")

codes = load_codes()

# 讀取用戶兌換記錄
def load_user_data(filename='user_data.json'):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return {}

# 保存用戶兌換記錄
def save_user_data(user_data, filename='user_data.json'):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(user_data, file, ensure_ascii=False, indent=4)

user_data = load_user_data()

# 自定義權限檢查函數，檢查用戶是否在 allowed_users 列表中
def is_allowed_user(user_id):
    return user_id in allowed_users

# 自定義權限檢查函數，檢查用戶是否是管理員
def is_admin(ctx):
    return ctx.author.id in admin_ids

@bot.command()
async def redeem(ctx, code: str):
    user_id = str(ctx.author.id)
    if code in codes:
        if user_id not in user_data:
            user_data[user_id] = []
        if code not in user_data[user_id]:
            reward = codes[code]
            user_data[user_id].append(code)
            save_user_data(user_data)
            await ctx.send(f"兌換成功！你獲得了：{reward}")

            # 發送消息到指定的頻道
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(f"{ctx.author} 兌換了代碼 {code} 並獲得了：{reward}")
        else:
            await ctx.send("你已經兌換過此代碼。")
    else:
        await ctx.send("無效的代碼。")

@bot.command()
@commands.check(is_admin)
async def add(ctx, code: str, *, reward: str = "未指定獎勵"):
    if code in codes:
        await ctx.send(f"代碼 {code} 已經存在。")
    else:
        codes[code] = reward
        save_codes(codes)
        await ctx.send(f"已添加代碼 {code}，獎勵為：{reward}")

        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {ctx.author} 添加了代碼 {code}，獎勵為：{reward}")

@bot.command()
@commands.check(is_admin)
async def remove(ctx, code: str):
    if code in codes:
        del codes[code]
        save_codes(codes)
        await ctx.send(f"已移除代碼 {code}")

        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {ctx.author} 移除了代碼 {code}")
    else:
        await ctx.send(f"代碼 {code} 不存在。")
        
@bot.command()
@commands.check(is_admin)
async def list(ctx):
    if codes:
        code_list = "\n".join([f"{code}: {reward}" for code, reward in codes.items()])
        await ctx.send(f"目前所有代碼及其獎勵如下：\n{code_list}")
    else:
        await ctx.send("目前沒有可用的代碼。")

@bot.command()
@commands.check(is_admin)
async def admin_add(ctx, user_id: int):
    global admin_ids
    if user_id not in admin_ids:
        admin_ids.append(user_id)
        await ctx.send(f"已將用戶 {user_id} 添加為管理員。")
        
        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f" {ctx.author} 把{user_id}添加為管理員")
        
    else:
        await ctx.send(f"用戶 {user_id} 已經是管理員。")

@bot.command()
@commands.check(is_admin)
async def admin_remove(ctx, user_id: int):
    global admin_ids
    if user_id in admin_ids:
        admin_ids.remove(user_id)
        await ctx.send(f"已將用戶 {user_id} 從管理員中移除。")
        
        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f" {ctx.author} 把{user_id}從管理員中移除")
        
    else:
        await ctx.send(f"用戶 {user_id} 不是管理員。")
        
@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, user: discord.User, *, reason: str = None):
    try:
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"用戶 {user} 已被禁止，原因：{reason}")
        
        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {user} 已被禁止，原因：{reason}")
    except Exception as e:
        await ctx.send(f"禁止用戶失敗：{e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def kick(ctx, user: discord.User, *, reason: str = None):
    try:
        await ctx.guild.kick(user, reason=reason)
        await ctx.send(f"用戶 {user} 已被踢出，原因：{reason}")
        
        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {user} 已被踢出，原因：{reason}")
    except Exception as e:
        await ctx.send(f"踢出用戶失敗：{e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def timeout(ctx, user: discord.Member, minutes: int, notify: bool = False, *, reason: str = None):
    try:
        # 计算禁言的结束时间
        end_time = discord.utils.utcnow() + timedelta(minutes=minutes)
        await user.edit(timed_out_until=end_time)
        
        await ctx.send(f"用戶 {user} 已被禁言，禁言時長為 {minutes} 分鐘，原因：{reason}")

        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {user} 已被禁言，禁言時長為 {minutes} 分鐘，原因：{reason}")

        # 是否私訊通知用戶
        if notify:
            try:
                await user.send(f"你已被禁言，禁言時長為 {minutes} 分鐘，原因：{reason}")
            except Exception as e:
                await ctx.send(f"無法私訊通知用戶：{e}")
    except Exception as e:
        await ctx.send(f"禁言用戶失敗：{e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def untimeout(ctx, user: discord.Member, notify: bool = False, *, reason: str = None):
    try:
        # 解除禁言
        await user.edit(timed_out_until=None)
        
        await ctx.send(f"用戶 {user} 的禁言已被解除，原因：{reason}")

        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {user} 的禁言已被解除，原因：{reason}")

        # 是否私訊通知用戶
        if notify:
            try:
                await user.send(f"你的禁言已被解除，原因：{reason}")
            except Exception as e:
                await ctx.send(f"無法私訊通知用戶：{e}")
    except Exception as e:
        await ctx.send(f"解除禁言失敗：{e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def dm(ctx, user: discord.User, *, message: str):
    try:
        await user.send(message)
        await ctx.send(f"已成功向用戶 {user} 發送私訊。")

        # 發送消息到指定的頻道
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"用戶 {ctx.author} 向用戶 {user} 發送了私訊：{message}")
    except Exception as e:
        await ctx.send(f"無法向用戶發送私訊：{e}")
        
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # 將延遲轉換為整數毫秒
    await ctx.send(f"機器人延遲為 {latency} 毫秒")

@bot.command()
@commands.check(is_admin)
async def status(ctx, mode: str, *, message: str = None):
    activity = None
    if mode.lower() == 'playing':
        activity = discord.Game(name=message)
    elif mode.lower() == 'streaming':
        activity = discord.Streaming(name=message, url="http://twitch.tv/your_url")  # 替換為實際的流媒體 URL
    elif mode.lower() == 'listening':
        activity = discord.Activity(type=discord.ActivityType.listening, name=message)
    elif mode.lower() == 'watching':
        activity = discord.Activity(type=discord.ActivityType.watching, name=message)
    else:
        await ctx.send("無效的模式。有效模式為：playing正在玩, streaming正在串流, listening正在聽, watching正在看")
        return
    
    await bot.change_presence(activity=activity)
    await ctx.send(f"狀態已更改為 {mode} {message}")
    
@bot.command()
@commands.check(is_admin)
async def stats(ctx, state: str):
    status = None
    if state.lower() == 'online':
        status = discord.Status.online
    elif state.lower() == 'idle':
        status = discord.Status.idle
    elif state.lower() == 'dnd':
        status = discord.Status.do_not_disturb
    elif state.lower() == 'inv':
        status = discord.Status.invisible
    else:
        await ctx.send("無效的狀態。有效狀態為：online線上, idle閒置, dnd請勿打擾, inv隱形")
        return

    await bot.change_presence(status=status)
    await ctx.send(f"機器人狀態已更改為 {state}")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="代碼兌換"))
    print(f'已登入為 {bot.user}')


bot.run(config['token'])
