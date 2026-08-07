import asyncio
import sqlite3
import logging
import requests
import re
import time
import os
from threading import Thread
from flask import Flask
from contextlib import closing
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
    LabeledPrice,
    PreCheckoutQuery,
    ChatMemberUpdated
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================= FLASK SERVER (RENDER.COM ÜÇİN) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running on Render!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Botuň sazlamalary
BOT_TOKEN = '8842438618:AAGk3DQyNaYppuCZNLRXJdzJfXDTrGGPdI8'
ADMIN_IDS = [7315359232]

# TGRASS
TGRASS_API_KEY_DEFAULT = "4473937fc919414daf11f42342aa4b18"  # ilk kurulumda DB'ye yazılacak varsayılan key
TGRASS_API_URL = "https://tgrass.space/offers"

# PIARFLOW
PIARFLOW_API_KEY_DEFAULT = "DQDCuVvJCUQaqH-MOJBiHQPkc4kM-OEQ"  # ilk kurulumda DB'ye yazılacak varsayılan key
PIARFLOW_API_URL = "https://piarflow.com/v1"

# bot
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM States
class AdminStates(StatesGroup):
    waiting_for_sponsor_channel_id = State()
    waiting_for_sponsor_link = State()
    waiting_for_remove_sponsor_id = State()
    waiting_for_start_text = State()
    waiting_for_vpn_code = State()
    waiting_for_addlist_name = State()
    waiting_for_addlist_link = State()
    waiting_for_remove_addlist_id = State()
    waiting_for_broadcast = State()
    waiting_for_sponsor_position = State()
    waiting_for_addlist_position = State()
    waiting_for_tgrass_api_key = State()
    waiting_for_tgrass_earnings = State()
    waiting_for_broadcast_button_text = State()
    waiting_for_broadcast_button_url = State()
    waiting_for_vip_channel_id = State()
    waiting_for_vip_channel_link = State()
    waiting_for_remove_vip_id = State()
    waiting_for_piarflow_api_key = State()
    waiting_for_vip_vpn_code = State()
    waiting_for_add_admin_id = State()
    waiting_for_vpn_sale_code = State()
    waiting_for_vpn_sale_price = State()
    waiting_for_autonews_content = State()

# i'm yourdad'
EMOJI_IDS = {
    "check": "5206607081334906820",      # ✔️
    "lock": "5463200466391298413",        # 🔐
    "stats": "5936143551854285132",       # 📊
    "refresh": "6030657343744644592",     # 🔄
    "broadcast": "6021418126061605425",   # 📢
    "edit": "5359488727158634349",        # ✏️
    "add": "5359651386160068849",         # ➕
    "remove": "5359651386160068849",      # ➖
    "vpn": "5206607081334906820",         # ✔️
    "sponsor": "5463200466391298413",     # 🔐
    "addlist": "5206607081334906820",     # ✔️
    "users": "5936143551854285132",       # 📊
    "warning": "5463200466391298413",     # 🔐
    "success": "5206607081334906820",     # ✔️
    "star": "5206607081334906820",        # ⭐
    "money": "5936143551854285132",       # 💰
    "phone": "6021418126061605425",       # 📱
    "people": "5463200466391298413",      # 👥
    "history": "6030657343744644592",     # 📋
    "info": "5359488727158634349",        # ℹ️
    "telegram": "5359651386160068849",    # 🇺🇸
    "thailand": "5206607081334906820",    # 🇹🇭
    "austria": "5463200466391298413",     # 🇦🇹
    "usa": "5359651386160068849",         # 🇺🇸
    "message": "6021418126061605425",     # 📨
    "time": "6030657343744644592",        # ⏰
    "link": "5359488727158634349",        # 🔗
    "tgrass": "5936143551854285132",      # 🌟
    "back": "5359488727158634349",        # ◀️
    "admin": "5463200466391298413",       # 👑
    "settings": "6030657343744644592"     # ⚙️
}

# Loglamagy sazlamak
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log'
)

logging.info(f"Admin ID: {ADMIN_IDS[0]}")

# ================= TGRASS FUNKSIÝALARY =================
def get_user_language(user_id):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", (f"lang_{user_id}",))
            res = cur.fetchone()
            return res[0] if res else 'ru'
        except:
            return 'ru'

def get_tgrass_api_key():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", ("tgrass_api_key",))
            res = cur.fetchone()
            return res[0] if res and res[0] else TGRASS_API_KEY_DEFAULT
        except:
            return TGRASS_API_KEY_DEFAULT

def set_tgrass_api_key(new_key):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                            ("tgrass_api_key", new_key))
            return True
        except Exception as e:
            logging.error(f"TGrass API key save error: {str(e)}")
            return False

def check_tgrass_subscriptions(user_id, username=None, is_premium=False):
    try:
        url = TGRASS_API_URL
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Auth": get_tgrass_api_key(),
        }
        
        lang = get_user_language(user_id)
        
        payload = {
            "tg_user_id": int(user_id),
            "tg_login": username or "",
            "lang": lang,
            "is_premium": is_premium,
        }
        
        logging.info(f"TGrass API istek: {payload}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            resp_json = response.json()
            logging.info(f"TGrass API cevap: {resp_json}")
            
            if resp_json.get("status") == "not_ok":
                offers = resp_json.get("offers", [])
                formatted_offers = []
                for offer in offers:
                    channel_name = None
                    if "title" in offer and offer["title"]:
                        channel_name = offer["title"]
                    elif "name" in offer and offer["name"]:
                        channel_name = offer["name"]
                    elif "channel_name" in offer and offer["channel_name"]:
                        channel_name = offer["channel_name"]
                    elif "description" in offer and offer["description"]:
                        channel_name = offer["description"][:30]
                    else:
                        channel_name = "Партнерский канал"
                    
                    channel_link = None
                    if "link" in offer and offer["link"]:
                        channel_link = offer["link"]
                    elif "url" in offer and offer["url"]:
                        channel_link = offer["url"]
                    elif "channel_link" in offer and offer["channel_link"]:
                        channel_link = offer["channel_link"]
                    else:
                        channel_link = "#"
                    
                    formatted_offers.append({
                        "title": channel_name,
                        "link": channel_link,
                        "id": offer.get("id", 0)
                    })
                
                return formatted_offers
        return []
    except Exception as e:
        logging.error(f"TGrass error: {e}")
        return []

def get_tgrass_enabled():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", ("tgrass_enabled",))
            res = cur.fetchone()
            return res[0] == '1' if res else True
        except:
            return True

def set_tgrass_enabled(enabled):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                            ("tgrass_enabled", "1" if enabled else "0"))
            return True
        except Exception as e:
            logging.error(f"TGrass error: {str(e)}")
            return False

def get_tgrass_channel_count():
    """TGrass API-den häzirki hödürlenýän sponsor kanal sanyny alýar (admin ID bilen synag soragy)."""
    if not get_tgrass_enabled():
        return 0
    try:
        probe_id = ADMIN_IDS[0] if ADMIN_IDS else 123456789
        offers = check_tgrass_subscriptions(probe_id, None, False)
        return len(offers)
    except Exception as e:
        logging.error(f"TGrass count error: {e}")
        return 0

def get_tgrass_earnings():
    return get_setting('tgrass_earnings') or '0'

def set_tgrass_earnings(value):
    set_setting('tgrass_earnings', value)

# ================= PIARFLOW FUNKSIÝALARY =================
def get_piarflow_api_key():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", ("piarflow_api_key",))
            res = cur.fetchone()
            return res[0] if res and res[0] else PIARFLOW_API_KEY_DEFAULT
        except:
            return PIARFLOW_API_KEY_DEFAULT

def set_piarflow_api_key(new_key):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                            ("piarflow_api_key", new_key))
            return True
        except Exception as e:
            logging.error(f"PiarFlow API key save error: {str(e)}")
            return False

def get_piarflow_enabled():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", ("piarflow_enabled",))
            res = cur.fetchone()
            return res[0] == '1' if res else True
        except:
            return True

def set_piarflow_enabled(enabled):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                            ("piarflow_enabled", "1" if enabled else "0"))
            return True
        except Exception as e:
            logging.error(f"PiarFlow error: {str(e)}")
            return False

def check_piarflow_sponsors_raw(user_id, chat_id, max_sponsors=5):
    """PiarFlow /sponsors API-sinden entegrasiýa edilmedik (unsubscribed) teklipleri alýar."""
    try:
        headers = {
            "Authorization": f"Bearer {get_piarflow_api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "user_id": int(user_id),
            "chat_id": int(chat_id),
            "max_sponsors": max_sponsors,
        }
        logging.info(f"PiarFlow API istek: {payload}")
        response = requests.post(f"{PIARFLOW_API_URL}/sponsors", json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            resp_json = response.json()
            logging.info(f"PiarFlow API cevap: {resp_json}")
            sponsors = resp_json.get("sponsors", [])
            return [s for s in sponsors if s.get("status") == "unsubscribed"]
        return []
    except Exception as e:
        logging.error(f"PiarFlow error: {e}")
        return []

async def check_piarflow_sponsors(user_id, chat_id, max_sponsors=5):
    """Adyny (title) çözen görnüşde PiarFlow tekliplerini gaýtarýar."""
    raw_offers = check_piarflow_sponsors_raw(user_id, chat_id, max_sponsors)
    formatted_offers = []
    for sponsor in raw_offers:
        link = sponsor.get("link", "#")
        name = await get_channel_name(link=link)
        formatted_offers.append({
            "title": name,
            "link": link,
            "price": sponsor.get("price", 0)
        })
    return formatted_offers

def get_piarflow_channel_count():
    """PiarFlow API-den häzirki hödürlenýän sponsor kanal sanyny alýar (admin ID bilen synag soragy)."""
    if not get_piarflow_enabled():
        return 0
    try:
        probe_id = ADMIN_IDS[0] if ADMIN_IDS else 123456789
        offers = check_piarflow_sponsors_raw(probe_id, probe_id, 5)
        return len(offers)
    except Exception as e:
        logging.error(f"PiarFlow count error: {e}")
        return 0

def parse_premium_emoji(text):
    pattern = r'<tg-emoji emoji-id="([^"]+)">([^<]+)</tg-emoji>'
    
    def replace_emoji(match):
        emoji_id = match.group(1)
        emoji_char = match.group(2)
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
    
    return re.sub(pattern, replace_emoji, text)

def init_db():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                                user_id INTEGER PRIMARY KEY
                            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS sponsors (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                channel_id TEXT,
                                link TEXT,
                                position INTEGER
                            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS settings (
                                key TEXT PRIMARY KEY,
                                value TEXT
                            )''')
            try:
                conn.execute('''CREATE TABLE IF NOT EXISTS addlists (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    name TEXT,
                                    link TEXT,
                                    position INTEGER
                                )''')
            except Exception as e:
                logging.error(f"Addlists error: {str(e)}")
                conn.execute('''DROP TABLE IF EXISTS addlists''')
                conn.execute('''CREATE TABLE addlists (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    name TEXT,
                                    link TEXT,
                                    position INTEGER
                                )''')

            conn.execute('''CREATE TABLE IF NOT EXISTS vip_channels (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                channel_id TEXT,
                                link TEXT,
                                position INTEGER
                            )''')

            conn.execute('''CREATE TABLE IF NOT EXISTS admins (
                                user_id INTEGER PRIMARY KEY,
                                added_by INTEGER,
                                added_at TEXT
                            )''')

            conn.execute('''CREATE TABLE IF NOT EXISTS bot_channels (
                                chat_id INTEGER PRIMARY KEY,
                                title TEXT,
                                added_at TEXT
                            )''')

            conn.execute('''CREATE TABLE IF NOT EXISTS vpn_sales (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                code TEXT,
                                stars INTEGER,
                                paid_at TEXT
                            )''')

            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('vpn_sale_code', '')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('vpn_sale_price', '50')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('autonews_enabled', '0')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('autonews_chat_id', '')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('autonews_message_id', '')")

            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('start_text', '')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('vpn_code', '')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('vip_vpn_code', '')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tgrass_enabled', '1')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tgrass_api_key', ?)", (TGRASS_API_KEY_DEFAULT,))
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tgrass_earnings', '0')")

            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('piarflow_enabled', '1')")
            conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('piarflow_api_key', ?)", (PIARFLOW_API_KEY_DEFAULT,))

            try:
                cur = conn.execute("PRAGMA table_info(sponsors)")
                columns = [info[1] for info in cur.fetchall()]
                if 'position' not in columns:
                    conn.execute("ALTER TABLE sponsors ADD COLUMN position INTEGER")
                    conn.execute("UPDATE sponsors SET position = id WHERE position IS NULL")
            except Exception as e:
                logging.error(f"Sponsor migration error: {str(e)}")

            try:
                cur = conn.execute("PRAGMA table_info(addlists)")
                columns = [info[1] for info in cur.fetchall()]
                if 'position' not in columns:
                    conn.execute("ALTER TABLE addlists ADD COLUMN position INTEGER")
                    conn.execute("UPDATE addlists SET position = id WHERE position IS NULL")
            except Exception as e:
                logging.error(f"Addlist migration error: {str(e)}")

init_db()

def get_setting(key):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            res = cur.fetchone()
            return res[0] if res else ''
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return ''

def set_setting(key, value):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        except Exception as e:
            logging.error(f"Error: {str(e)}")

def get_admin_ids():
    """Eýesi (ADMIN_IDS) + DB-de goşulan adminleriň sanawyny gaýtarýar."""
    ids = set(ADMIN_IDS)
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT user_id FROM admins")
            ids.update(row[0] for row in cur.fetchall())
        except Exception as e:
            logging.error(f"get_admin_ids error: {str(e)}")
    return ids

def is_admin(user_id):
    return user_id in get_admin_ids()

def add_admin(user_id, added_by):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute(
                    "INSERT OR IGNORE INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
                    (user_id, added_by, time.strftime('%Y-%m-%d %H:%M:%S'))
                )
            return True
        except Exception as e:
            logging.error(f"add_admin error: {str(e)}")
            return False

def remove_admin(user_id):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
            return True
        except Exception as e:
            logging.error(f"remove_admin error: {str(e)}")
            return False

def get_extra_admins():
    """Diňe DB-de goşulan (eýesi bolmadyk) adminler — bulary aýryp bolýar."""
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT user_id FROM admins ORDER BY added_at ASC")
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logging.error(f"get_extra_admins error: {str(e)}")
            return []

# ================= BOT-ADMIN KANALLAR (awto-habar üçin) =================
def upsert_bot_channel(chat_id, title):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO bot_channels (chat_id, title, added_at) VALUES (?, ?, ?)",
                    (chat_id, title, time.strftime('%Y-%m-%d %H:%M:%S'))
                )
        except Exception as e:
            logging.error(f"upsert_bot_channel error: {str(e)}")

def remove_bot_channel(chat_id):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("DELETE FROM bot_channels WHERE chat_id = ?", (chat_id,))
        except Exception as e:
            logging.error(f"remove_bot_channel error: {str(e)}")

def get_bot_channels():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT chat_id, title FROM bot_channels")
            return cur.fetchall()
        except Exception as e:
            logging.error(f"get_bot_channels error: {str(e)}")
            return []

# ================= VPN SATYŞ (Telegram Stars) =================
def get_vpn_sale_code():
    return get_setting('vpn_sale_code')

def set_vpn_sale_code(code):
    set_setting('vpn_sale_code', code)

def get_vpn_sale_price():
    try:
        return int(get_setting('vpn_sale_price') or '50')
    except ValueError:
        return 50

def set_vpn_sale_price(stars):
    set_setting('vpn_sale_price', str(int(stars)))

def log_vpn_sale(user_id, code, stars):
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute(
                    "INSERT INTO vpn_sales (user_id, code, stars, paid_at) VALUES (?, ?, ?, ?)",
                    (user_id, code, stars, time.strftime('%Y-%m-%d %H:%M:%S'))
                )
        except Exception as e:
            logging.error(f"log_vpn_sale error: {str(e)}")

def get_vpn_sales_stats():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT COUNT(*), COALESCE(SUM(stars), 0) FROM vpn_sales")
            return cur.fetchone()
        except Exception as e:
            logging.error(f"get_vpn_sales_stats error: {str(e)}")
            return (0, 0)

# ================= AWTO-HABAR (her 3 sagatdan) =================
def get_autonews_enabled():
    return get_setting('autonews_enabled') == '1'

def set_autonews_enabled(enabled):
    set_setting('autonews_enabled', '1' if enabled else '0')

def set_autonews_content(chat_id, message_id):
    set_setting('autonews_chat_id', str(chat_id))
    set_setting('autonews_message_id', str(message_id))

def get_autonews_content():
    chat_id = get_setting('autonews_chat_id')
    message_id = get_setting('autonews_message_id')
    if chat_id and message_id:
        return int(chat_id), int(message_id)
    return None, None

def get_sponsors():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT id, channel_id, link, position FROM sponsors ORDER BY position ASC")
            return cur.fetchall()
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return []

def get_addlists():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT id, name, link, position FROM addlists ORDER BY position ASC")
            return cur.fetchall()
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return []

def get_vip_channels():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT id, channel_id, link, position FROM vip_channels ORDER BY position ASC")
            return cur.fetchall()
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return []

def get_all_users():
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            cur = conn.execute("SELECT user_id FROM users")
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return []

async def is_user_subscribed(user_id, channel_id):
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return False

async def get_channel_name(channel_id=None, link=None):
    try:
        if channel_id:
            chat = await bot.get_chat(channel_id)
            return chat.title or f"Канал {channel_id}"
        elif link and link.startswith('https://t.me/'):
            username = link.replace('https://t.me/', '@')
            chat = await bot.get_chat(username)
            return chat.title or username
        else:
            return link.split('/')[-1] if link else "Неизвестный канал"
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return link.split('/')[-1] if link else "Неизвестный канал"

async def get_all_channels(user_id, username=None, is_premium=False):
    sponsors = get_sponsors()
    addlists = get_addlists()
    used_urls = set()
    all_channels = []

    for sponsor in sponsors:
        if sponsor[2] not in used_urls and sponsor[3] is not None:
            used_urls.add(sponsor[2])
            all_channels.append({
                'id': sponsor[0],
                'link': sponsor[2],
                'position': sponsor[3],
                'channel_id': sponsor[1],
                'type': 'sponsor',
                'name': await get_channel_name(channel_id=sponsor[1]),
                'is_tgrass': False
            })

    for addlist in addlists:
        if addlist[2] not in used_urls and addlist[3] is not None:
            used_urls.add(addlist[2])
            all_channels.append({
                'id': addlist[0],
                'link': addlist[2],
                'position': addlist[3],
                'channel_id': None,
                'type': 'addlist',
                'name': addlist[1],
                'is_tgrass': False
            })

    tgrass_enabled = get_tgrass_enabled()
    if tgrass_enabled:
        tgrass_offers = check_tgrass_subscriptions(user_id, username, is_premium)
        if tgrass_offers:
            max_position = len(all_channels) + 1
            for i, offer in enumerate(tgrass_offers):
                channel_name = offer.get('title', 'Партнерский канал')
                if not channel_name or channel_name == 'Bilinmeýän':
                    channel_name = f"🌟 Канал {i+1}"
                
                all_channels.append({
                    'id': f"tgrass_{i}",
                    'link': offer.get('link', '#'),
                    'position': max_position + i,
                    'channel_id': None,
                    'type': 'tgrass',
                    'name': channel_name,
                    'is_tgrass': True,
                    'offer_id': offer.get('id', i)
                })

    piarflow_enabled = get_piarflow_enabled()
    if piarflow_enabled:
        piarflow_offers = await check_piarflow_sponsors(user_id, user_id, 5)
        if piarflow_offers:
            max_position = len(all_channels) + 1
            for i, offer in enumerate(piarflow_offers):
                channel_name = offer.get('title') or f"💎 Канал {i+1}"

                all_channels.append({
                    'id': f"piarflow_{i}",
                    'link': offer.get('link', '#'),
                    'position': max_position + i,
                    'channel_id': None,
                    'type': 'piarflow',
                    'name': channel_name,
                    'is_tgrass': False
                })

    all_channels.sort(key=lambda x: x['position'])
    return all_channels

async def check_all_subscriptions(user_id, username=None, is_premium=False):
    not_subscribed = []
    
    sponsors = get_sponsors()
    for sponsor in sponsors:
        channel_id = sponsor[1]
        if not await is_user_subscribed(user_id, channel_id):
            not_subscribed.append({
                'name': await get_channel_name(channel_id=sponsor[1]),
                'link': sponsor[2],
                'type': 'sponsor'
            })
    
    tgrass_enabled = get_tgrass_enabled()
    if tgrass_enabled:
        tgrass_offers = check_tgrass_subscriptions(user_id, username, is_premium)
        if tgrass_offers:
            for offer in tgrass_offers:
                channel_name = offer.get('title', 'Партнерский канал')
                if not channel_name or channel_name == 'Bilinmeýän':
                    channel_name = "🌟 Партнерский канал"
                not_subscribed.append({
                    'name': channel_name,
                    'link': offer.get('link', '#'),
                    'type': 'tgrass'
                })
    
    piarflow_enabled = get_piarflow_enabled()
    if piarflow_enabled:
        piarflow_offers = await check_piarflow_sponsors(user_id, user_id, 5)
        if piarflow_offers:
            for offer in piarflow_offers:
                channel_name = offer.get('title') or "💎 Партнерский канал"
                not_subscribed.append({
                    'name': channel_name,
                    'link': offer.get('link', '#'),
                    'type': 'piarflow'
                })
    
    return len(not_subscribed) == 0, not_subscribed

# Bot haýsy kanal/gruppalarda admin bolsa, awto-habar üçin ýazgy edilýär
@dp.my_chat_member()
async def track_bot_admin_channels(event: ChatMemberUpdated):
    try:
        if event.chat.type not in ("channel", "group", "supergroup"):
            return
        new_status = event.new_chat_member.status
        if new_status in ("administrator", "creator"):
            upsert_bot_channel(event.chat.id, event.chat.title or str(event.chat.id))
            logging.info(f"Bot admin boldy: {event.chat.title} ({event.chat.id})")
        elif new_status in ("left", "kicked", "member", "restricted"):
            remove_bot_channel(event.chat.id)
            logging.info(f"Bot admin däl indi: {event.chat.title} ({event.chat.id})")
    except Exception as e:
        logging.error(f"track_bot_admin_channels error: {str(e)}")

# /start komut
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    is_premium = getattr(message.from_user, 'is_premium', False)
    
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        except Exception as e:
            logging.error(f"Error: {str(e)}")

    start_text = get_setting('start_text').strip()
    if not start_text:
        start_text = (
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['lock']}\">🔐</tg-emoji> <b>Добро пожаловать!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Чтобы получить VPN код, подпишитесь на каналы ниже 👇\n\n"
            f"После подписки нажмите кнопку <b>«Я подписался»</b>"
        )
    else:
        start_text = parse_premium_emoji(start_text)

    all_channels = await get_all_channels(user_id, username, is_premium)
    
    if not all_channels:
        await message.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> Каналы не найдены. Свяжитесь с администратором."
        )
        return

    # Каналы 2 столбца ýerleşdirilýär
    channel_rows = []
    row_buffer = []
    for idx, channel in enumerate(all_channels, start=1):
        icon = "🔵"
        btn = InlineKeyboardButton(text=f"{icon} {idx}. {channel['name']}", url=channel['link'])
        row_buffer.append(btn)
        if len(row_buffer) == 2:
            channel_rows.append(row_buffer)
            row_buffer = []
    if row_buffer:
        channel_rows.append(row_buffer)

    check_button = InlineKeyboardButton(
        text="🟢 Я подписался",
        callback_data="check_sub"
    )
    channel_rows.append([check_button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=channel_rows)

    await message.answer(
        f"{start_text}\n\n<i>Каналов для подписки: {len(all_channels)}</i>",
        reply_markup=keyboard
    )

# Check subscription callback
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery):
    user_id = call.from_user.id
    username = call.from_user.username
    is_premium = getattr(call.from_user, 'is_premium', False)

    is_subscribed, not_subscribed = await check_all_subscriptions(user_id, username, is_premium)

    if not is_subscribed:
        text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> <b>Вы подписались не на все каналы:</b>\n━━━━━━━━━━━━━━━\n"
        for i, channel in enumerate(not_subscribed, start=1):
            text += f"{i}. {channel['name']}\n"
        text += "\n👉 Подпишитесь и нажмите кнопку ещё раз."
        await call.answer(text=text, show_alert=True)
    else:
        await call.answer(text="🟢 Отлично! Вы подписаны на все каналы!", show_alert=True)
        vpn_code = get_setting('vpn_code')
        if vpn_code:
            await call.message.answer(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['vpn']}\">✔️</tg-emoji> <b>Ваш VPN код готов:</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"<code>{vpn_code}</code>\n\n"
                f"<i>Нажмите на код, чтобы скопировать</i>"
            )
        else:
            await call.message.answer(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> VPN код еще не настроен администратором."
            )

# /vip komut
@dp.message(Command("vip"))
async def cmd_vip(message: Message):
    vip_channels = get_vip_channels()

    if not vip_channels:
        await message.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> VIP каналы еще не добавлены администратором."
        )
        return

    text = (
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['star']}\">⭐</tg-emoji> <b>VIP каналы</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Подпишитесь на каналы ниже 👇\n\n"
        f"После подписки нажмите кнопку <b>«Я подписался»</b>"
    )

    channel_rows = []
    row_buffer = []
    for idx, vip in enumerate(vip_channels, start=1):
        name = await get_channel_name(channel_id=vip[1])
        btn = InlineKeyboardButton(text=f"🔵 {idx}. {name}", url=vip[2])
        row_buffer.append(btn)
        if len(row_buffer) == 2:
            channel_rows.append(row_buffer)
            row_buffer = []
    if row_buffer:
        channel_rows.append(row_buffer)

    check_button = InlineKeyboardButton(
        text="🟢 Я подписался",
        callback_data="check_vip_sub"
    )
    channel_rows.append([check_button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=channel_rows)

    await message.answer(
        f"{text}\n\n<i>Каналов для подписки: {len(vip_channels)}</i>",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "check_vip_sub")
async def check_vip_sub_callback(call: CallbackQuery):
    user_id = call.from_user.id
    vip_channels = get_vip_channels()

    if not vip_channels:
        await call.answer("❌ VIP каналы не найдены.", show_alert=True)
        return

    not_subscribed = []
    for vip in vip_channels:
        if not await is_user_subscribed(user_id, vip[1]):
            name = await get_channel_name(channel_id=vip[1])
            not_subscribed.append(name)

    if not_subscribed:
        text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> Вы подписались не на все VIP каналы:\n"
        for i, name in enumerate(not_subscribed, start=1):
            text += f"{i}. {name}\n"
        text += "\n👉 Подпишитесь и нажмите кнопку ещё раз."
        await call.answer(text=text, show_alert=True)
    else:
        await call.answer(text="🟢 Отлично! Вы подписаны на все VIP каналы!", show_alert=True)
        vip_vpn_code = get_setting('vip_vpn_code')
        if vip_vpn_code:
            await call.message.answer(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['star']}\">⭐</tg-emoji> <b>Ваш VIP VPN код готов:</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"<code>{vip_vpn_code}</code>\n\n"
                f"<i>Нажмите на код, чтобы скопировать</i>"
            )
        else:
            await call.message.answer(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> VIP VPN код еще не настроен администратором."
            )

# ================= VPN SATYŞ (Telegram Stars bilen satyn almak) =================
@dp.message(Command("buyvpn"))
async def cmd_buy_vpn(message: Message):
    price = get_vpn_sale_price()
    code = get_vpn_sale_code()
    if not code:
        await message.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> VPN сатылмаýар — администратор ýaly kod goşmady."
        )
        return

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="VPN код",
        description=f"Premium VPN kody satyn almak — dessine iberilýär.",
        payload=f"vpn_sale_{message.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label="VPN код", amount=price)],
        provider_token=""
    )

@dp.callback_query(F.data == "buy_vpn")
async def callback_buy_vpn(call: CallbackQuery):
    price = get_vpn_sale_price()
    code = get_vpn_sale_code()
    if not code:
        await call.answer("❌ VPN коды пока не настроен администратором.", show_alert=True)
        return

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="VPN код",
        description="Premium VPN код — придёт сразу после оплаты.",
        payload=f"vpn_sale_{call.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label="VPN код", amount=price)],
        provider_token=""
    )
    await call.answer()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    # Töleg tassyklanmazdan öň barlanýar; kod bar bolmaly
    if not get_vpn_sale_code():
        await bot.answer_pre_checkout_query(
            pre_checkout_q.id, ok=False, error_message="VPN код временно недоступен, попробуйте позже."
        )
        return
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    code = get_vpn_sale_code()
    stars = message.successful_payment.total_amount
    log_vpn_sale(message.from_user.id, code, stars)

    if code:
        await message.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Оплата прошла успешно!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Ваш VPN код:\n<code>{code}</code>\n\n"
            f"<i>Нажмите на код, чтобы скопировать</i>"
        )
    else:
        await message.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">⚠️</tg-emoji> Оплата прошла, но код временно недоступен. Напишите администратору."
        )

# Admin panel
def build_admin_panel_keyboard():
    builder = InlineKeyboardBuilder()

    builder.button(text="Добавить спонсора", callback_data="add_sponsor", icon_custom_emoji_id=EMOJI_IDS["add"])
    builder.button(text="Удалить спонсора", callback_data="remove_sponsor", icon_custom_emoji_id=EMOJI_IDS["remove"])
    builder.button(text="Добавить Addlist", callback_data="add_addlist", icon_custom_emoji_id=EMOJI_IDS["add"])
    builder.button(text="Удалить Addlist", callback_data="remove_addlist", icon_custom_emoji_id=EMOJI_IDS["remove"])
    builder.button(text="Start текст", callback_data="edit_start", icon_custom_emoji_id=EMOJI_IDS["edit"])
    builder.button(text="VPN код", callback_data="edit_code", icon_custom_emoji_id=EMOJI_IDS["lock"])
    builder.button(text="VIP VPN код", callback_data="edit_vip_code", icon_custom_emoji_id=EMOJI_IDS["star"])
    builder.button(text="Рассылка", callback_data="broadcast", icon_custom_emoji_id=EMOJI_IDS["broadcast"])
    builder.button(text="Статистика", callback_data="stats", icon_custom_emoji_id=EMOJI_IDS["stats"])
    builder.button(text="TGrass настройки", callback_data="tgrass_settings", icon_custom_emoji_id=EMOJI_IDS["tgrass"])
    builder.button(text="PiarFlow настройки", callback_data="piarflow_settings", icon_custom_emoji_id=EMOJI_IDS["money"])
    builder.button(text="VIP каналы", callback_data="vip_menu", icon_custom_emoji_id=EMOJI_IDS["star"])
    builder.button(text="Админы", callback_data="admin_menu", icon_custom_emoji_id=EMOJI_IDS["admin"])
    builder.button(text="VPN продажа", callback_data="vpn_sale_menu", icon_custom_emoji_id=EMOJI_IDS["vpn"])
    builder.button(text="Авто-рассылка каналов", callback_data="autonews_menu", icon_custom_emoji_id=EMOJI_IDS["broadcast"])

    builder.adjust(2)
    return builder.as_markup()

async def build_admin_panel_text():
    users = get_all_users()
    sponsors = get_sponsors()
    addlists = get_addlists()
    tgrass_enabled = get_tgrass_enabled()
    tgrass_count = get_tgrass_channel_count()
    tgrass_earnings = get_tgrass_earnings()
    vip_channels = get_vip_channels()
    piarflow_count = get_piarflow_channel_count()
    admin_count = len(get_admin_ids())
    bot_channels_count = len(get_bot_channels())
    sales_count, sales_stars = get_vpn_sales_stats()
    autonews_on = get_autonews_enabled()

    return (
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['admin']}\">👑</tg-emoji> <b>Админ панель</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: <b>{len(users)}</b>  |  👑 Админов: <b>{admin_count}</b>\n"
        f"📢 Спонсоров: <b>{len(sponsors)}</b>  |  📋 Addlist: <b>{len(addlists)}</b>\n"
        f"⭐ VIP каналов: <b>{len(vip_channels)}</b>\n"
        f"💎 PiarFlow каналов: <b>{piarflow_count}</b>\n"
        f"🌟 TGrass: {'✅ Вкл' if tgrass_enabled else '❌ Выкл'}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['tgrass']}\">🌟</tg-emoji> TGrass каналов: <b>{tgrass_count}</b>\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['money']}\">💰</tg-emoji> Доход с TGrass: <b>{tgrass_earnings}</b>\n"
        f"💳 Продаж VPN: <b>{sales_count}</b> (⭐{sales_stars})\n"
        f"📡 Каналов бот-админ: <b>{bot_channels_count}</b>  |  Авто-рассылка: {'✅' if autonews_on else '❌'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<i>Выберите раздел ниже 👇</i>"
    )

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id not in get_admin_ids():
        await message.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">🔐</tg-emoji> Вы не администратор!"
        )
        return

    await message.answer(
        await build_admin_panel_text(),
        reply_markup=build_admin_panel_keyboard()
    )

# ================= ADMIN CALLBACK HANDLERS =================

@dp.callback_query(F.data == "add_sponsor")
async def add_sponsor_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['add']}\">➕</tg-emoji> <b>Добавление спонсора</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Шаг 1/2: отправьте <b>ID канала</b>\n"
        f"<code>-1001234567890</code>\n\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_sponsor_channel_id)
    await call.answer()

@dp.message(AdminStates.waiting_for_sponsor_channel_id)
async def process_sponsor_channel_id(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    channel_id = message.text.strip()
    await state.update_data(channel_id=channel_id)
    
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['link']}\">🔗</tg-emoji> Шаг 2/2: отправьте <b>ссылку</b> на канал\n"
        f"<code>https://t.me/channelname</code>"
    )
    await state.set_state(AdminStates.waiting_for_sponsor_link)

@dp.message(AdminStates.waiting_for_sponsor_link)
async def process_sponsor_link(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    link = message.text.strip()
    data = await state.get_data()
    channel_id = data.get('channel_id')
    
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                cur = conn.execute("SELECT MAX(position) FROM sponsors")
                max_pos = cur.fetchone()[0]
                new_position = (max_pos + 1) if max_pos else 1
                
                conn.execute(
                    "INSERT INTO sponsors (channel_id, link, position) VALUES (?, ?, ?)",
                    (channel_id, link, new_position)
                )
            
            builder = InlineKeyboardBuilder()
            builder.button(text="◀️ В меню", callback_data="back_to_admin")
            await message.answer(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Спонсор успешно добавлен!</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 ID: <code>{channel_id}</code>\n"
                f"🔗 Ссылка: {link}",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()

@dp.callback_query(F.data == "remove_sponsor")
async def remove_sponsor_start(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    sponsors = get_sponsors()
    if not sponsors:
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="back_to_admin")
        await call.message.edit_text("❌ Список спонсоров пуст.", reply_markup=builder.as_markup())
        await call.answer()
        return
    
    text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['remove']}\">➖</tg-emoji> <b>Выберите спонсора для удаления:</b>\n━━━━━━━━━━━━━━━\n"
    builder = InlineKeyboardBuilder()
    
    for sponsor in sponsors:
        name = await get_channel_name(channel_id=sponsor[1])
        builder.button(
            text=f"❌ {name}",
            callback_data=f"del_sponsor_{sponsor[0]}"
        )
    
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(2)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("del_sponsor_"))
async def delete_sponsor(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    sponsor_id = int(call.data.replace("del_sponsor_", ""))
    
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("DELETE FROM sponsors WHERE id = ?", (sponsor_id,))
            builder = InlineKeyboardBuilder()
            builder.button(text="◀️ В меню", callback_data="back_to_admin")
            await call.message.edit_text(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Спонсор удален!",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            await call.answer(f"Ошибка: {str(e)}", show_alert=True)
    
    await call.answer()

@dp.callback_query(F.data == "edit_start")
async def edit_start_text(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    current_text = get_setting('start_text')
    
    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['edit']}\">✏️</tg-emoji> <b>Изменение стартового сообщения</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text if current_text else 'Стандартный текст'}\n\n"
        f"<b>Отправьте новый текст:</b>\n"
        f"Вы можете использовать HTML теги:\n"
        f"• <code>&lt;b&gt;жирный&lt;/b&gt;</code> - <b>жирный</b>\n"
        f"• <code>&lt;i&gt;курсив&lt;/i&gt;</code> - <i>курсив</i>\n"
        f"• <code>&lt;u&gt;подчеркнутый&lt;/u&gt;</code> - <u>подчеркнутый</u>\n"
        f"• <code>&lt;s&gt;зачеркнутый&lt;/s&gt;</code> - <s>зачеркнутый</s>\n"
        f"• <code>&lt;code&gt;моноширинный&lt;/code&gt;</code> - <code>моноширинный</code>\n"
        f"• <code>&lt;a href='url'&gt;ссылка&lt;/a&gt;</code> - ссылка\n\n"
        f"<b>Premium эмодзи:</b>\n"
        f"Отправьте любое premium эмодзи из Telegram, и бот автоматически сохранит его ID.\n\n"
        f"Отправьте /cancel для отмены."
    )
    await state.set_state(AdminStates.waiting_for_start_text)
    await call.answer()

@dp.message(AdminStates.waiting_for_start_text)
async def process_start_text(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    new_text = message.html_text if message.html_text else message.text
    
    if message.entities:
        for entity in message.entities:
            if entity.type == "custom_emoji":
                emoji_id = entity.custom_emoji_id
                logging.info(f"Premium emoji found: {emoji_id}")
    
    set_setting('start_text', new_text)
    
    preview_text = parse_premium_emoji(new_text)
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="back_to_admin")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Текст сохранен!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>Предпросмотр:</b>\n{preview_text}",
        parse_mode=ParseMode.HTML,
        reply_markup=builder.as_markup()
    )
    
    await state.clear()

@dp.callback_query(F.data == "edit_code")
async def edit_vpn_code(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    current_code = get_setting('vpn_code')
    
    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['lock']}\">🔐</tg-emoji> <b>Изменение VPN кода</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Текущий код: <code>{current_code if current_code else 'Не установлен'}</code>\n\n"
        f"Отправьте новый VPN код или /cancel для отмены."
    )
    await state.set_state(AdminStates.waiting_for_vpn_code)
    await call.answer()

@dp.message(AdminStates.waiting_for_vpn_code)
async def process_vpn_code(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    new_code = message.text.strip()
    set_setting('vpn_code', new_code)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="back_to_admin")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> VPN код сохранен: <code>{new_code}</code>",
        reply_markup=builder.as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "edit_vip_code")
async def edit_vip_vpn_code(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    current_code = get_setting('vip_vpn_code')

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['star']}\">⭐</tg-emoji> <b>Изменение VIP VPN кода</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Текущий код: <code>{current_code if current_code else 'Не установлен'}</code>\n\n"
        f"Этот код выдается только тем, кто подписался на все VIP каналы (/vip).\n"
        f"Отправьте новый VIP VPN код или /cancel для отмены."
    )
    await state.set_state(AdminStates.waiting_for_vip_vpn_code)
    await call.answer()

@dp.message(AdminStates.waiting_for_vip_vpn_code)
async def process_vip_vpn_code(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    new_code = message.text.strip()
    set_setting('vip_vpn_code', new_code)

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="back_to_admin")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> VIP VPN код сохранен: <code>{new_code}</code>",
        reply_markup=builder.as_markup()
    )
    await state.clear()


@dp.callback_query(F.data == "add_addlist")
async def add_addlist_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['add']}\">➕</tg-emoji> <b>Добавление Addlist</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Шаг 1/2: отправьте <b>название</b> для отображения\n\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_addlist_name)
    await call.answer()

@dp.message(AdminStates.waiting_for_addlist_name)
async def process_addlist_name(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    name = message.text.strip()
    await state.update_data(name=name)
    
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['link']}\">🔗</tg-emoji> Шаг 2/2: отправьте <b>ссылку</b>:"
    )
    await state.set_state(AdminStates.waiting_for_addlist_link)

@dp.message(AdminStates.waiting_for_addlist_link)
async def process_addlist_link(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    link = message.text.strip()
    data = await state.get_data()
    name = data.get('name')
    
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                cur = conn.execute("SELECT MAX(position) FROM addlists")
                max_pos = cur.fetchone()[0]
                new_position = (max_pos + 1) if max_pos else 1
                
                conn.execute(
                    "INSERT INTO addlists (name, link, position) VALUES (?, ?, ?)",
                    (name, link, new_position)
                )
            
            builder = InlineKeyboardBuilder()
            builder.button(text="◀️ В меню", callback_data="back_to_admin")
            await message.answer(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Addlist успешно добавлен!</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📋 Название: {name}\n"
                f"🔗 Ссылка: {link}",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()

@dp.callback_query(F.data == "remove_addlist")
async def remove_addlist_start(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    addlists = get_addlists()
    if not addlists:
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="back_to_admin")
        await call.message.edit_text("❌ Список Addlist пуст.", reply_markup=builder.as_markup())
        await call.answer()
        return
    
    text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['remove']}\">➖</tg-emoji> <b>Выберите Addlist для удаления:</b>\n━━━━━━━━━━━━━━━\n"
    builder = InlineKeyboardBuilder()
    
    for addlist in addlists:
        builder.button(
            text=f"❌ {addlist[1]}",
            callback_data=f"del_addlist_{addlist[0]}"
        )
    
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(2)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("del_addlist_"))
async def delete_addlist(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    addlist_id = int(call.data.replace("del_addlist_", ""))
    
    with closing(sqlite3.connect('wwwnahnah.db')) as conn:
        try:
            with conn:
                conn.execute("DELETE FROM addlists WHERE id = ?", (addlist_id,))
            builder = InlineKeyboardBuilder()
            builder.button(text="◀️ В меню", callback_data="back_to_admin")
            await call.message.edit_text(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Addlist удален!",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            await call.answer(f"Ошибка: {str(e)}", show_alert=True)
    
    await call.answer()

@dp.callback_query(F.data == "broadcast")
async def broadcast_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    users = get_all_users()
    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['broadcast']}\">📢</tg-emoji> <b>Рассылка</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Получателей: <b>{len(users)}</b>\n\n"
        f"Отправьте сообщение (текст, фото, GIF, видео) для рассылки всем пользователям.\n"
        f"Premium эмодзи в тексте сохраняются автоматически — их увидят все, даже без Premium.\n"
        f"После отправки можно будет добавить кнопку-ссылку.\n\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_broadcast)
    await call.answer()

async def execute_broadcast(chat_id, message_id, progress_msg, reply_markup=None):
    users = get_all_users()
    success = 0
    failed = 0

    for user_id in users:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
            success += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            logging.error(f"Broadcast error for {user_id}: {e}")

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="back_to_admin")
    await progress_msg.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['stats']}\">📊</tg-emoji> <b>Рассылка завершена!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ Успешно: {success}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=builder.as_markup()
    )

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    await state.update_data(bc_chat_id=message.chat.id, bc_message_id=message.message_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить кнопку", callback_data="bc_add_button")
    builder.button(text="🚀 Отправить без кнопки", callback_data="bc_send_now")
    builder.adjust(1)

    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['message']}\">📨</tg-emoji> <b>Сообщение получено.</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Хотите добавить кнопку-ссылку под сообщением (например GIF + кнопка «Перейти»)?",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "bc_add_button")
async def broadcast_ask_button_text(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['edit']}\">✏️</tg-emoji> <b>Текст кнопки</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Отправьте текст, который будет на кнопке (например: «Перейти в канал»)\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_broadcast_button_text)
    await call.answer()

@dp.message(AdminStates.waiting_for_broadcast_button_text)
async def process_broadcast_button_text(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    await state.update_data(bc_button_text=message.text.strip())
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['link']}\">🔗</tg-emoji> Теперь отправьте <b>ссылку</b> для кнопки (https://...)"
    )
    await state.set_state(AdminStates.waiting_for_broadcast_button_url)

@dp.message(AdminStates.waiting_for_broadcast_button_url)
async def process_broadcast_button_url(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("t.me/") or url.startswith("tg://")):
        await message.answer("❌ Ссылка должна начинаться с https:// или t.me/. Попробуйте снова или /cancel.")
        return

    data = await state.get_data()
    button_text = data.get('bc_button_text', 'Перейти')
    chat_id = data.get('bc_chat_id')
    message_id = data.get('bc_message_id')

    button_builder = InlineKeyboardBuilder()
    button_builder.button(text=button_text, url=url)

    progress_msg = await message.answer(f"📤 Начинаю рассылку с кнопкой...")
    await execute_broadcast(chat_id, message_id, progress_msg, reply_markup=button_builder.as_markup())
    await state.clear()

@dp.callback_query(F.data == "bc_send_now")
async def broadcast_send_now(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    data = await state.get_data()
    chat_id = data.get('bc_chat_id')
    message_id = data.get('bc_message_id')

    if not chat_id or not message_id:
        await call.answer("❌ Сообщение не найдено, начните заново.", show_alert=True)
        await state.clear()
        return

    await call.message.edit_text(f"📤 Начинаю рассылку...")
    await execute_broadcast(chat_id, message_id, call.message, reply_markup=None)
    await state.clear()
    await call.answer()

@dp.callback_query(F.data == "stats")
async def show_stats(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    users = get_all_users()
    sponsors = get_sponsors()
    addlists = get_addlists()
    tgrass_enabled = get_tgrass_enabled()
    tgrass_count = get_tgrass_channel_count()
    tgrass_earnings = get_tgrass_earnings()
    piarflow_enabled = get_piarflow_enabled()
    piarflow_count = get_piarflow_channel_count()
    vip_channels = get_vip_channels()
    
    text = (
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['stats']}\">📊</tg-emoji> <b>Статистика бота</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: <b>{len(users)}</b>\n"
        f"📢 Спонсоров: <b>{len(sponsors)}</b>\n"
        f"📋 Addlist: <b>{len(addlists)}</b>\n"
        f"⭐ VIP каналов: <b>{len(vip_channels)}</b>\n"
        f"🌟 TGrass: {'✅ Включен' if tgrass_enabled else '❌ Выключен'}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['tgrass']}\">🌟</tg-emoji> TGrass каналов: <b>{tgrass_count}</b>\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['money']}\">💰</tg-emoji> Доход с TGrass: <b>{tgrass_earnings}</b>\n"
        f"💎 PiarFlow: {'✅ Включен' if piarflow_enabled else '❌ Выключен'}\n"
        f"💎 PiarFlow каналов: <b>{piarflow_count}</b>\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Обновить", callback_data="stats", icon_custom_emoji_id=EMOJI_IDS["refresh"])
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(2)
    
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "tgrass_settings")
async def tgrass_settings(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    enabled = get_tgrass_enabled()
    status_text = "✅ Включен" if enabled else "❌ Выключен"
    current_key = get_tgrass_api_key()
    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else current_key
    channel_count = get_tgrass_channel_count()
    earnings = get_tgrass_earnings()

    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Включить" if not enabled else "❌ Выключить",
        callback_data="toggle_tgrass"
    )
    builder.button(
        text="Обновить API ключ",
        callback_data="edit_tgrass_key",
        icon_custom_emoji_id=EMOJI_IDS["refresh"]
    )
    builder.button(
        text="Изменить доход",
        callback_data="edit_tgrass_earnings",
        icon_custom_emoji_id=EMOJI_IDS["money"]
    )
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(1)

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['tgrass']}\">🌟</tg-emoji> <b>Настройки TGrass</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Статус: {status_text}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['tgrass']}\">🌟</tg-emoji> Каналов сейчас: <b>{channel_count}</b>\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['money']}\">💰</tg-emoji> Доход с TGrass: <b>{earnings}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"API Key: <code>{masked_key}</code>",
        reply_markup=builder.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data == "edit_tgrass_earnings")
async def edit_tgrass_earnings_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    current = get_tgrass_earnings()

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['money']}\">💰</tg-emoji> <b>Изменение дохода TGrass</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Текущее значение: <b>{current}</b>\n\n"
        f"Отправьте новую сумму (например: 150.50)\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_tgrass_earnings)
    await call.answer()

@dp.message(AdminStates.waiting_for_tgrass_earnings)
async def process_tgrass_earnings(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    new_value = message.text.strip()
    set_tgrass_earnings(new_value)

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="back_to_admin")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Доход обновлен:</b> {new_value}",
        reply_markup=builder.as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "edit_tgrass_key")
async def edit_tgrass_key_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    current_key = get_tgrass_api_key()
    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else current_key

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['refresh']}\">🔄</tg-emoji> <b>Обновление TGrass API ключа</b>\n\n"
        f"Текущий ключ: <code>{masked_key}</code>\n\n"
        f"Отправьте новый API ключ.\n"
        f"Отправьте /cancel для отмены."
    )
    await state.set_state(AdminStates.waiting_for_tgrass_api_key)
    await call.answer()

@dp.message(AdminStates.waiting_for_tgrass_api_key)
async def process_tgrass_api_key(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    new_key = message.text.strip()

    if not new_key:
        await message.answer("❌ Ключ не может быть пустым. Попробуйте снова или /cancel.")
        return

    status_msg = await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['refresh']}\">🔄</tg-emoji> Проверка ключа..."
    )

    old_key = get_tgrass_api_key()
    set_tgrass_api_key(new_key)

    try:
        test_offers = check_tgrass_subscriptions(message.from_user.id, message.from_user.username, False)
        try:
            test_response_ok = True
            headers = {"accept": "application/json", "Content-Type": "application/json", "Auth": new_key}
            resp = requests.post(TGRASS_API_URL, json={"tg_user_id": int(message.from_user.id), "tg_login": message.from_user.username or "", "lang": "ru", "is_premium": False}, headers=headers, timeout=10)
            test_response_ok = resp.status_code == 200
        except Exception:
            test_response_ok = False

        if test_response_ok:
            await status_msg.edit_text(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Новый API ключ сохранен и работает!</b>\n\n"
                f"Получено предложений: {len(test_offers)}"
            )
        else:
            set_tgrass_api_key(old_key)
            await status_msg.edit_text(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">⚠️</tg-emoji> <b>Ключ не прошел проверку, изменения отменены.</b>\n\n"
                f"Проверьте правильность ключа и попробуйте снова."
            )
    except Exception as e:
        set_tgrass_api_key(old_key)
        logging.error(f"TGrass key test error: {e}")
        await status_msg.edit_text(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">⚠️</tg-emoji> Ошибка проверки ключа: {str(e)}\nИзменения отменены."
        )

    await state.clear()

@dp.callback_query(F.data == "toggle_tgrass")
async def toggle_tgrass(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return
    
    current = get_tgrass_enabled()
    set_tgrass_enabled(not current)
    
    new_status = "✅ Включен" if not current else "❌ Выключен"
    await call.answer(f"TGrass {new_status}!", show_alert=True)
    
    await tgrass_settings(call)

# ================= PIARFLOW ADMIN CALLBACK HANDLERS =================

@dp.callback_query(F.data == "piarflow_settings")
async def piarflow_settings(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    enabled = get_piarflow_enabled()
    status_text = "✅ Включен" if enabled else "❌ Выключен"
    current_key = get_piarflow_api_key()
    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else current_key
    channel_count = get_piarflow_channel_count()

    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Включить" if not enabled else "❌ Выключить",
        callback_data="toggle_piarflow"
    )
    builder.button(
        text="Обновить API ключ",
        callback_data="edit_piarflow_key",
        icon_custom_emoji_id=EMOJI_IDS["refresh"]
    )
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(1)

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['money']}\">💎</tg-emoji> <b>Настройки PiarFlow</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Статус: {status_text}\n"
        f"💎 Каналов сейчас: <b>{channel_count}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"API Key: <code>{masked_key}</code>",
        reply_markup=builder.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data == "toggle_piarflow")
async def toggle_piarflow(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    current = get_piarflow_enabled()
    set_piarflow_enabled(not current)

    new_status = "✅ Включен" if not current else "❌ Выключен"
    await call.answer(f"PiarFlow {new_status}!", show_alert=True)

    await piarflow_settings(call)

@dp.callback_query(F.data == "edit_piarflow_key")
async def edit_piarflow_key_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    current_key = get_piarflow_api_key()
    masked_key = f"{current_key[:8]}...{current_key[-4:]}" if len(current_key) > 12 else current_key

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['refresh']}\">🔄</tg-emoji> <b>Обновление PiarFlow API ключа</b>\n\n"
        f"Текущий ключ: <code>{masked_key}</code>\n\n"
        f"Отправьте новый API ключ.\n"
        f"Отправьте /cancel для отмены."
    )
    await state.set_state(AdminStates.waiting_for_piarflow_api_key)
    await call.answer()

@dp.message(AdminStates.waiting_for_piarflow_api_key)
async def process_piarflow_api_key(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    new_key = message.text.strip()

    if not new_key:
        await message.answer("❌ Ключ не может быть пустым. Попробуйте снова или /cancel.")
        return

    status_msg = await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['refresh']}\">🔄</tg-emoji> Проверка ключа..."
    )

    old_key = get_piarflow_api_key()
    set_piarflow_api_key(new_key)

    try:
        test_offers = check_piarflow_sponsors_raw(message.from_user.id, message.from_user.id, 5)
        try:
            headers = {"Authorization": f"Bearer {new_key}", "Content-Type": "application/json"}
            resp = requests.post(
                f"{PIARFLOW_API_URL}/sponsors",
                json={"user_id": int(message.from_user.id), "chat_id": int(message.from_user.id), "max_sponsors": 5},
                headers=headers,
                timeout=10
            )
            test_response_ok = resp.status_code == 200
        except Exception:
            test_response_ok = False

        if test_response_ok:
            await status_msg.edit_text(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> <b>Новый API ключ сохранен и работает!</b>\n\n"
                f"Получено предложений: {len(test_offers)}"
            )
        else:
            set_piarflow_api_key(old_key)
            await status_msg.edit_text(
                f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">⚠️</tg-emoji> <b>Ключ не прошел проверку, изменения отменены.</b>\n\n"
                f"Проверьте правильность ключа и попробуйте снова."
            )
    except Exception as e:
        set_piarflow_api_key(old_key)
        logging.error(f"PiarFlow key test error: {e}")
        await status_msg.edit_text(
            f"<tg-emoji emoji-id=\"{EMOJI_IDS['warning']}\">⚠️</tg-emoji> Ошибка проверки ключа: {str(e)}\nИзменения отменены."
        )

    await state.clear()

@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await call.message.edit_text(
        await build_admin_panel_text(),
        reply_markup=build_admin_panel_keyboard()
    )
    await call.answer()

# ================= ADMIN GOŞMAK / AÝYRMAK =================
@dp.callback_query(F.data == "admin_menu")
async def admin_menu(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    admin_ids = get_admin_ids()
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить админа", callback_data="add_admin", icon_custom_emoji_id=EMOJI_IDS["add"])
    builder.button(text="➖ Удалить админа", callback_data="remove_admin", icon_custom_emoji_id=EMOJI_IDS["remove"])
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(1)

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['admin']}\">👑</tg-emoji> <b>Администраторы</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Всего админов: <b>{len(admin_ids)}</b>\n"
        f"Владелец (не удаляется): <code>{ADMIN_IDS[0]}</code>",
        reply_markup=builder.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data == "add_admin")
async def add_admin_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['add']}\">➕</tg-emoji> <b>Добавление админа</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Отправьте Telegram ID пользователя (число).\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_add_admin_id)
    await call.answer()

@dp.message(AdminStates.waiting_for_add_admin_id)
async def process_add_admin(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    text = message.text.strip()
    if not text.lstrip("-").isdigit():
        await message.answer("❌ ID должен быть числом. Попробуйте снова или /cancel.")
        return

    new_admin_id = int(text)
    add_admin(new_admin_id, message.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="admin_menu")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Пользователь <code>{new_admin_id}</code> теперь администратор!",
        reply_markup=builder.as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "remove_admin")
async def remove_admin_start(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    extra_admins = get_extra_admins()
    if not extra_admins:
        builder = InlineKeyboardBuilder()
        builder.button(text="◀️ Назад", callback_data="admin_menu")
        await call.message.edit_text("❌ Нет дополнительных админов для удаления.", reply_markup=builder.as_markup())
        await call.answer()
        return

    builder = InlineKeyboardBuilder()
    for admin_id in extra_admins:
        builder.button(text=f"❌ {admin_id}", callback_data=f"del_admin_{admin_id}")
    builder.button(text="◀️ Назад", callback_data="admin_menu")
    builder.adjust(2)

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['remove']}\">➖</tg-emoji> <b>Выберите админа для удаления:</b>",
        reply_markup=builder.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data.startswith("del_admin_"))
async def delete_admin_callback(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    target_id = int(call.data.replace("del_admin_", ""))
    if target_id in ADMIN_IDS:
        await call.answer("❌ Владельца нельзя удалить!", show_alert=True)
        return

    remove_admin(target_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="admin_menu")
    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Админ <code>{target_id}</code> удален!",
        reply_markup=builder.as_markup()
    )
    await call.answer()

# ================= VPN SATYŞ SAZLAMALARY (admin) =================
@dp.callback_query(F.data == "vpn_sale_menu")
async def vpn_sale_menu(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    code = get_vpn_sale_code()
    price = get_vpn_sale_price()
    sales_count, sales_stars = get_vpn_sales_stats()

    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить код", callback_data="edit_vpn_sale_code", icon_custom_emoji_id=EMOJI_IDS["edit"])
    builder.button(text="Изменить цену", callback_data="edit_vpn_sale_price", icon_custom_emoji_id=EMOJI_IDS["money"])
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(1)

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['vpn']}\">✔️</tg-emoji> <b>Продажа VPN за Telegram Stars</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Код: <code>{code or 'не задан'}</code>\n"
        f"Цена: ⭐ <b>{price}</b>\n"
        f"Продаж: <b>{sales_count}</b> (⭐{sales_stars} всего)\n\n"
        f"Пользователи покупают код через /buyvpn.",
        reply_markup=builder.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data == "edit_vpn_sale_code")
async def edit_vpn_sale_code_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['edit']}\">✏️</tg-emoji> Отправьте новый VPN код для продажи.\n/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_vpn_sale_code)
    await call.answer()

@dp.message(AdminStates.waiting_for_vpn_sale_code)
async def process_vpn_sale_code(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    set_vpn_sale_code(message.text.strip())
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="vpn_sale_menu")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Код для продажи обновлён!",
        reply_markup=builder.as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "edit_vpn_sale_price")
async def edit_vpn_sale_price_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['money']}\">💰</tg-emoji> Отправьте новую цену в Stars (целое число).\n/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_vpn_sale_price)
    await call.answer()

@dp.message(AdminStates.waiting_for_vpn_sale_price)
async def process_vpn_sale_price(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("❌ Цена должна быть положительным числом. Попробуйте снова или /cancel.")
        return

    set_vpn_sale_price(int(text))
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="vpn_sale_menu")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Цена обновлена: ⭐ {text}",
        reply_markup=builder.as_markup()
    )
    await state.clear()

# ================= AWTO-HABAR (her 3 sagatdan kanallara) =================
@dp.callback_query(F.data == "autonews_menu")
async def autonews_menu(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    channels = get_bot_channels()
    enabled = get_autonews_enabled()
    news_chat_id, news_msg_id = get_autonews_content()

    builder = InlineKeyboardBuilder()
    builder.button(text="Задать пост", callback_data="set_autonews", icon_custom_emoji_id=EMOJI_IDS["edit"])
    builder.button(text=("Выключить" if enabled else "Включить"), callback_data="toggle_autonews", icon_custom_emoji_id=EMOJI_IDS["refresh"])
    builder.button(text="Отправить сейчас", callback_data="autonews_send_now", icon_custom_emoji_id=EMOJI_IDS["broadcast"])
    builder.button(text="◀️ Назад", callback_data="back_to_admin")
    builder.adjust(1)

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['broadcast']}\">📢</tg-emoji> <b>Авто-рассылка в каналы</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Бот админ в каналах: <b>{len(channels)}</b>\n"
        f"Пост задан: {'✅' if news_msg_id else '❌'}\n"
        f"Статус: {'✅ Включена (каждые 3 часа)' if enabled else '❌ Выключена'}",
        reply_markup=builder.as_markup()
    )
    await call.answer()

@dp.callback_query(F.data == "set_autonews")
async def set_autonews_start(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    await call.message.edit_text(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['edit']}\">✏️</tg-emoji> <b>Пост для авто-рассылки</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Отправьте сообщение (текст, фото, видео) — оно будет автоматически "
        f"публиковаться во все каналы, где бот админ, каждые 3 часа.\n\n"
        f"/cancel — отменить"
    )
    await state.set_state(AdminStates.waiting_for_autonews_content)
    await call.answer()

@dp.message(AdminStates.waiting_for_autonews_content)
async def process_autonews_content(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return

    set_autonews_content(message.chat.id, message.message_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ В меню", callback_data="autonews_menu")
    await message.answer(
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['success']}\">✅</tg-emoji> Пост для авто-рассылки сохранён!",
        reply_markup=builder.as_markup()
    )
    await state.clear()

@dp.callback_query(F.data == "toggle_autonews")
async def toggle_autonews(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    news_chat_id, news_msg_id = get_autonews_content()
    if not news_msg_id and not get_autonews_enabled():
        await call.answer("❌ Сначала задайте пост для рассылки.", show_alert=True)
        return

    set_autonews_enabled(not get_autonews_enabled())
    await autonews_menu(call)

@dp.callback_query(F.data == "autonews_send_now")
async def autonews_send_now(call: CallbackQuery):
    if call.from_user.id not in get_admin_ids():
        await call.answer("❌ Доступ запрещен!", show_alert=True)
        return

    sent, failed = await execute_autonews_broadcast()
    await call.answer(f"✅ Отправлено: {sent}, ошибок: {failed}", show_alert=True)

async def execute_autonews_broadcast():
    """Bot-yň admin bolan ähli kanallaryna sazlanan habary iberýär."""
    news_chat_id, news_msg_id = get_autonews_content()
    if not news_msg_id:
        return 0, 0

    channels = get_bot_channels()
    sent, failed = 0, 0
    for chat_id, title in channels:
        try:
            await bot.copy_message(chat_id=chat_id, from_chat_id=news_chat_id, message_id=news_msg_id)
            sent += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            failed += 1
            logging.error(f"Autonews error for channel {chat_id} ({title}): {e}")
    return sent, failed

async def autonews_scheduler():
    """Her 3 sagatdan (10800 sekunt) bot-yň admin bolan kanallaryna awto-habar iberýär."""
    while True:
        await asyncio.sleep(10800)
        if get_autonews_enabled():
            await execute_autonews_broadcast()

async def main():
    keep_alive()
    asyncio.create_task(autonews_scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())