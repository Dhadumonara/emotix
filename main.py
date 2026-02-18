import telebot
from telebot import types
from flask import Flask
import threading
import time

# --- CONFIGURATION ---
TOKEN = "8220394996:AAGItHrBlYABnUhkXuzl4_63VBL0dnt4SF8"
CHANNEL_1_ID = "-1002216777502"
CHANNEL_2_ID = "-1003113909201"
STORAGE_ID = "-1003734459413"
LINK_1 = "https://t.me/CineRU23"
LINK_2 = "https://t.me/+kx5UJgl1_G1iYzQ0"
SITE_REDIRECT = "https://cineru.wuaze.com/index.php?i=2"

bot = telebot.TeleBot(TOKEN)

# --- FLASK WEB SERVER FOR KOYEB ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# --- AUTO-DELETE FUNCTION ---
def delete_after_delay(chat_id, message_id, delay_seconds):
    time.sleep(delay_seconds)
    try:
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "⚠️ The file has been deleted for security. Use the link again if you need it.")
    except telebot.apihelper.ApiTelegramException as e:
        print(f"[DELETE ERROR] Could not delete message for {chat_id}: {e}")

# --- CHECK CHANNEL MEMBERSHIP ---
def check_membership(user_id):
    try:
        res1 = bot.get_chat_member(CHANNEL_1_ID, user_id).status
        res2 = bot.get_chat_member(CHANNEL_2_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return res1 in allowed and res2 in allowed
    except telebot.apihelper.ApiTelegramException as e:
        print(f"[CHECK ERROR] Could not check membership for {user_id}: {e}")
        return False
    except Exception as e:
        return False

# --- SEND FILE AND AUTO-DELETE ---
def send_file_and_schedule_delete(chat_id, file_msg_id):
    try:
        sent_msg = bot.copy_message(chat_id, STORAGE_ID, file_msg_id)
        delay = 10800  # 3 hours
        threading.Thread(target=delete_after_delay, args=(chat_id, sent_msg.message_id, delay)).start()
    except telebot.apihelper.ApiTelegramException as e:
        print(f"[SEND ERROR] Could not send file to {chat_id}: {e}")

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start_command(message):
    args = message.text.split()

    # If user opens bot directly
    if len(args) == 1:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🌐 Open Website", url=SITE_REDIRECT)
        markup.add(btn)
        try:
            bot.send_message(
                message.chat.id,
                "⚠️ Please visit our website first before using the bot 👇",
                reply_markup=markup
            )
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[START ERROR] Could not message user {message.chat.id}: {e}")
        return

    # If user comes with file ID
    file_msg_id = args[1]
    if check_membership(message.from_user.id):
        try:
            bot.send_message(message.chat.id, "✅ Verified! File is ready...")
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[START SEND ERROR] Could not message {message.chat.id}: {e}")
        send_file_and_schedule_delete(message.chat.id, file_msg_id)
    else:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Join Channel 1", url=LINK_1)
        btn2 = types.InlineKeyboardButton("Join Channel 2", url=LINK_2)
        verify_btn = types.InlineKeyboardButton("🔄 Check Membership", callback_data=f"check_{file_msg_id}")
        markup.row(btn1, btn2)
        markup.add(verify_btn)
        try:
            bot.send_message(message.chat.id, "⚠️ Join both channels to get the file!", reply_markup=markup)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[JOIN MSG ERROR] Could not message {message.chat.id}: {e}")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def verify_user(call):
    file_msg_id = call.data.split("_")[1]
    if check_membership(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Verified! Sending file (Auto-deletes in 3 hours)...")
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[CALLBACK ERROR] Could not message/delete for {call.from_user.id}: {e}")
        send_file_and_schedule_delete(call.message.chat.id, file_msg_id)
    else:
        try:
            bot.answer_callback_query(call.id, "❌ Join both channels first!", show_alert=True)
        except telebot.apihelper.ApiTelegramException as e:
            print(f"[CALLBACK ALERT ERROR] {call.from_user.id}: {e}")

# --- START WEB SERVER + BOT ---
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000, threaded=True)).start()
time.sleep(2)
bot.infinity_polling()
