import os
from pymongo import MongoClient
import asyncio
import json
import random
import logging
from datetime import datetime, UTC
import pytz
from telegram.error import Forbidden
import threading

import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          CallbackQueryHandler, ContextTypes, MessageHandler,
                          filters, ConversationHandler)

from database import *

import telegram

from flask import Flask, request


############################################################################
############################################################################
#### THIS IS THE ACTUAL SCRIPT THAT IS RUNNING ON AZURE IN A CONTAINER #####
############################################################################
############################################################################
"""Yet to be fixed  :there are some inneficient algorithms to be fixed yet. 
                    :deleyd clear functionality {delete_sent_messages()} should 
                      be moved out of /stats button.
                    :Should write new organized code instead of this spaggeti code!"""

# === CONFIGURATION ===
BOT_TOKEN = 'hdskjhsdfdsjjcknsxahdmahlxj'  # Replace with your bot token
ADMIN_ID =  3245435676434855 # Replace with your Telegram user ID


number_of_videos_per_batch = 6

del_time = 60 * (60)  #in minutes
#icons
Like = "❤️"
Dislike = "🤢"


# === Messages ===
A = "Let's check it out."
B = "Shall we watch a video?"
C = "That’s all of them. Do you still have anything left?"
D = "Can you send another video?"
E = "Didn’t really feel it."
F = "That was everything we had. If none of that worked, maybe it's time to take a break!"
G = "Here are four more videos."
H = "I uploaded the video. Thank you very much."

#This variable keeps track of the number of the videos uploaded within 5 minutes
NVUW5M = 0

#this I variable should be declared inside the function just before sending the message.
# I = f"{NVUW5M} new videos added!"

#New video update sleep timer
NVUST = 60 * 5 # SECS





# sticker
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.effective_user.id != ADMIN_ID:
    #     return

    sticker = update.message.sticker
    if not sticker:
        return

    stickers = load_stickers_from_db()
    

    if sticker.file_id not in stickers:
        stickers.append(sticker.file_id)
        save_stickers_to_db(stickers)
        await update.message.reply_text("✅ Sticker saved!")
    else:
        await update.message.reply_text("ℹ️ Sticker already exists.")


# ==== HELPER FUNCTIONS ====
def load_json(file):
    """Load data from a JSON file."""
    if not os.path.exists(file):
        return {}
    with open(file, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(file, data):
    """Save data to a JSON file."""
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def load_txt_as_list(file):
    """Load data from a text file as a list."""
    if not os.path.exists(file):
        return []
    with open(file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def save_txt_as_list(file, data):
    """Save a list of data to a text file."""
    with open(file, 'w') as f:
        for item in data:
            f.write(f"{item}\n")

def update_video_stats(file_id, user_id):
    """Update video statistics in MongoDB."""
    stats = load_stats_from_db() # Load all to work like before, but consider optimizing
    if file_id not in stats:
        stats[file_id] = {"send_count": 0, "users": []}
    stats[file_id]["send_count"] += 1
    if user_id not in stats[file_id]["users"]:
        stats[file_id]["users"].append(user_id)
    update_stat_in_db(file_id, stats[file_id]) # Save individual stat document


def update_valid_users(user):
    """Update valid users in MongoDB."""
    update_valid_user_in_db(user.id, user.username)




def update_user_info(user):
    """Update user information in MongoDB."""
    users_info_data = users_info_collection.find_one({"_id": user.id})

    colombo_tz = pytz.timezone("Asia/Colombo")
    utc_now = datetime.now(UTC)
    colombo_now = utc_now.astimezone(colombo_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    if not users_info_data:
        new_data = {
            "accessed_times": 1,
            "username": user.username,
            "full_name": user.full_name,
            "link": user.link,
            "last access": colombo_now,
            "bot access": str(user.id) in load_valid_users_from_db() # Load all valid users to check access
        }
        users_info_collection.insert_one({"_id": user.id, **new_data})
    else:
        # Use $inc for atomic increment, and $set for other fields
        users_info_collection.update_one(
            {"_id": user.id},
            {
                "$inc": {"accessed_times": 1},
                "$set": {
                    "last access": colombo_now,
                    "bot access": str(user.id) in load_valid_users_from_db()
                }
            }
        )









user_video_progress = {}


def load_stickers(): # This function is called by handle_sticker and send_videos
    return load_stickers_from_db() # CHANGED



#MOVE TO THE TOP LATER
INVALID_USER_MESSAGE = "❌ Your account is not registered. please send your name to see if access is granted."


# === COMMANDS ===
async def starting_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [[InlineKeyboardButton(A, callback_data="send_more")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    strt_button = await update.message.reply_text(B, reply_markup=reply_markup)
    #asyncio.create_task(delayed_clear(context.bot, context._chat_id, strt_button.message_id, delay=del_time))
    add_to_delete(chatID=context._chat_id, messageID=strt_button.message_id, user_id=update._effective_user.id)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_video_progress[update.effective_user.id] = []

    colombo_tz = pytz.timezone("Asia/Colombo")

    utc_now = datetime.now(UTC)

    colombo_now = utc_now.astimezone(colombo_tz).strftime("%Y-%m-%d %H:%M:%S")

    print(update.effective_user.username, " : ",
         colombo_now)
    
    valid_users_dict = load_valid_users_from_db() # CHANGED: Load from DB, it's a dict
    update_user_info(update.effective_user)
    
    if str(update.effective_user.id) not in valid_users_dict: # CHANGED: Check against dict keys
        await update.message.reply_text(INVALID_USER_MESSAGE)
        return 1
    else:
        await starting_button(update, context)

        # thread2 = threading.Thread(target=delte_sent_messages, args=(context.bot,))
        # thread2.start()
        # await delete_sent_messages(context.bot , update.effective_chat.id)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await database_info(
        update,
        context)  # Call the database_info function to print stats in console


# === VIDEO SENDING ===


async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id
    global chat_id
    chat_id = update.effective_chat.id

    if str(user_id) not in load_valid_users_from_db(): # CHANGED
        mg = await context.bot.send_message(
            chat_id=chat_id,
            text=
            "❌  Your account is not registered. press /start to try again"
        )
        #asyncio.create_task(
        #    delayed_clear(context.bot, chat_id, mg.message_id, delay=del_time))
        add_to_delete(chatID=chat_id, messageID=mg.message_id, user_id= user_id)
        
        return  # Exit if user is not valid

    # Load all videos from DB (CHANGED)
    videos_data = load_videos_from_db()
    videos_list_of_ids = list(videos_data.keys()) # Get a list of file_ids (keys)
    random.shuffle(videos_list_of_ids)  # Shuffle the list of file_ids
    #IMPORTANT >> the video list is getting shuffled every times the program sends a batch of videos. So thaere is a chance for user to see same video multiple times(fixed)
    #             and not see some videos at all, even if it says "videos are over, all are sent"

    start = len(user_video_progress.get(user_id, []))
    end = start + number_of_videos_per_batch
    chunk_file_ids = videos_list_of_ids[start:end] # Get chunk of file_ids

    # if none left
    if not chunk_file_ids:
        mg = await context.bot.send_message(chat_id=chat_id, text=C)
        # asyncio.create_task(
        #     delayed_clear(context.bot, chat_id, mg.message_id, delay=del_time))
        add_to_delete(chatID=chat_id, messageID=mg.message_id, user_id=user_id)
        return

    # Send a message prior to the batch
    mg = await context.bot.send_message(chat_id=chat_id, text=G)
    # asyncio.create_task(
    #     delayed_clear(context.bot, chat_id, mg.message_id, delay=del_time))
    add_to_delete(chatID=chat_id, messageID=mg.message_id , user_id=user_id)

    # send the batch
    for file_id in chunk_file_ids: # Iterate through file_ids
        video_details = videos_data[file_id] # Get full details from the loaded dictionary (CHANGED)

        keyboard = [[
            InlineKeyboardButton(
                f"{Like}{video_details['likes']}", # Use video_details (CHANGED)
                callback_data=f"like:{video_details['video no']}:{user_id}"),
            InlineKeyboardButton(
                f"{Dislike}{video_details['dislikes']}", # Use video_details (CHANGED)
                callback_data=f"dislike:{video_details['video no']}:{user_id}")
        ]]
        markup = InlineKeyboardMarkup(keyboard)
        if file_id not in user_video_progress.get(user_id, []):
            sent_message = await context.bot.send_video(chat_id=chat_id,
                                                        video=file_id,
                                                        reply_markup=markup,
                                                        protect_content=True)
            add_to_delete(chatID=sent_message.chat_id, messageID=sent_message.message_id, user_id=user_id)

            # Update watched_by for the current video (CHANGED)
            watched_by_key = str((user.username, user.full_name, user.link))
            if watched_by_key not in video_details["watched_by"]:
                video_details["watched_by"][watched_by_key] = 1
            else:
                video_details["watched_by"][watched_by_key] += 1
            
            # Save updated video details back to DB for this specific video (CHANGED)
            update_video_in_db(file_id, video_details)


            if update.effective_user.id == ADMIN_ID:
                keyboard = [[
                    InlineKeyboardButton(
                        "Delete This!",
                        callback_data=
                        f"delete_video:{video_details['video no']}") # Use video_details (CHANGED)
                ]]
                del_markup = InlineKeyboardMarkup(keyboard)
                delete_message = await update.callback_query.message.reply_text(
                    "❓ delete it? 🗑️", reply_markup=del_markup)
            #     asyncio.create_task(
            #         delayed_clear(context.bot,
            #                     chat_id,
            #                     delete_message.message_id,
            #                     delay=del_time))
                add_to_delete(chatID=chat_id, messageID=delete_message.message_id, user_id=user_id)

            # asyncio.create_task(
            #     delayed_clear(context.bot,
            #                 chat_id,
            #                 sent_message.message_id,
            #                 delay=del_time))
            add_to_delete(chatID=chat_id, messageID=sent_message.message_id, user_id=user_id)
            try:
                user_video_progress[user_id].append(file_id)
            except(KeyError):
                user_video_progress[user_id] = []
                user_video_progress[user_id].append(file_id)
    else:
        print(f"sent a batch to user {user.username}")
    # REMOVED: save_json(VIDEO_FILE, videos_update) is no longer needed here as updates are per-video

    stickers = load_stickers_from_db() # CHANGED
    if not isinstance(stickers, list):
        stickers = []
    stickers = [s for s in stickers if isinstance(s, str) and s] # Filter out bad entries

    if stickers: # Only send if there are stickers (CHANGED)
        sent_sticker = await context.bot.send_sticker(
            chat_id=chat_id, sticker=random.choice(stickers))
        # asyncio.create_task(
        #     delayed_clear(context.bot,
        #                 chat_id,
        #                 sent_sticker.message_id,
        #                 delay=del_time))
        add_to_delete(chatID=chat_id, messageID=sent_sticker.message_id, user_id=user_id)

    # more videos?
    if end < len(videos_list_of_ids): # CHANGED: Check against the length of file_ids list
        keyboard = [[InlineKeyboardButton(D, callback_data="send_more")]]
        markup = InlineKeyboardMarkup(keyboard)
        mg = await context.bot.send_message(chat_id=chat_id,
                                            text=E,
                                            reply_markup=markup)
        # asyncio.create_task(
        #     delayed_clear(context.bot, chat_id, mg.message_id, delay=del_time))
        add_to_delete(chatID=chat_id, messageID=mg.message_id, user_id=user_id)
    else:
        await context.bot.send_message(chat_id=chat_id, text=F)


#THIS FUNCTION HAS NO USE IN THIS VERSION (3.1) OF THE BOT
async def delayed_clear(bot, chat_id, message_id, delay):
    # await asyncio.sleep(delay)
    await bot.delete_message(chat_id=chat_id, message_id=message_id)




async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    if query:
        await query.answer()
    if query.data == "send_more":
        await send_videos(update, context)
    elif query.data.startswith("delete_video:"):
        file_no = query.data.split(":")[1]
        await delete_video(file_no) # This is a custom delete function
        await query.message.reply_text(
            f"✅ Video {file_no} deleted successfully.")
        print(
            f"Video {file_no} deleted by admin {update.effective_user.username} ({update.effective_user.id})"
        )

    elif query.data.split(":")[0] == "like":
        video_no = int(query.data.split(":")[1])
        user_id = int(query.data.split(":")[2])
        
        # Find the video by 'video no' (CHANGED)
        video_doc = videos_collection.find_one({"video no": video_no})

        if video_doc:
            current_likes = video_doc.get("likes", 0)
            current_dislikes = video_doc.get("dislikes", 0)
            
            # Update only the likes field in MongoDB (CHANGED)
            videos_collection.update_one(
                {"_id": video_doc["_id"]}, # Use the actual _id for update
                {"$inc": {"likes": 1}} # Increment likes atomically
            )

            users_info_collection.update_one({"_id":user_id}, {"$addToSet":{"liked":video_no}})

            
            keyboard = [[
                InlineKeyboardButton(
                    f"{Like}{current_likes+1}",
                    callback_data=f"like:{video_no}:{user_id}"),
                InlineKeyboardButton(
                    f"{Dislike}{current_dislikes}",
                    callback_data=f"dislike:{video_no}:{user_id}")
            ]]
            markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=markup)
            print(f"user {user_id} liked the video {video_no}")

    elif query.data.split(":")[0] == "dislike":
        video_no = int(query.data.split(":")[1])
        user_id = int(query.data.split(":")[2])
        
        # Find the video by 'video no' (CHANGED)
        video_doc = videos_collection.find_one({"video no": video_no})

        if video_doc:

            removing = users_info_collection.update_one({"_id":user_id}, {"$pull":{"liked":video_no}})
                #a liked video can be removed from the favorites list, if it was disliked.
            if removing.modified_count <= 0:
                current_likes = video_doc.get("likes", 0)
                current_dislikes = video_doc.get("dislikes", 0)
                
                # Update only the dislikes field in MongoDB (CHANGED)
                videos_collection.update_one(
                    {"_id": video_doc["_id"]},
                    {"$inc": {"dislikes": 1}}
                )

                
                keyboard = [[
                    InlineKeyboardButton(
                        f"{Like}{current_likes}",
                        callback_data=f"like:{video_no}:{user_id}"),
                    InlineKeyboardButton(
                        f"{Dislike}{current_dislikes+1}",
                        callback_data=f"dislike:{video_no}:{user_id}")
                ]]
                markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_reply_markup(reply_markup=markup)
                print(f"disliked the video {video_no}")
            else:
                print("video was removed from favorites")
                await context.bot.send_message(chat_id=chat_id, text=f"video no #{video_no} is removed from your favorites list!")



async def up_vid_count_updater(update:Update, context: ContextTypes.DEFAULT_TYPE,sleep_time):

    global NVUW5M


       
    await asyncio.sleep(sleep_time)

    users = list(load_valid_users_from_db().keys())
    for user in users:
        try:
            message_text = f"{NVUW5M}new videos added! \nSee database statistics: /stats"
            await context.bot.send_message(chat_id=user,text= message_text )
            print(f"bot update message sent to {user}")
        except Forbidden:
            print(f"failed to send the message to the user {user}. \nreason: bot is blocked or remover by the user")
        except:
            print(f"couldn't send the update message to the user {user}")
        
    NVUW5M = 0
    







# Add videos
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    global NVUW5M

    if not video:
        return


    file_id = video.file_id  #this is a string by default
    
    # Check if video already exists by its file_id (_id in MongoDB) (CHANGED)
    existing_video = videos_collection.find_one({"_id": file_id})

    if not existing_video:
        # Get the next video number (similar to len(videos) + 1) (CHANGED)
        # Find the max 'video no' and add 1, or start from 1 if no videos
        last_video = videos_collection.find_one(sort=[("video no", -1)])
        next_video_no = (last_video["video no"] + 1) if last_video else 1
        

        new_video_doc = {
            "_id": file_id, # Use file_id as the primary key
            "video no": next_video_no,
            "likes": 0,
            "dislikes": 0,
            "file_name": video.file_name,
            "file_size(MB)": round(video.file_size / (1024 * 1024), 2),  # Convert to MB
            "duration (seconds)": video.duration,
            "added_by(user name)": update.effective_user.username,
            "added_by": update.effective_user.full_name,
            "link to the added guy": update.effective_user.link,
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "watched_by": {}
        }
        videos_collection.insert_one(new_video_doc) # Insert the new document (CHANGED)
        print("video added [no:"+ str(next_video_no) + "]")


        await update.message.reply_text(H)

        if NVUW5M == 0 :
            NVUW5M = 1
            asyncio.create_task(up_vid_count_updater(update=update, context=context, sleep_time= NVUST))
        else:
            NVUW5M += 1
        

    else:
        await update.message.reply_text("ℹ️ Video already exists.")
        if update.effective_user.id == ADMIN_ID:
            keyboard = [[
                InlineKeyboardButton(
                    "Delete",
                    callback_data=
                    f"delete_video:{str(existing_video['video no'])}") # Use existing_video's video no (CHANGED)
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❓ Do you want to delete it? 🗑️",
                                            reply_markup=reply_markup)


async def delete_video(file_no_to_delete):
    # This delete function now works by 'video no' (CHANGED)
    # Find the document by 'video no' and then delete it
    result = videos_collection.delete_one({"video no": int(file_no_to_delete)})
    if result.deleted_count > 0:
        print(f"Video with video no {file_no_to_delete} deleted from MongoDB.")
    else:
        print(f"Video with video no {file_no_to_delete} not found or already deleted.")




async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    added_valid_names = load_add_valid_users_from_db() # CHANGED
    entered_name = update.message.text.strip()
    if entered_name in added_valid_names:
        await starting_button(update, context)
        update_valid_users(update.effective_user)
        update_user_info(update.effective_user)
        await update.message.reply_text("✅ Access granted! You can now use the bot.")
        await send_videos(update, context)
        
        # Remove the name from the pending list in DB (CHANGED)
        added_valid_names.remove(entered_name)
        save_add_valid_users_to_db(added_valid_names) # CHANGED

        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Looks like you don't have access. please contact the admininistrator."
        )
        return 1
    # return ConversationHandler.END # End for non-admin on unknown input


async def add_this_guy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only the admin can add users.")
        return

    await update.message.reply_text("📝 Enter the username of the user to add:")
    return 2  # Return to the input state of the conversation

async def handle_add_this_guy(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    added_valid_names = load_add_valid_users_from_db() # CHANGED
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❌ Invalid input. Please try again.")
    elif name in added_valid_names:
        await update.message.reply_text("ℹ️ User already in pending list.")
    else:
        added_valid_names.append(name)
        save_add_valid_users_to_db(added_valid_names) # CHANGED
        await update.message.reply_text(f"✅ User {name} added successfully to pending list!")
    return ConversationHandler.END

#SEND MESSAGE TO USERS
async def send_mg_enter_cycle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text="Enter the message:")
    print("waiting for message")
    return 3

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    # await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    if update.effective_user.id == ADMIN_ID:
        users = list(load_valid_users_from_db().keys())
        for user in users:
            try:
            
                await context.bot.send_message(chat_id=user,text= message )
                print(f" message sent to {user}")
            except Forbidden:
                print(f"failed to send the message to the user {user}. \nreason: bot is blocked or remover by the user")
            except:
                print(f"couldn't send the update message to the user {user}")
    else:
        context.bot.send_message(chat_id=ADMIN_ID,text=message)
        
    print(f"message sent:{message}")
    return ConversationHandler.END



async def database_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_vids = videos_collection.count_documents({}) # CHANGED
    # Aggregate total size using MongoDB's aggregation pipeline (CHANGED)
    pipeline = [{"$group": {"_id": None, "total_size_mb": {"$sum": "$file_size(MB)"}}}]

    #Total watch time
    twh = 0 #calculated in seconds
    for file in load_videos_from_db().values():
        twh += file['duration (seconds)']
    #convert to hours, mins and ,secs
    twhh = int(twh / 3600)
    lmins = int((twh - (twhh * 3600))/60)

    result = list(videos_collection.aggregate(pipeline))
    print(result)
    total_size = round((result[0]["total_size_mb"]) /1024, 2) if result else 0 #database size in GBs

    total_stickers = len(load_stickers_from_db()) # CHANGED
    total_users = valid_users_collection.count_documents({}) # Count documents in valid_users collection (CHANGED)

    stats_string =f"🎬 Total Videos: {total_vids}\n💾 Total Size:   {total_size} GB\n👥 Total Users:    {total_users} users\n🎟️ Total Stickers: {total_stickers} stickers\n🕓 Total watch time: {twhh} H {lmins} Mins\n⚙️ Bot Version: 3.2-evDri"


    print(stats_string)
    await update.message.reply_text(stats_string)
    await delete_sent_messages(context.bot , update.effective_chat.id)
    


async def favorites_send(update: Update, context:ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id) #load_users_info_from_db returns strings as keys in the returned dictionary
    
    chat_id = update.effective_chat.id #samae reason mentioned above
    videos = load_videos_from_db()
    try:
        liked_list = (load_users_info_from_db()[user_id]).get("liked", [])

        if len(liked_list) > 0:
            mg_text = await context.bot.send_message(chat_id=chat_id, text="❤️ *Your Favorite Videos*\n\nTap the 🤮 button to remove a video from your favorites.",parse_mode="Markdown")
            # asyncio.create_task(delayed_clear(context.bot,chat_id,mg_text.message_id,delay=del_time))
            add_to_delete(chatID=chat_id, messageID=mg_text.message_id, user_id=user_id)
            for video_no in liked_list:
                mg_text_2 = await context.bot.send_message(chat_id=chat_id, text=f" *You liked video number* #{video_no}", parse_mode="Markdown")
                # asyncio.create_task(delayed_clear(context.bot,chat_id,mg_text_2.message_id,delay=del_time))
                add_to_delete(chatID=chat_id, messageID=mg_text_2.message_id, user_id=user_id)
                to_send_video = str(videos_collection.find_one({"video no":video_no}).get("_id"))
                video_details = videos[to_send_video]
                keyboard = [[
                    InlineKeyboardButton(
                        f"{Like}{video_details['likes']}", # Use video_details (CHANGED)
                        callback_data=f"like:{video_details['video no']}:{user_id}"),
                    InlineKeyboardButton(
                        f"{Dislike}{video_details['dislikes']}", # Use video_details (CHANGED)
                        callback_data=f"dislike:{video_details['video no']}:{user_id}")
                ]]
                markup = InlineKeyboardMarkup(keyboard)

                mg = await context.bot.send_video(chat_id=chat_id,video=to_send_video,protect_content=True, reply_markup=markup)
                # asyncio.create_task(delayed_clear(context.bot,chat_id,mg.message_id,delay=del_time))
                add_to_delete(chatID=chat_id, messageID=mg.message_id, user_id=user_id)
        else:
            no_data_msg = await context.bot.send_message(chat_id=chat_id, text="*You have not liked any videos yet!*\n\nLike videos by tapping the ❤️ to save them in your favorites list.", parse_mode="Markdown")
            # asyncio.create_task(delayed_clear(context.bot,chat_id,no_data_msg.message_id,delay=del_time))
            add_to_delete(chatID=chat_id, messageID=no_data_msg.message_id, user_id=user_id)
    except(KeyError):
        message = await context.bot.send_message(chat_id=chat_id,text="⚠️ *You have not registered yet.*\n\nPlease register first by pressing /start.",parse_mode="Markdown")
        # asyncio.create_task(delayed_clear(context.bot,chat_id,message.message_id,delay=del_time))
        add_to_delete(chatID=chat_id, messageID=message.message_id, user_id=user_id)



async def send_all(update:Update, context:ContextTypes.DEFAULT_TYPE):
    videos = list(load_videos_from_db().keys())
    if update.effective_user.id == ADMIN_ID:
        no = 0
        for vid in videos:
            no += 1
            await context.bot.sendVideo(chat_id=ADMIN_ID,video=vid)
            print(f"video # {no} sent!")


async def delete_sent_messages(bot, live_user_chat_id):
    print("entered the function (debugging)")

    #take time
    colombo_tz = pytz.timezone("Asia/Colombo")
    utc_now = datetime.now(UTC)
    colombo_now = utc_now.astimezone(colombo_tz).strftime("%Y-%m-%d %H:%M:%S")
    now_hour = colombo_now[-8:-6]
    print(now_hour)
    
    for chat in to_delete_collection.find():
        #data_records[chat["_id"]] = chat['messages']

        #Taking if user's last online time is at leas 1H ago
        if chat.get("user_id"):
            user_last_seen = users_info_collection.find_one({"_id":chat["user_id"]})["last access"]
            user_last_seen_hour = user_last_seen[-8:-6]
            print("kkkkkkkkkkkk")
        else: user_last_seen_hour = 00

        chat_id = chat['_id']
                                            #This not compatible if run in different days. It should be fixed later.
        if chat_id != live_user_chat_id and (int(now_hour)-int(user_last_seen_hour) > 1):
            print(f"last seen: {user_last_seen_hour}")
            print(f"now minute: {now_hour}")

            print(chat_id)
            messages = chat['messages']
            for msg in messages:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id = msg)
                    print(f"    {msg} deleted from the chat!")
                except Exception as e:
                    print(e)
                    print("error occured!")
                    

                update_operation ={"$pull":{"messages":msg}}
                result = to_delete_collection.update_one({"_id":chat_id}, update_operation)
                print(f"{result.modified_count} message record deleted from the database")

        else:
            print("current users messages are not going to be deleted")
                #await bot.delete_message(chat_id=chat_id, message_id=message_id)
        #print(f"{msg} deleted")
   # print(data_records)



# === MAIN SETUP ===
if __name__ == '__main__':

    app = ApplicationBuilder().token(BOT_TOKEN).build()


    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("add", add_this_guy)
        ],
        states={
            1: [MessageHandler(filters.TEXT, handle_input)],
            2: [MessageHandler(filters.TEXT, handle_add_this_guy)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)

    conv_handller_send_message = ConversationHandler(
        entry_points=[CommandHandler("message",send_mg_enter_cycle)],
        states={ 3: [MessageHandler(filters.TEXT,send_message)],},
        fallbacks=[],
    )
    app.add_handler(conv_handller_send_message)

    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("favorites",favorites_send))
    app.add_handler(CommandHandler("sendall",send_all))

    app.add_handler(CallbackQueryHandler(handle_button))

    app.add_handler(MessageHandler(filters.Sticker.ALL,
                                   handle_sticker))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    print("🤖 BOT is online!!")
    logging.basicConfig(level=logging.INFO)
    
    WEBHOOK_URL = "https://rnbfc-101-2-186-38.a.free.pinggy.link"
    LOCAL_WEBHOOK_TUNNELING_URL = "https://rnbfc-101-2-186-38.a.free.pinggy.link"  #for testing
    WEBHOOK_PORT = 8000

    LISTEN_IP = "0.0.0.0"

    app.run_webhook(
        listen=LISTEN_IP,
        port=WEBHOOK_PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
       

    )
    print("xxx")



