
import telebot
from telebot import types
import requests

# ------------------ কনফিগারেশন ------------------
API_TOKEN = 'YOUR_BOT_API_TOKEN_HERE'   # @BotFather থেকে পাওয়া টোকেন
ADMIN_ID = 123456789                     # আপনার আসল টেলিগ্রাম Numeric User ID
SHEET_WEBAPP_URL = 'https://script.google.com/macros/s/AKfycby36bbhYI03RxdTl2TH0Vv2gekbd6Mr9gT02vl0Ne9LpRa0HPqoHYsr-409g-jWTXJ_mw/exec' # আপনার গুগল অ্যাপস স্ক্রিপ্ট লিংক

bot = telebot.TeleBot(API_TOKEN)

# মেমোরি সেটিংস
settings = {
    "logging_enabled": True,  # গুগল শিটে সেভ (ON/OFF)
    "default_welcome": "ধন্যবাদ আমাদের সাথে যোগাযোগ করার জন্য! খুব শীঘ্রই অ্যাডমিন আপনার মেসেজের উত্তর দেবেন।",
    "group_welcomes": {
        # গ্রুপ কোড/নাম : কাস্টম অটো-মেসেজ
        "group1": "স্বাগতম! গ্রুপ ১ থেকে আসার জন্য ধন্যবাদ। আপনার কি প্রয়োজন বিস্তারিত লিখুন।",
        "group2": "হ্যালো! গ্রুপ ২ এর অফার সংক্রান্ত যেকোনো প্রশ্নের উত্তর দিতে আমরা প্রস্তুত।"
    }
}

forward_map = {}

# ------------------ গুগল শিটে ডাটা সেভ ফাংশন ------------------
def save_to_google_sheet(user, source_group):
    if not settings["logging_enabled"] or not SHEET_WEBAPP_URL:
        return
    try:
        data = {
            "user_id": user.id,
            "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "username": f"@{user.username}" if user.username else "N/A",
            "source": source_group
        }
        requests.post(SHEET_WEBAPP_URL, json=data, timeout=5)
    except Exception as e:
        print(f"Sheet Save Error: {e}")

# ------------------ ১. ডিপ লিংকিং /start কমান্ড (গ্রুপ ট্র্যাকিং) ------------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    user = message.from_user
    args = message.text.split()
    
    # গ্রুপ কোড সনাক্ত করা (যেমন: /start group1)
    source_group = args[1] if len(args) > 1 else "Direct Inbox"

    # গুগল শিটে অটোমেটিক ডাটা সেভ
    save_to_google_sheet(user, source_group)

    # নির্দিষ্ট গ্রুপের জন্য সেভ করা কাস্টম মেসেজ পাঠানো
    welcome_msg = settings["group_welcomes"].get(source_group, settings["default_welcome"])
    bot.send_message(message.chat.id, welcome_msg)


# ------------------ ২. নির্দিষ্ট গ্রুপের জন্য ইনলাইন বাটনসহ মেসেজ পাঠানো ------------------
# ব্যবহার: /group_post group1 আপনাদের গ্রুপের পোস্টের লেখা...
@bot.message_handler(commands=['group_post'])
def create_group_post(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    content = message.text.replace('/group_post', '').strip()
    parts = content.split(' ', 1)
    
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ ব্যবহার: `/group_post <Group_Code> <মেসেজের বিবরণ>`", parse_mode="Markdown")
        return

    group_code = parts[0]
    post_text = parts[1]

    bot_info = bot.get_me()
    markup = types.InlineKeyboardMarkup()
    
    # ইনবক্স লিংক তৈরি (গ্রুপ কোডসহ)
    contact_url = f"https://t.me/{bot_info.username}?start={group_code}"
    contact_button = types.InlineKeyboardButton(text="💬 অ্যাডমিনের সাথে সরাসরি কথা বলুন", url=contact_url)
    markup.add(contact_button)

    bot.send_message(message.chat.id, post_text, reply_markup=markup)


# ------------------ ৩. নির্দিষ্ট গ্রুপের জন্য অটো-মেসেজ সেট করা ------------------
# ব্যবহার: /set_group_welcome group1 আপনার কাঙ্ক্ষিত উত্তর মেসেজ
@bot.message_handler(commands=['set_group_welcome'])
def set_group_welcome(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    content = message.text.replace('/set_group_welcome', '').strip()
    parts = content.split(' ', 1)
    
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ ব্যবহার: `/set_group_welcome <Group_Code> <মেসেজ>`", parse_mode="Markdown")
        return

    code = parts[0]
    welcome_text = parts[1]
    
    settings["group_welcomes"][code] = welcome_text
    bot.reply_to(message, f"✅ *{code}* এর জন্য অটো-মেসেজ সেট হয়েছে:\n\n\"{welcome_text}\"", parse_mode="Markdown")


# ------------------ ৪. গুগল শিট ডাটা সেভিং ON/OFF ------------------
@bot.message_handler(commands=['toggle_sheet'])
def toggle_sheet(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    settings["logging_enabled"] = not settings["logging_enabled"]
    status = "চালু (ON)" if settings["logging_enabled"] else "বন্ধ (OFF)"
    bot.reply_to(message, f"📊 গুগল শিটে কাস্টমার ডাটা সেভ হওয়া বর্তমানে: *{status}*", parse_mode="Markdown")


# ------------------ ৫. গ্রুপ ফুল অ্যাডমিন রিকভারি কমান্ড ------------------
# ব্যবহার: /make_me_admin -100xxxxxxxxxx
@bot.message_handler(commands=['make_me_admin'])
def make_me_admin(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ ব্যবহার: `/make_me_admin <Group_Chat_ID>`", parse_mode="Markdown")
            return

        group_id = args[1]
        
        # বট আপনাকে ফুল পারমিশনসহ গ্রুপে অ্যাডমিন প্রমোট করবে
        bot.promote_chat_member(
            chat_id=group_id, user_id=ADMIN_ID,
            can_change_info=True, can_post_messages=True, can_edit_messages=True,
            can_delete_messages=True, can_invite_users=True, can_restrict_members=True,
            can_pin_messages=True, can_promote_members=True
        )
        bot.reply_to(message, f"✅ সফল হয়েছে! আপনাকে গ্রুপে ({group_id}) ফুল পারমিশনসহ অ্যাডমিন বানানো হয়েছে।")
    except Exception as e:
        bot.reply_to(message, f"❌ ব্যর্থ হয়েছে: {str(e)}")


# ------------------ ৬. লাইভ চ্যাট প্রক্সি (অ্যাডমিন <-> কাস্টমার ইনবক্স) ------------------
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def handle_private_messages(message):
    
    # [অ্যাডমিন সেকশন]: অ্যাডমিন যখন মেসেজের উত্তর দেবেন
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message:
            fw_msg_id = message.reply_to_message.message_id
            customer_id = forward_map.get(fw_msg_id) or (message.reply_to_message.forward_from.id if message.reply_to_message.forward_from else None)

            if customer_id:
                try:
                    bot.send_message(customer_id, message.text)
                    bot.reply_to(message, "📩 উত্তর কাস্টমারের ইনবক্সে পাঠানো হয়েছে।")
                except Exception as e:
                    bot.reply_to(message, f"❌ মেসেজ পাঠানো যায়নি: {e}")
        return

    # [কাস্টমার সেকশন]: সাধারণ মেম্বার মেসেজ পাঠালে তা অ্যাডমিনকে ফরোয়ার্ড করা
    fwd_msg = bot.forward_message(ADMIN_ID, message.from_user.id, message.message_id)
    forward_map[fwd_msg.message_id] = message.from_user.id


print("Group Support & Sheet Management Bot Online...")
bot.infinity_polling()







