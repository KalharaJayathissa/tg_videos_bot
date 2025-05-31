import os
import logging
import json
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes,MessageHandler, filters,ConversationHandler
)

# === CONFIGURATION ===
BOT_TOKEN = '7410380924:AAE7QggH2U57JOfm7Bo_7LjNC-SQccMV0L4'  # Replace with your bot token
ADMIN_ID = 1056939282  # Replace with your Telegram user ID
VIDEO_FILE = "videos.json"
STATS_FILE = "video_stats.json"
STICKER_FILE = "stickers.json"

# === Messages ===
A = "බලමු බලමු මචන්."
B ="වැලක් බලමුද මචන්!"
C = "ඉවරයි පකයො, පය්ය තියෙද උබේ තාම?"
D = "තව වැලක් දියන්කො මචන්."
E = "නැග්ගෙ නැනෙ මචන්."
F = "තිබ්බ සේරම ඉවරයි හුත්තෝ, ඔච්චර බලලත් නගින් නැත්තන් කොල්ලො ගහපන් ගිහින් කැරියා"
G = "මෙන්න මචන් තව වැල් හතරක්."
H = "විඩියෝ එක දාගත්ත මචන්. බොහොම ස්තූතී."

# sticker
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.effective_user.id != ADMIN_ID:
    #     return

    sticker = update.message.sticker
    if not sticker:
        return

    stickers = load_json(STICKER_FILE)
    

    if not isinstance(stickers, list):
        stickers = []

    if sticker.file_id not in stickers:
        stickers.append(sticker.file_id)
        save_json(STICKER_FILE, stickers)
        await update.message.reply_text("✅ Sticker saved!")
    else:
        await update.message.reply_text("ℹ️ Sticker already exists.")


# === HELPER FUNCTIONS ===
def load_json(file):
    if not os.path.exists(file):
       
            return {}
    with open(file, 'r') as f:
        return json.load(f)

def load_txt_as_list(file):
    if not os.path.exists(file):

        return []

    with open(file,'r') as f:
        return [line.strip() for line in f if line.strip()]


def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def update_video_stats(file_id, user_id):
    stats = load_json(STATS_FILE)
    if file_id not in stats:
        stats[file_id] = {"send_count": 0, "users": []}
    stats[file_id]["send_count"] += 1
    if user_id not in stats[file_id]["users"]:
        stats[file_id]["users"].append(user_id)
    save_json(STATS_FILE, stats)

def update_valid_users(user):
    valid_users =load_json("valid_users.json")
    valid_users[user.id ] = user.username
    save_json("valid_users.json", valid_users)

def update_user_info(user):
    users_info = load_json("users_info.json")
    if str(user.id) not in users_info:
        users_info[str(user.id)] = {
            "accesesed times": 1,
            "user name": user.username,
            "full_name": user.full_name,
            "link": user.link,
            "last access": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
    else:
        users_info[str(user.id)]["accesesed times"] += 1
        users_info[str(user.id)]["last access"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    users_info[str(user.id)]["bot access"] = True if str(user.id) in load_json("valid_users.json") else False
    save_json("users_info.json", users_info)


# def valid_users()

user_video_progress = {}

def load_stickers():
    if not os.path.exists(STICKER_FILE):
        return []
    with open(STICKER_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# def shuffle_videos():
#     videos = load_json(VIDEO_FILE)
#     random.shuffle(videos)
#     save_json(VIDEO_FILE, videos)

#MOVE TO THE TOP LATER
INVALID_USER_MESSAGE = "❌ මචන් උඹට ඇක්සස් නෑ. උබේ නම කියපන් බලන්න පොඩ්ඩක්. (Eg: Saman)"



# === COMMANDS ===

async def starting_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(A, callback_data="send_more")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(B, reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_video_progress[update.effective_user.id] = 0
    print(update.effective_user.username," : ",time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    valid_users = set(load_json("valid_users.json"))
    update_user_info(update.effective_user)  # Update user info in users_info.json
    if str(update.effective_user.id) not in valid_users:
        await update.message.reply_text(INVALID_USER_MESSAGE)
        return 1
    

    else:
        await starting_button(update, context)
        # keyboard = [[InlineKeyboardButton(A, callback_data="send_more")]]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # await update.message.reply_text(B, reply_markup=reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.effective_user.id != ADMIN_ID:
    #     return
    stats = load_json(STATS_FILE)
    if not stats:
        await update.message.reply_text("📊 No stats yet.")
        return
    msg = "📊 Video Stats:\n\n"
    for i, (fid, data) in enumerate(stats.items(), 1):
        msg += f"{i}. File ID: `{fid[:10]}...`\n"
        msg += f"   Sent: {data['send_count']} times\n"
        msg += f"   Users: {len(data['users'])} unique\n\n"
        await update.message.reply_text(msg, parse_mode='Markdown')
        msg =""  # Reset for next iteration

# === VIDEO SENDING ===
async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    chat_id = user.id

    # load and validate videos
    videos_update = load_json(VIDEO_FILE) #to update the dictionary
    videos = list(load_json(VIDEO_FILE))
    random.shuffle(videos)  # Shuffle the videos list
    start = user_video_progress.get(user_id, 0)
    end = start + 4
    chunk = videos[start:end]

    # if none left
    if not chunk:
        await context.bot.send_message(chat_id=chat_id, text=C)
        return
    
    # Send a message prior to the batch
    await context.bot.send_message(chat_id=chat_id, text= G )

    # send the batch
    for file_id in chunk:
        await context.bot.send_video(chat_id=chat_id, video=file_id)
        update_video_stats(file_id, user_id)
        videos_update[file_id]["watched_by"].append((user.username, user.full_name, user.link))  # Add user info to watched_by
    
    user_video_progress[user_id] = end
    save_json(VIDEO_FILE, videos_update)  # Save the updated video data
    # —— load/validate stickers ONCE ——
    stickers = load_stickers()
    if not isinstance(stickers, list):
        stickers = []
    # filter out any bad entries
    stickers = [s for s in stickers if isinstance(s, str) and s]
    # send one random sticker if possible
    
    await context.bot.send_sticker(chat_id=chat_id, sticker=random.choice(stickers))

    # more videos?
    if end < len(videos):
        #,[InlineKeyboardButton("test1", callback_data="test1")]
      
        
        keyboard = [[InlineKeyboardButton(D, callback_data="send_more")],[InlineKeyboardButton("test", callback_data="send_more")]]
        markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text=E, reply_markup=markup)
        #keyboard = [[InlineKeyboardButton("test,callback_data ")]]
    else:
        await context.bot.send_message(chat_id=chat_id, text=F)


# === CALLBACK HANDLER ===
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
    await send_videos(update, context)


# Add videos
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.effective_user.id != ADMIN_ID:
    #     return  # Only admin can add videos
    
    video = update.message.video
    if not video:
        return
    
    file_id = video.file_id
    videos = load_json(VIDEO_FILE)
    if not isinstance(videos, dict):
        videos = {}
    
    if file_id not in videos:
        
        videos[file_id] = {
            "video no": len(videos) + 1,
            "likes": 0,
            "dislikes": 0,
            "file_name": video.file_name,
            "file_size(MB)": round(video.file_size/(1024*1024),2),  # Convert to MB
            "duration (seconds)": video.duration ,
            "added_by(user name)": update.effective_user.username,
            "added_by":update.effective_user.full_name,
            "link to the added guy":update.effective_user.link,
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "watched_by": []

        }
        save_json(VIDEO_FILE, videos)
        await update.message.reply_text(H)
    else:
        await update.message.reply_text("ℹ️ Video already exists.")

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    added_valid_names = load_txt_as_list("add_valid_users.txt")
    entered_name = update.message.text.strip()
    if entered_name in added_valid_names:
        
        await starting_button(update, context)
        update_valid_users(update.effective_user)
        update_user_info(update.effective_user)  # Update user info in users_info.json
        await update.message.reply_text("✅ Access granted මචන්! You can now use the bot.")
        await send_videos(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("මචන් උබව අදුරන් නෑ මම, බොසාට මැසේජ් එකක් දාල ඇක්සස් දෙන්න කියපන්කො. ඊටපස්සෙ ආයෙ අවිත් මට නම කියහන්.")
    if update.effective_user.id != ADMIN_ID:
        return 1
    else:
        return ConversationHandler.END  # End the conversation for admin

async def add_this_guy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can add users.")
        return

    await update.message.reply_text("📝 Enter the username of the user to add:")
    return 2  # Return to the input state of the conversation

async def handle_add_this_guy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    added_valid_names = load_txt_as_list("add_valid_users.txt")
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Invalid input. Please try again.")
    if name in added_valid_names:
        return
    else:
        with open("add_valid_users.txt", "a") as f:
            f.write(name + "\n")
        await update.message.reply_text(f"✅ User {name} added successfully!")
    return ConversationHandler.END


# === MAIN SETUP ===
if __name__ == '__main__':
    #shuffle_videos()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("add", add_this_guy)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_this_guy)],
        },
        fallbacks=[],
    )
    

    app.add_handler(conv_handler)

    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CallbackQueryHandler(handle_button))

    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))  # <-- ADDED THIS
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # tmp = load_json("videos.json")
    # for file in tmp:
    #     tmp[file]["file_size(MB)"] = round(tmp[file]["file_size(MB)"] / (1024 * 1024), 2)
    #     print(tmp[file]["file_name"], ":", tmp[file]["file_size(MB)"], "MB")
    #     # print(file)
    #     print()
    # print()

    # print("done")

    print("🤖 කොල්ල වැඩ!")
    logging.basicConfig(level=logging.DEBUG)
    app.run_polling()
