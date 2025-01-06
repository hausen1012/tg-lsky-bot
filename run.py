import os
import sys
import requests
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram.constants import ChatAction
from telegram.ext import CommandHandler

# 从环境变量读取配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')
API_USERNAME = os.getenv('API_USERNAME')
API_PASSWORD = os.getenv('API_PASSWORD',)
STRATEGY_ID = int(os.getenv('STRATEGY_ID', '1'))  # STRATEGY_ID 默认为 '1'
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')  # 允许的用户列表，逗号分隔

if ALLOWED_USERS == ['']:
    ALLOWED_USERS = []

# Token 保存路径
TOKEN_FILE = 'token.json'

# 检查必需的环境变量
required_env_vars = {
    'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
    'API_BASE_URL': API_BASE_URL,
    'API_USERNAME': API_USERNAME,
    'API_PASSWORD': API_PASSWORD
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        sys.exit(f"Error: {var_name} 环境变量未设置")

# 添加时间戳的 print 函数
def timestamped_print(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# 从文件中读取 Token
def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as file:
            data = json.load(file)
            return data.get('token')
    return None

# 将 Token 保存到文件
def save_token(token):
    with open(TOKEN_FILE, 'w') as file:
        json.dump({'token': token}, file)

# 生成新的 Token 并保存
def generate_token():
    response = requests.post(f"{API_BASE_URL}/tokens", json={
        "email": API_USERNAME,
        "password": API_PASSWORD
    })
    response.raise_for_status()
    token = response.json().get('data', {}).get('token')
    save_token(token)
    return token

# 获取有效的 Token，检查本地是否存在，如果不存在或失效则重新生成
def get_valid_token():
    token = load_token()
    if token:
        return token
    else:
        return generate_token()

# 上传图片并返回 URL
def upload_image(file_path, token):
    with open(file_path, 'rb') as file:
        files = {'file': file}
        headers = {
            'Authorization': f'Bearer {token}',
        }
        data = {
            'strategy_id': STRATEGY_ID
        }
        response = requests.post(f"{API_BASE_URL}/upload", headers=headers, data=data, files=files)

        # 如果返回 401，则 Token 失效，重新生成 Token
        if response.status_code == 401:
            token = generate_token()  # 重新生成 Token
            return upload_image(file_path, token)
        
        response.raise_for_status()
        return response.json().get('data', {}).get('links')

# 校验用户是否被允许
def is_user_allowed(user_id):
    # 如果 ALLOWED_USERS 为空，则所有用户都有权限
    return str(user_id) in ALLOWED_USERS or not ALLOWED_USERS

# 将mp4转为gif 
def mp42gif(in_file_path, out_file_path):
        ''''''
        palette_path = out_file_path.replace('.gif', '_palette.png')
        command = 'ffmpeg -y -i %(mp4)s -vf fps=10,scale=-1:-1:flags=lanczos,palettegen %(palette)s'
        command = command % {'mp4': in_file_path, 'palette': palette_path}
        status = os.system(command + ' > /dev/null 2>&1')
        if status != 0:
            os.path.isfile(palette_path) and os.remove(palette_path)
            raise Exception('ffmpeg error: execute gif => _palette.png')

        command = 'ffmpeg -y -i %(mp4)s -i %(palette)s -filter_complex "fps=10,scale=-1:-1:flags=lanczos[x];[x][1:v]paletteuse" %(gif)s'
        command = command % {'mp4': in_file_path, 'palette': palette_path, 'gif': out_file_path}
        status = os.system(command + ' > /dev/null 2>&1')
        os.path.isfile(palette_path) and os.remove(palette_path)
        if status != 0:
            raise Exception('ffmpeg error: execute .gif => .mp4')
        else:
            return out_file_path


# 处理图片消息
async def handle_message(update: Update, context: CallbackContext):
    #调试用的数据
    #update_json = json.dumps(update.to_dict(), ensure_ascii=False, indent=4)
    #timestamped_print(f"收到的 Update 数据: {update_json}")

    if not is_user_allowed(update.message.from_user.id):
        timestamped_print(f"{update.message.from_user.id} 用户未被授权访问")
        await update.message.reply_text("您没有权限使用此机器人。")
        return

    
    # 通知用户正在处理图片
    await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
    
    if update.message.photo:
        timestamped_print("收到图片消息")
        file_id = update.message.photo[-1].file_id
        file_path = 'temp.jpg'
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        timestamped_print("收到文件消息")
        file_id = update.message.document.file_id
        file_path = update.message.document.file_name
    elif update.message.animation:
        timestamped_print("收到gif消息")
        file_id = update.message.animation.file_id
        file_path = update.message.document.file_name
    else:
        timestamped_print("收到非图片消息")
        await update.message.reply_text("不支持的文件类型，请发送图片。")
        return

    file = await context.bot.get_file(file_id)
    await file.download_to_drive(file_path)

    # gif 需要特殊处理
    if update.message.animation:
        gif_path = file_path.replace('mp4', 'gif')
        mp42gif(file_path, gif_path)
        os.remove(file_path)
        file_path = gif_path

    token = get_valid_token()
    try:
        url_data = upload_image(file_path, token)
        
        # 如果获取到 URL 数据，进行美化输出
        if url_data:
            url = url_data.get('url')
            markdown = url_data.get('markdown')

            message = (
                f"🌐 **URL:** {url}\n"
                f"📝 **Markdown:** `{markdown}`"
            )
            timestamped_print(f"图床上传成功: {url}")
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("图片上传失败，未获取到 URL 数据。")
    except Exception as e:
        timestamped_print(f"上传图片时出错: {e}")
        await update.message.reply_text(f"上传图片时出错: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
async def start(update: Update, context: CallbackContext):
    user_first_name = update.message.from_user.first_name
    welcome_message = f"您好，我是一个图床机器人，{user_first_name}！请发送图片以获取上传链接。"
    await update.message.reply_text(welcome_message)

# 运行主程序
def main():
    timestamped_print("启动 Telegram Bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 注册 /start 命令的 handler
    application.add_handler(CommandHandler('start', start))
    # 注册处理消息的 handler
    application.add_handler(MessageHandler(None, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()

