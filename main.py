import telebot
from telebot import types
import threading
import time

# --- CONFIGURATION ---
TOKEN = "8220394996:AAGItHrBlYABnUhkXuzl4_63VBL0dnt4SF8"
CHANNEL_1_ID = "-1002216777502"
CHANNEL_2_ID = "-1003113909201"
STORAGE_ID = "-1003734459413"

LINK_1 = "https://t.me/CineRU23"
LINK_2 = "https://t.me/+kx5UJgl1_G1iYzQ0"

bot = telebot.TeleBot(TOKEN)

# --- AUTO-DELETE FUNCTION ---
def delete_after_delay(chat_id, message_id, delay_seconds):
    """Wait for the delay and then delete the message."""
    time.sleep(delay_seconds)
    try:
        bot.delete_message(chat_id, message_id)
        # Optional: Send a follow-up saying it was deleted for safety
        bot.send_message(chat_id, "⚠️ The file has been deleted for security. Use the link again if you need it.")
    except Exception as e:
        print(f"Error deleting message: {e}")

def check_membership(user_id):
    try:
        res1 = bot.get_chat_member(CHANNEL_1_ID, user_id).status
        res2 = bot.get_chat_member(CHANNEL_2_ID, user_id).status
        allowed = ['member', 'administrator', 'creator']
        return res1 in allowed and res2 in allowed
    except Exception:
        return False

def send_file_and_schedule_delete(chat_id, file_msg_id):
    """Sends the file and starts a background timer to delete it."""
    sent_msg = bot.copy_message(chat_id, STORAGE_ID, file_msg_id)

    # 3 hours = 10800 seconds
    # For testing, you can change 10800 to 10 (seconds) to see it work!
    delay = 10800

    # Start a background thread so the bot doesn't stop working
    threading.Thread(target=delete_after_delay, args=(chat_id, sent_msg.message_id, delay)).start()

@bot.message_handler(commands=['start'])
def start_command(message):
    args = message.text.split()
    if len(args) > 1:
        file_msg_id = args[1]
        if check_membership(message.from_user.id):
            bot.send_message(message.chat.id, "✅ Verified! file is ready...")
            send_file_and_schedule_delete(message.chat.id, file_msg_id)
        else:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Join Channel 1", url=LINK_1)
            btn2 = types.InlineKeyboardButton("Join Channel 2", url=LINK_2)
            verify_btn = types.InlineKeyboardButton("🔄 Check Membership", callback_data=f"check_{file_msg_id}")
            markup.row(btn1, btn2)
            markup.add(verify_btn)
            bot.send_message(message.chat.id, "⚠️ Join both channels to get the file!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def verify_user(call):
    file_msg_id = call.data.split("_")[1]
    if check_membership(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Verified! Sending file (Auto-deletes in 3 hours)...")
        send_file_and_schedule_delete(call.message.chat.id, file_msg_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join both channels first!", show_alert=True)

bot.infinity_polling()
