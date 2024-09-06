import os
import sys
import requests
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram.constants import ChatAction

# 从环境变量读取配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BASE_URL = os.getenv('API_BASE_URL')
API_USERNAME = os.getenv('API_USERNAME')
API_PASSWORD = os.getenv('API_PASSWORD',)
STRATEGY_ID = int(os.getenv('STRATEGY_ID', '1'))  # STRATEGY_ID 默认为 '1'

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

# 处理图片消息
async def handle_photo(update: Update, context: CallbackContext):
    timestamped_print("收到图片消息")
    # 通知用户正在处理图片
    await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
    
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    file_path = 'temp.jpg'
    await file.download_to_drive(file_path)

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
            os.remove(file_path)  # 删除临时文件

# 处理非图片消息
async def handle_unsupported_message(update: Update, context: CallbackContext):
    timestamped_print("收到非图片消息，提示用户发送图片")
    await update.message.reply_text("不支持的文件类型，请发送图片。")

# 运行主程序
def main():
    timestamped_print("启动 Telegram Bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 注册处理图片消息的 handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # 注册处理非图片消息的 handler
    application.add_handler(MessageHandler(~filters.PHOTO, handle_unsupported_message))
    application.run_polling()

if __name__ == '__main__':
    main()