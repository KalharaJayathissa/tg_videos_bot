from pymongo import MongoClient

MONGODB_CONNECTION_STRING = "" #replace with connection key
DATABASE_NAME = "" #replace with the database name

try:
    client = MongoClient(MONGODB_CONNECTION_STRING)
    db = client[DATABASE_NAME]
    print("mongodb connection successfull")
except:
    print("mongodb connection failed! : {e}")

# References to your MongoDB Collections
videos_collection = db["videos"]
video_stats_collection = db["video_stats"]
stickers_collection = db["stickers"]
valid_users_collection = db["valid_users"]
add_valid_users_collection = db["add_valid_users"]
users_info_collection = db["users_info"]

#for delayed delete functionality
to_delete_collection = db["to_be_deleted"]

# ==== HELPER FUNCTIONS (Adapted for MongoDB) ====
# These replace your load_json/save_json/load_txt_as_list/save_txt_as_list
def load_videos_from_db():
    """Load all video documents from MongoDB, keyed by _id."""
    videos = {}
    for doc in videos_collection.find():
        k = doc["_id"] # _id is the file_id here
        del doc["_id"] # Remove _id from the value dict
        videos[k] = doc
    return videos

def update_video_in_db(file_id, video_data):
    """Update a single video document in MongoDB."""
    # Use update_one to update existing document, or insert it if it doesn't exist
    videos_collection.update_one({"_id": file_id}, {"$set": video_data}, upsert=True)

def load_stats_from_db():
    """Load all video stats from MongoDB, keyed by _id (file_id)."""
    stats = {}
    for doc in video_stats_collection.find():
        k = doc["_id"]
        del doc["_id"]
        stats[k] = doc
    return stats

def update_stat_in_db(file_id, stats_data):
    """Update a single video stat document in MongoDB."""
    video_stats_collection.update_one({"_id": file_id}, {"$set": stats_data}, upsert=True)

def load_stickers_from_db():
    """Load sticker file_ids from MongoDB."""
    # Assuming stickers are stored as {"_id": "all_stickers", "file_ids": ["id1", "id2"]}
    doc = stickers_collection.find_one({"_id": "all_stickers"})
    return doc["file_ids"] if doc and "file_ids" in doc else []

def save_stickers_to_db(sticker_list):
    """Save sticker file_ids to MongoDB."""
    stickers_collection.update_one(
        {"_id": "all_stickers"},
        {"$set": {"file_ids": sticker_list}},
        upsert=True
    )

def load_valid_users_from_db():
    """Load valid users from MongoDB, keyed by user_id."""
    valid_users = {}
    for doc in valid_users_collection.find():
        valid_users[str(doc["_id"])] = doc.get("username") # Ensure ID is string for dict key
    return valid_users

def update_valid_user_in_db(user_id, username):
    """Update a single valid user in MongoDB."""
    valid_users_collection.update_one(
        {"_id": user_id},
        {"$set": {"username": username}},
        upsert=True
    )

def load_users_info_from_db():
    """Load users info from MongoDB, keyed by user_id."""
    users_info = {}
    for doc in users_info_collection.find():
        users_info[str(doc["_id"])] = doc # _id is user_id
    return users_info

def update_user_info_in_db(user_id, user_data):
    """Update a single user's info in MongoDB."""
    users_info_collection.update_one({"_id": user_id}, {"$set": user_data}, upsert=True)

def load_add_valid_users_from_db():
    """Load pending users from MongoDB (from the 'names' list)."""
    doc = add_valid_users_collection.find_one({"_id": "pending_users"})
    return doc["names"] if doc and "names" in doc else []


def save_add_valid_users_to_db(names_list):
    """Save pending users list to MongoDB."""
    add_valid_users_collection.update_one(
        {"_id": "pending_users"},
        {"$set": {"names": names_list}},
        upsert=True
    )



#for delayed clear functionality
def add_to_delete(chatID,messageID,user_id):
    query ={"_id":chatID}
    upd_op = { "$addToSet":{"messages":messageID}, "$set":{"user_id":user_id}}

    to_delete_collection.update_one(query, upd_op, upsert=True)
    print(to_delete_collection.find_one(query))


