import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
import random
import string
import uuid
import aiohttp 
import os
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, types, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.types import Message, CallbackQuery, Chat, User, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError, ClientDecodeError
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable, Union

# milas_devx
BOT_TOKEN = "8842438618:AAGk3DQyNaYppuCZNLRXJdzJfXDTrGGPdI8"
ADMIN_IDS = [7569831989]
CHIEF_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None
ADMIN_CHANNEL_ID = -1004358812003
PAYMENTS_CHANNEL_ID = -1003870504084
PAYMENTS_CHANNEL_LINK = "https://t.me/MAREO_STARSPAY"
MIN_REFERRALS_FOR_WITHDRAWAL = 0
DB_FILE = "MareoStars.db"

# milas
START_PHOTO_URL = "https://freeimage.host/i/CkFEO4S"

# milas
TGRASS_API_KEY = "4a1f3982b48c482391b0d857439327e1"

# flyer api
FLYER_API_KEY = "FL-pndrjg-ntIPBY-zRAOfM-ELiFkA"

# piarflow
PIARFLOW_API_KEY = "_qyZYD5EoxHImjEv37nRTbKkrYMGQP-7"
PIARFLOW_API_URL = "https://piarflow.com/v1"

# milas - CUSTOM EMOJILER
EMOJI_IDS = {
    "start": "5895288332581082241",
    "star": "5258185631355378853",
    "withdraw": "6039573425268201570",
    "profile": "5316727448644103237",
    "bonus": "6032644646587338669",
    "promo": "5382327529287720847",
    "top": "5440539497383087970",
    "back": "5983506750387523533",
    "check": "5206607081334906820",
    "lock": "5463200466391298413",
    "stats": "5936143551854285132",
    "refresh": "6030657343744644592",
    "broadcast": "6021418126061605425",
    "edit": "5359488727158634349",
    "add": "5359651386160068849",
    "remove": "5359651386160068849",
    "list": "6030657343744644592",
    "warning": "5463200466391298413",
    "success": "5206607081334906820",
    "money": "5936143551854285132",
    "phone": "6021418126061605425",
    "people": "5463200466391298413",
    "history": "6030657343744644592",
    "info": "5359488727158634349",
    "time": "6030657343744644592",
    "link": "5271604874419647061",
    "profile_icon": "5373012449597335010",
    "id_icon": "5445353829304387411",
    "balance_icon": "5287231198098117669",
    "star_icon": "5954135079662916434",
    "friends_icon": "5372926953978341366",
    "gift_icon": "5850323366476519158",
    "celebration": "5461151367559141950",
    "warning_icon": "5274099962655816924",
    "check_premium": "5427009714745517609",
    "user_icon": "5373012449597335010",
    "star_premium": "5954135079662916434",
    "status_icon": "5264727218734524899",
    "gear_icon": "5341715473882955310",
    "gift_sent": "5199749070830197566",
    "declined": "5825434739665803309",
    "rose": "5280947338821524402",
    "bouquet": "5280774333243873175",
    "trophy": "5280769763398671636",
    "card_icon": "5445353829304387411",
    "star_premium_icon": "5954135079662916434",
    "status_wait": "5341715473882955310",
    "db_download": "6039802767931871481",
    "db_upload": "5963103826075456248"
}

# --- METİNLER ---
TEXTS = {
    "start": "<tg-emoji emoji-id=\"{start_emoji}\">😎</tg-emoji> <b>Hoş geldiňiz!</b>",
    "profile": "<tg-emoji emoji-id=\"{profile_icon}\">👤</tg-emoji> <b>Ady:</b> @{username}\n"
               "<tg-emoji emoji-id=\"{id_icon}\">💳</tg-emoji> <b>ID:</b> <code>{user_id}</code>\n"
               "<tg-emoji emoji-id=\"{balance_icon}\">💰</tg-emoji> <b>Balans:</b> {balance} <tg-emoji emoji-id=\"{star_icon}\">⭐️</tg-emoji>\n"
               "<tg-emoji emoji-id=\"{friends_icon}\">👥</tg-emoji> <b>Çagyrylan dostlar:</b> {referrals_count}",
    "invite": "<tg-emoji emoji-id=\"{star_emoji}\">⭐️</tg-emoji> <b>Dostlaryňy çagyr</b>\n\n"
              "Siziň ssylkaňyzdan geçen her bir dostuň üçin <b>{ref_bonus}</b> <tg-emoji emoji-id=\"{star_emoji}\">⭐️</tg-emoji> alýarsyň!\n\n"
              "<tg-emoji emoji-id=\"{link_emoji}\">🔗</tg-emoji> <b>Siziň referal ssylkaňyz:</b>\n"
              "<code>{ref_link}</code>\n\n"
              "<tg-emoji emoji-id=\"{celebration_emoji}\">🎉</tg-emoji> Dostlaryňy bu ssylka arkaly çagyr, ony ähli toparlara ugrat we Ýyldyz gazan!",
    "withdraw_title": "<tg-emoji emoji-id=\"{withdraw_emoji}\">📤</tg-emoji> <b>Serişdeleri çykarmak</b>\n\nÝyldyzlaryňyzy sowgatlaryň deregine çalşyň!\n\n"
                      "<blockquote><tg-emoji emoji-id=\"{card_icon}\">💳</tg-emoji> <b>Siziň balansyňyz:</b> {balance} <tg-emoji emoji-id=\"{star_premium_icon}\">⭐️</tg-emoji></blockquote>\n\n",
    "bonus": "<tg-emoji emoji-id=\"{bonus_emoji}\">🎁</tg-emoji> <b>Gündelik bonus</b>\n\n"
             "<blockquote>Siz her 24 sagatdan bir gezek tötänleýin bonus alyp bilersiňiz! Bagtyňyzy synamak üçin düwmä basyň.</blockquote>",
    "bonus_claimed": "🎁 Gutlaýarys! Siz {bonus_amount} ⭐ aldyňyz!",
    "bonus_wait": "😔 Indiki bonus {hours} sag. {minutes} min. soňra.",
    "promo": "<tg-emoji emoji-id=\"{gift_icon}\">🎁</tg-emoji> <b>Promokody giriziň:</b>\n\n<blockquote>Mysal üçin: <code>STAR50</code></blockquote>",
    "promo_success": "✅ Promokod işjeňleşdirildi! Size {reward} ⭐ berildi.",
    "promo_fail_used": "🚫 Siz bu promokody eýýäm ulandyňyz.",
    "promo_fail_general": "❌ Promokod ýok ýa-da möhleti gutarypdyr.",
    "top": "<tg-emoji emoji-id=\"{top_emoji}\">🥇</tg-emoji> <b>Iň gowy ulanyjylar</b>\n\n<blockquote>Bu ýerde iň işjeň kim? Ýyldyzlar we çakylyklar boýunça öňdebaryjylary biliň.</blockquote>",
    "top_balance_title": "<tg-emoji emoji-id=\"{top_emoji}\">🥇</tg-emoji> <b>Ýyldyzlar boýunça Top-5:</b>\n\n",
    "top_referrals_title": "<tg-emoji emoji-id=\"{top_emoji}\">🥇</tg-emoji> <b>24 sagadyň içinde Top 5 referal:</b>\n\n",
    "top_no_users": "<i>Hiç kim ýok.</i>",
    "top_not_in_top": "\n\n🚫 Siz topa girmediňiz! | 24 sag. içinde {count} referal.",
    "request_submitted_for_review": "✅ Siziň <code>#{request_uid}</code> belgili islegiňiz gözden geçirmek üçin ugradyldy. Birnäçe günüň dowamynda adminden tassyklama garaşyň.",
    "btn_earn": "Dostuňy çagyr",
    "btn_withdraw": "Çykarmak",
    "btn_profile": "Meniň profilim",
    "btn_bonus": "Bonus",
    "btn_promo": "Promokod",
    "btn_top": "Top",
    "btn_invite": "Dostlaryňy çagyr",
    "btn_back": "Yza",
    "btn_back_to_menu": "Menýua dolanmak",
    "btn_copy_link": "Referal çelgisi",
    "btn_cancel": "Ýatyr",
    "btn_top_balance": "Ýyldyzlar boýunça top",
    "btn_top_referrals": "Referallar boýunça top",
    "btn_check_status": "Tölegler kanaly",
    "sub_check_fail": "<tg-emoji emoji-id=\"{warning_icon}\">❗️</tg-emoji> <b>Boty ulanmak üçin kanallara agza bolmaly:</b>",
    "sub_check_button": "Men agza boldum",
    "sub_check_success": "✅ Agza bolanyňyz üçin sag boluň!",
    "sub_check_not_yet": "❗️ Siz entek ähli kanallara agza bolmadyňyz.",
    "referral_notification": "🎉 Siziň ssylkaňyz arkaly täze ulanyjy goşuldy: {new_user_display}!\nSize <b>{ref_bonus}</b> ⭐ berildi.",
    "alert_action_canceled": "Hereket ýatyryldy",
    "alert_need_more_refs": "❗️ Çykarmak üçin ýene-de {diff} dost çagyrmaly.",
    "alert_pending_withdrawal": "❗️ Siziň eýýäm gözden geçirilýän islegiňiz bar.",
    "alert_insufficient_stars": "❌ Iň pes çykaryş möçberi 25⭐. Sizde: {balance}⭐",
    "status_approved": "✅ Siziň islegiňiz (#{uid}) tassyklandy! «{gift_name}» üçin {amount} ⭐ aýryldy.",
    "status_declined": "❌ Siziň islegiňiz (#{uid}) ret edildi.\n\nSebäbi: {reason}",
    "link_copied": "✅ Referal ssylka kopýalandy!",
}

def get_text(key: str, **kwargs):
    text = TEXTS.get(key, f"_{key}_")
    if kwargs:
        return text.format(**kwargs)
    return text

# --- ВЫВОД СПОНСОРОВ В 2 СТОЛБИКА С ПРЕМ ЭМОДЗИ ---
def get_subscription_kb(not_subscribed_list):
    builder = InlineKeyboardBuilder()
    sizes = []
    s_count = len(not_subscribed_list)
    
    for channel in not_subscribed_list:
        emoji_id = channel.get('icon_custom_emoji_id', "6039381989985882045")
        builder.button(
            text=f"{channel['name']}", 
            url=channel['url'], 
            icon_custom_emoji_id=emoji_id, 
            style="primary"
        )
    
    # Расчитываем 2 столбца
    while s_count > 0:
        if s_count >= 2:
            sizes.append(2)
            s_count -= 2
        else:
            sizes.append(1)
            s_count -= 1
            
    # Кнопка проверки в самом низу
    builder.button(text=get_text('sub_check_button'), callback_data="check_subscription", icon_custom_emoji_id=EMOJI_IDS["check"], style="success")
    sizes.append(1)
    
    builder.adjust(*sizes)
    return builder.as_markup()

# --- BUTONLAR ---
def get_main_menu_kb():
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=get_text('btn_earn'), 
        callback_data="earn", 
        icon_custom_emoji_id=EMOJI_IDS["star"],
        style="success"
    )
    
    builder.button(
        text=get_text('btn_profile'), 
        callback_data="profile", 
        icon_custom_emoji_id=EMOJI_IDS["profile"],
        style="danger"
    )
    
    builder.button(
        text=get_text('btn_withdraw'), 
        callback_data="withdraw", 
        icon_custom_emoji_id=EMOJI_IDS["withdraw"],
        style="danger"
    )
    
    builder.button(
        text=get_text('btn_top'), 
        callback_data="top_referrals",
        icon_custom_emoji_id=EMOJI_IDS["top"],
        style="primary"
    )
    
    builder.adjust(1, 2, 1)
    return builder.as_markup()

def get_profile_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_bonus'), callback_data="bonus", icon_custom_emoji_id=EMOJI_IDS["bonus"], style="success")
    builder.button(text=get_text('btn_promo'), callback_data="promo", icon_custom_emoji_id=EMOJI_IDS["promo"], style="primary")
    builder.button(text=get_text('btn_back_to_menu'), callback_data="main_menu", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_invite_kb(ref_link: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text('btn_copy_link'), 
        copy_text=CopyTextButton(text=ref_link),
        style="primary"
    )
    builder.button(
        text=get_text('btn_back'), 
        callback_data="main_menu", 
        icon_custom_emoji_id=EMOJI_IDS["back"],
        style="danger"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_back_kb(callback_data="main_menu"):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_back'), callback_data=callback_data, icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    return builder.as_markup()

def get_withdraw_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="25 ⭐", callback_data="withdraw_gift_25_🌹", icon_custom_emoji_id=EMOJI_IDS["rose"], style="primary")
    builder.button(text="50 ⭐", callback_data="withdraw_gift_50_💐", icon_custom_emoji_id=EMOJI_IDS["bouquet"], style="primary")
    builder.button(text="100 ⭐", callback_data="withdraw_gift_100_🏆", icon_custom_emoji_id=EMOJI_IDS["trophy"], style="primary")
    builder.button(text=get_text('btn_back'), callback_data="main_menu", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_withdraw_submitted_kb():
    builder = InlineKeyboardBuilder()
    if PAYMENTS_CHANNEL_LINK and "YourPaymentsChannel" not in PAYMENTS_CHANNEL_LINK:
        builder.button(text=get_text('btn_check_status'), url=PAYMENTS_CHANNEL_LINK, icon_custom_emoji_id=EMOJI_IDS["money"], style="success")
    builder.button(text=get_text('btn_back_to_menu'), callback_data="main_menu", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    return builder.as_markup()

def get_cancel_kb(callback_data="cancel_action"):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_cancel'), callback_data=callback_data, icon_custom_emoji_id=EMOJI_IDS["remove"], style="danger")
    return builder.as_markup()

def get_admin_kb(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Hat ýaýratmak", callback_data="admin_broadcast", icon_custom_emoji_id=EMOJI_IDS["broadcast"], style="primary")
    builder.button(text="Statistika", callback_data="admin_stats", icon_custom_emoji_id=EMOJI_IDS["stats"], style="primary")
    builder.button(text="Bonus sazlamalary", callback_data="admin_bonus_settings", icon_custom_emoji_id=EMOJI_IDS["edit"], style="primary")
    builder.button(text="Promokodlar", callback_data="admin_promo_menu", icon_custom_emoji_id=EMOJI_IDS["promo"], style="primary")
    builder.button(text="Kanallar", callback_data="admin_req_subs", icon_custom_emoji_id=EMOJI_IDS["lock"], style="primary")
    builder.button(text="Balans", callback_data="admin_balance_change", icon_custom_emoji_id=EMOJI_IDS["money"], style="primary")
    builder.button(text="Referal bonusy", callback_data="admin_ref_bonus", icon_custom_emoji_id=EMOJI_IDS["star"], style="primary")    
    if db.is_chief_admin(user_id):
        builder.button(text="Adminler", callback_data="admin_manage_admins", icon_custom_emoji_id=EMOJI_IDS["lock"], style="primary")
    builder.button(text="DB ýükläp al", callback_data="admin_download_db", icon_custom_emoji_id=EMOJI_IDS["db_download"], style="primary")
    builder.button(text="DB gurna", callback_data="admin_upload_db", icon_custom_emoji_id=EMOJI_IDS["db_upload"], style="primary")
    builder.adjust(2)
    return builder.as_markup()

def get_back_to_admin_panel_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Admin-panele dolan", callback_data="admin_panel", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    return builder.as_markup()

def get_admin_withdraw_kb(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Tassykla", callback_data=f"withdraw_approve_{request_id}", icon_custom_emoji_id=EMOJI_IDS["check"], style="success")
    builder.button(text="Ret et", callback_data=f"withdraw_decline_{request_id}", icon_custom_emoji_id=EMOJI_IDS["remove"], style="danger")
    builder.adjust(2)
    return builder.as_markup()

def get_payment_channel_kb(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ugrat", callback_data=f"payment_send_{request_id}", style="success")
    builder.button(text="❌ Ret et", callback_data=f"payment_decline_{request_id}", style="danger")
    builder.adjust(2)
    return builder.as_markup()

def get_payment_channel_status_text(request_id: int, user_id: int, amount: float, gift_name: str, status: str = "pending"):
    username = db.get_user_username(user_id)
    
    if status == "pending":
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['status_icon']}\">🔄</tg-emoji> Işlenilmegine garaşylýar <tg-emoji emoji-id=\"{EMOJI_IDS['status_wait']}\">⚙️</tg-emoji>"
    elif status == "sent":
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['gift_sent']}\">🎁</tg-emoji> Sowgat ugradyldy"
    elif status == "declined":
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['declined']}\">🚫</tg-emoji> Ret edildi"
    else:
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['status_icon']}\">🔄</tg-emoji> Işlenilmegine garaşylýar"
    
    text = (
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['check_premium']}\">✅</tg-emoji> <b>Çykarmak üçin isleg №{request_id}</b>\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['user_icon']}\">👤</tg-emoji> <b>Ulanyjy:</b> @{username} | ID {user_id}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['star_premium']}\">⭐️</tg-emoji> <b>Möçberi:</b> {amount} ⭐\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['gift_icon']}\">🎁</tg-emoji> <b>Sowgat:</b> {gift_name}\n\n"
        f"{status_text}"
    )
    return text

# --- VERİTABANI ---
class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.setup_database()

    def setup_database(self):
        with self.connection:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance REAL DEFAULT 0,
                    referrer_id INTEGER,
                    last_bonus_time DATETIME,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    referral_processed BOOLEAN DEFAULT 0
                )''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS used_promocodes (user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code))''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT NOT NULL UNIQUE,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    amount REAL NOT NULL,
                    gift_name TEXT,
                    status TEXT DEFAULT 'pending',
                    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    decline_reason TEXT,
                    details TEXT,
                    payment_channel_message_id INTEGER
                )''')
            try: self.cursor.execute("ALTER TABLE withdrawal_requests ADD COLUMN decline_reason TEXT")
            except: pass
            try: self.cursor.execute("ALTER TABLE withdrawal_requests ADD COLUMN details TEXT")
            except: pass
            try: self.cursor.execute("ALTER TABLE withdrawal_requests ADD COLUMN payment_channel_message_id INTEGER")
            except: pass
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, reward REAL, activations_left INTEGER)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS required_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT NOT NULL, channel_id TEXT NOT NULL UNIQUE, channel_url TEXT NOT NULL)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, is_chief BOOLEAN DEFAULT 0)''')
            self.set_setting_if_not_exists('ref_bonus', '1.5')
            self.set_setting_if_not_exists('daily_bonus_min', '0.1')
            self.set_setting_if_not_exists('daily_bonus_max', '0.2')
            if CHIEF_ADMIN_ID:
                self.cursor.execute("UPDATE admins SET is_chief = 0")
                self.cursor.execute("INSERT OR REPLACE INTO admins (user_id, is_chief) VALUES (?, 1)", (CHIEF_ADMIN_ID,))

    def add_user(self, user: User, referrer_id=None):
        with self.connection:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, referrer_id) VALUES (?, ?, ?, ?)",
                               (user.id, user.username, user.first_name, referrer_id))

    def update_user_info(self, user_id: int, username: str, first_name: str):
        with self.connection:
            self.cursor.execute("UPDATE users SET username = ?, first_name = ? WHERE user_id = ?", (username, first_name, user_id))

    def is_admin(self, user_id: int) -> bool:
        self.cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def is_chief_admin(self, user_id: int) -> bool:
        self.cursor.execute("SELECT is_chief FROM admins WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] == 1 if result else False

    def get_admins(self) -> list:
        self.cursor.execute("SELECT user_id, is_chief FROM admins")
        return self.cursor.fetchall()

    def add_admin(self, user_id: int):
        with self.connection: self.cursor.execute("INSERT OR IGNORE INTO admins (user_id, is_chief) VALUES (?, 0)", (user_id,))

    def remove_admin(self, user_id: int):
        with self.connection: self.cursor.execute("DELETE FROM admins WHERE user_id = ? AND is_chief = 0", (user_id,))

    def get_user_referral_info(self, user_id):
        self.cursor.execute("SELECT referrer_id, referral_processed FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def mark_referral_as_processed(self, user_id):
        with self.connection: self.cursor.execute("UPDATE users SET referral_processed = 1 WHERE user_id = ?", (user_id,))

    def add_required_channel(self, name, channel_id, channel_url):
        with self.connection: self.cursor.execute("INSERT INTO required_channels (channel_name, channel_id, channel_url) VALUES (?, ?, ?)",(name, channel_id, channel_url))

    def get_required_channels(self):
        self.cursor.execute("SELECT id, channel_name, channel_id, channel_url FROM required_channels")
        return self.cursor.fetchall()

    def delete_required_channel(self, channel_pk_id):
        with self.connection: self.cursor.execute("DELETE FROM required_channels WHERE id = ?", (channel_pk_id,))

    def create_withdrawal_request(self, user_id, username, amount, gift_name, details=None):
        with self.connection:
            request_uid = str(uuid.uuid4()).split('-')[0]
            self.cursor.execute("INSERT INTO withdrawal_requests (uid, user_id, username, amount, gift_name, details) VALUES (?, ?, ?, ?, ?, ?)", 
                               (request_uid, user_id, username, amount, gift_name, details))
            request_id = self.cursor.lastrowid
            return request_id, request_uid

    def get_withdrawal_request(self, request_id):
        self.cursor.execute("SELECT id, uid, user_id, username, amount, gift_name, status, decline_reason, details, payment_channel_message_id FROM withdrawal_requests WHERE id = ?", (request_id,))
        return self.cursor.fetchone()

    def get_withdrawal_request_by_id(self, request_id):
        self.cursor.execute("SELECT id, uid, user_id, username, amount, gift_name, status, decline_reason, details, payment_channel_message_id FROM withdrawal_requests WHERE id = ?", (request_id,))
        return self.cursor.fetchone()

    def update_withdrawal_status(self, request_id, status, reason=None):
        with self.connection: 
            self.cursor.execute("UPDATE withdrawal_requests SET status = ?, decline_reason = ? WHERE id = ?", (status, reason, request_id))

    def update_payment_channel_message_id(self, request_id, message_id):
        with self.connection:
            self.cursor.execute("UPDATE withdrawal_requests SET payment_channel_message_id = ? WHERE id = ?", (message_id, request_id))

    def has_pending_withdrawal(self, user_id: int) -> bool:
        self.cursor.execute("SELECT 1 FROM withdrawal_requests WHERE user_id = ? AND status = 'pending' LIMIT 1", (user_id,))
        return self.cursor.fetchone() is not None

    def set_setting_if_not_exists(self, key, value):
        with self.connection: self.cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def get_setting(self, key):
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def set_setting(self, key, value):
        with self.connection: self.cursor.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def user_exists(self, user_id):
        self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def get_user_balance(self, user_id):
        self.cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_user_display_name(self, user_id):
        self.cursor.execute("SELECT username, first_name FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        if result:
            return f"@{result[0]}" if result[0] else html.quote(result[1])
        return f"User {user_id}"

    def get_user_username(self, user_id):
        self.cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else str(user_id)

    def update_balance(self, user_id, amount):
        with self.connection: self.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))

    def get_referrals_count(self, user_id):
        self.cursor.execute("SELECT COUNT(user_id) FROM users WHERE referrer_id = ? AND referral_processed = 1", (user_id,))
        return self.cursor.fetchone()[0]

    def get_referrals_count_last_24h(self, user_id):
        last_24h = datetime.now() - timedelta(hours=24)
        self.cursor.execute("""
            SELECT COUNT(user_id) FROM users 
            WHERE referrer_id = ? AND referral_processed = 1 AND join_date >= ?
        """, (user_id, last_24h.isoformat()))
        return self.cursor.fetchone()[0]

    def get_top_by_referrals_last_24h(self, limit=5):
        last_24h = datetime.now() - timedelta(hours=24)
        self.cursor.execute("""
            SELECT u.referrer_id, COUNT(u.user_id) as ref_count, ref.username, ref.first_name
            FROM users u
            JOIN users ref ON u.referrer_id = ref.user_id
            WHERE u.referrer_id IS NOT NULL AND u.referral_processed = 1 AND u.join_date >= ?
            GROUP BY u.referrer_id
            ORDER BY ref_count DESC
            LIMIT ?
        """, (last_24h.isoformat(), limit))
        return self.cursor.fetchall()

    def get_last_bonus_time(self, user_id):
        self.cursor.execute("SELECT last_bonus_time FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return datetime.fromisoformat(result[0]) if result and result[0] else None

    def update_last_bonus_time(self, user_id):
        with self.connection: self.cursor.execute("UPDATE users SET last_bonus_time = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))

    def get_top_by_balance(self, limit=5):
        self.cursor.execute("SELECT user_id, balance, username, first_name FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_all_user_ids(self):
        self.cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in self.cursor.fetchall()]

    def get_stats(self):
        self.cursor.execute("SELECT COUNT(user_id) FROM users")
        total_users = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(user_id) FROM users WHERE join_date >= date('now', '-24 hours')")
        new_users_24h = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT SUM(balance) FROM users")
        total_balance = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT status, COUNT(*) FROM withdrawal_requests GROUP BY status")
        withdraw_counts = {s: c for s, c in self.cursor.fetchall()}
        self.cursor.execute("SELECT SUM(amount) FROM withdrawal_requests WHERE status = 'approved'")
        withdrawn_sum = self.cursor.fetchone()[0]
        return {"total_users": total_users, "new_users_24h": new_users_24h, "total_balance": round(total_balance or 0, 2), 
                "withdraw_pending": withdraw_counts.get('pending', 0), "withdraw_approved": withdraw_counts.get('approved', 0), 
                "withdraw_declined": withdraw_counts.get('declined', 0), "withdrawn_sum": round(withdrawn_sum or 0, 2)}

    def create_promocode(self, code, reward, activations):
        with self.connection: self.cursor.execute("INSERT OR REPLACE INTO promocodes (code, reward, activations_left) VALUES (?, ?, ?)", (code, reward, activations))

    def get_promocode(self, code):
        self.cursor.execute("SELECT reward, activations_left FROM promocodes WHERE code = ?", (code,))
        return self.cursor.fetchone()

    def use_promocode(self, user_id, code):
        with self.connection:
            self.cursor.execute("UPDATE promocodes SET activations_left = activations_left - 1 WHERE code = ?", (code,))
            self.cursor.execute("INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)", (user_id, code))

    def has_user_used_promo(self, user_id, code):
        self.cursor.execute("SELECT 1 FROM used_promocodes WHERE user_id = ? AND code = ?", (user_id, code))
        return self.cursor.fetchone() is not None

    def get_all_promocodes(self):
        self.cursor.execute("SELECT code, reward, activations_left FROM promocodes ORDER BY code")
        return self.cursor.fetchall()

    def delete_promocode(self, code):
        with self.connection: self.cursor.execute("DELETE FROM promocodes WHERE code = ?", (code,))

db = Database(DB_FILE)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- FSM ---
class UserStates(StatesGroup):
    getting_payment_details = State()
    enter_promo_code = State()

class AdminStates(StatesGroup):
    broadcast_message = State()
    set_bonus_amount = State()
    decline_reason = State()
    create_promo_code = State()
    create_promo_reward = State()
    create_promo_activations = State()
    add_req_channel_name = State()
    add_req_channel_entry = State()
    add_req_private_link = State()
    add_admin_id = State()
    balance_change_user_id = State()
    balance_change_amount = State()
    set_ref_bonus = State()
    upload_db_file = State()

# --- FİLTRELER ---
class IsAdmin(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        return db.is_admin(event.from_user.id)

class IsChiefAdmin(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        return db.is_chief_admin(event.from_user.id)

# --- PIARFLOW API İŞLEVİ ---
async def check_piarflow_sponsors(user: User) -> list:
    not_subbed = []
    try:
        headers = {
            "Authorization": f"Bearer {PIARFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "user_id": int(user.id),
            "chat_id": int(user.id),
            "max_sponsors": 5
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{PIARFLOW_API_URL}/sponsors", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sponsors = data.get("sponsors") or []
                    if sponsors:
                        links = [s["link"] for s in sponsors if s.get("link")]
                        if links:
                            check_payload = {
                                "user_id": int(user.id),
                                "links": links
                            }
                            async with session.post(f"{PIARFLOW_API_URL}/sponsors/check", json=check_payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as check_resp:
                                if check_resp.status == 200:
                                    check_data = await check_resp.json()
                                    checked_sponsors = check_data.get("sponsors") or []
                                    for item in checked_sponsors:
                                        if item.get("status") != "subscribed":
                                            link = item.get("link")
                                            not_subbed.append({
                                                'name': "Sponsor",
                                                'url': link,
                                                'icon_custom_emoji_id': "6039381989985882045"
                                            })
                                else:
                                    for s in sponsors:
                                        if s.get("status") != "subscribed" and s.get("link"):
                                            not_subbed.append({
                                                'name': "Sponsor",
                                                'url': s.get("link"),
                                                'icon_custom_emoji_id': "6039381989985882045"
                                            })
                        else:
                            for s in sponsors:
                                if s.get("status") != "subscribed" and s.get("link"):
                                    not_subbed.append({
                                        'name': "Sponsor",
                                        'url': s.get("link"),
                                        'icon_custom_emoji_id': "6039381989985882045"
                                    })
    except Exception as e:
        logging.error(f"PiarFlow check error: {e}")
    return not_subbed

# --- ABONELİK KONTROLÜ ---
async def run_full_subscription_check(user: User, bot: Bot) -> tuple[bool, list]:
    not_subscribed_channels = []
    is_fully_subscribed = True
    user_id = user.id

    # 1. Локальные обязательные каналы
    local_channels = db.get_required_channels()
    if local_channels:
        for _, name, channel_id, url in local_channels:
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in ["creator", "administrator", "member"]:
                    is_fully_subscribed = False
                    not_subscribed_channels.append({'name': name, 'url': url, 'icon_custom_emoji_id': "6039381989985882045"})
            except TelegramAPIError as e:
                logging.error(f"Error checking local sub for {channel_id}: {e}")
                is_fully_subscribed = False
                not_subscribed_channels.append({'name': name, 'url': url, 'icon_custom_emoji_id': "6039381989985882045"})

    # 2. PiarFlow API
    try:
        pf_unsubbed = await check_piarflow_sponsors(user)
        if pf_unsubbed:
            is_fully_subscribed = False
            not_subscribed_channels.extend(pf_unsubbed)
    except Exception as e:
        logging.error(f"PiarFlow check error: {e}")

    # 3. TGrass API
    try:
        url = "https://tgrass.space/offers"
        headers = {"accept": "application/json", "Content-Type": "application/json", "Auth": TGRASS_API_KEY}
        payload = {"tg_user_id": int(user.id), "tg_login": user.username or "", "lang": user.language_code or "en", "is_premium": user.is_premium or False}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    resp_json = await response.json()
                    if resp_json.get("status") == "not_ok":
                         is_fully_subscribed = False
                         for offer in resp_json.get("offers", []):
                             not_subscribed_channels.append({'name': f" {offer.get('title', 'Sponsor')}", 'url': offer['link'], 'icon_custom_emoji_id': "6039381989985882045"})
    except Exception as e:
        logging.error(f"TGrass check error: {e}")

    # 4. Flyer API
    try:
        if FLYER_API_KEY:
            flyer_url = "https://api.flyerhubs.com/max/get_tasks"
            flyer_payload = {
                "key": FLYER_API_KEY,
                "chat_id": int(user.id),
                "user_id": int(user.id),
                "user_locale": user.language_code or "ru",
                "limit": 5
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(flyer_url, json=flyer_payload, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        flyer_json = await response.json()
                        tasks = flyer_json.get("result", [])
                        if tasks:
                            is_fully_subscribed = False
                            for task in tasks:
                                task_url = task.get("url") or task.get("link") or task.get("button_url") or task.get("channel_url")
                                task_name = task.get("name") or task.get("title") or "Sponsor"
                                if task_url:
                                    not_subscribed_channels.append({
                                        'name': task_name,
                                        'url': task_url,
                                        'icon_custom_emoji_id': "6039381989985882045"
                                    })
    except Exception as e:
        logging.error(f"Flyer API check error: {e}")

    return is_fully_subscribed, not_subscribed_channels

async def process_referral(new_user: User, bot: Bot):
    user_id = new_user.id
    ref_info = db.get_user_referral_info(user_id)
    if not ref_info: return
    referrer_id, referral_processed = ref_info
    if referrer_id and not referral_processed:
        ref_bonus = float(db.get_setting('ref_bonus'))
        db.update_balance(referrer_id, ref_bonus)
        db.mark_referral_as_processed(user_id)
        new_user_display = db.get_user_display_name(user_id)
        notification_text = get_text('referral_notification').format(new_user_display=new_user_display, ref_bonus=ref_bonus)
        try:
            await bot.send_message(referrer_id, notification_text)
        except TelegramAPIError as e:
            logging.warning(f"Could not send ref notification to {referrer_id}: {e}")

async def send_photo_or_message(chat_id, text, markup, parse_mode="HTML"):
    if START_PHOTO_URL:
        return await bot.send_photo(chat_id, photo=START_PHOTO_URL, caption=text, reply_markup=markup, parse_mode=parse_mode)
    else:
        return await bot.send_message(chat_id, text, reply_markup=markup, parse_mode=parse_mode)

async def send_photo_or_message_to_target(target, text, markup):
    if isinstance(target, CallbackQuery):
        try:
            await target.message.delete()
        except:
            pass
        return await send_photo_or_message(target.message.chat.id, text, markup)
    else:
        return await send_photo_or_message(target.chat.id, text, markup)

async def clean_prompt(state: FSMContext, chat_id: int, bot: Bot):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    if prompt_message_id:
        try: await bot.delete_message(chat_id, prompt_message_id)
        except TelegramAPIError: pass

# --- ARA YAZILIM (ИСПРАВЛЕНА ЗАЩИТА ОТ СТАРЫХ КНОПКИ В МЕНЮ) ---
class MasterMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: types.TelegramObject, data: Dict) -> Any:
        user = data.get('event_from_user')
        if not user:
            return await handler(event, data)

        db.update_user_info(user.id, user.username, user.first_name)

        # Пропускаем команды админа, но для обычных кнопок админ тоже проходит проверку спонсоров
        # Это решает проблему, когда админ при тестах видит, что спонсоры не запрашиваются
        if db.is_admin(user.id):
            if (isinstance(event, types.Message) and event.text and event.text.startswith('/admin')) or \
               (isinstance(event, types.CallbackQuery) and event.data and event.data.startswith('admin_')):
                return await handler(event, data)

        if (isinstance(event, types.Message) and event.text and event.text.startswith('/start')) or \
           (isinstance(event, types.CallbackQuery) and event.data == "check_subscription"):
            return await handler(event, data)

        is_subscribed, not_subscribed_list = await run_full_subscription_check(user, data['bot'])
        
        if not is_subscribed:
            text = get_text('sub_check_fail', warning_icon=EMOJI_IDS["warning_icon"])
            markup = get_subscription_kb(not_subscribed_list)

            if isinstance(event, types.Message):
                await event.answer(text, reply_markup=markup, disable_web_page_preview=True)
            elif isinstance(event, types.CallbackQuery):
                try:
                    await event.answer(get_text('sub_check_not_yet'), show_alert=True)
                except TelegramAPIError:
                    pass
                
                # Мгновенно перерисовываем старое меню на меню спонсоров, стирая старые кнопки навсегда!
                try:
                    if event.message.caption:
                        await event.message.edit_caption(caption=text, reply_markup=markup)
                    else:
                        await event.message.edit_text(text=text, reply_markup=markup, disable_web_page_preview=True)
                except TelegramAPIError:
                    try:
                        await event.message.delete()
                        await event.message.answer(text, reply_markup=markup, disable_web_page_preview=True)
                    except TelegramAPIError:
                        pass
            return

        return await handler(event, data)

# --- KULLANICI İŞLEYİCİLERİ ---
@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(call: CallbackQuery, bot: Bot):
    user = call.from_user
    is_subscribed, not_subscribed_list = await run_full_subscription_check(user, bot)
    
    if is_subscribed:
        await call.answer(get_text('sub_check_success'), show_alert=True)
        try: await call.message.delete()
        except TelegramAPIError: pass
        await process_referral(user, bot)
        text = get_text('start').format(start_emoji=EMOJI_IDS["start"])
        await send_photo_or_message(call.message.chat.id, text, get_main_menu_kb())
    else:
        await call.answer(get_text('sub_check_not_yet'), show_alert=True)
        markup = get_subscription_kb(not_subscribed_list)
        text = get_text('sub_check_fail', warning_icon=EMOJI_IDS["warning_icon"])
        try:
            if call.message.caption:
                await call.message.edit_caption(caption=text, reply_markup=markup)
            else:
                await call.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
        except TelegramAPIError:
            try:
                await call.message.edit_reply_markup(reply_markup=markup)
            except TelegramAPIError:
                pass

@dp.message(CommandStart())
async def command_start(message: Message, bot: Bot):
    user = message.from_user
    if not db.user_exists(user.id):
        referrer_id = None
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit() and int(args[1]) != user.id:
            referrer_id = int(args[1])
        db.add_user(user, referrer_id)

    is_subscribed, not_subscribed_list = await run_full_subscription_check(user, bot)

    if is_subscribed:
        await process_referral(user, bot)
        text = get_text('start').format(start_emoji=EMOJI_IDS["start"])
        await send_photo_or_message(message.chat.id, text, get_main_menu_kb())
    else:
        text = get_text('sub_check_fail', warning_icon=EMOJI_IDS["warning_icon"])
        markup = get_subscription_kb(not_subscribed_list)
        await message.answer(text, reply_markup=markup, disable_web_page_preview=True)

@dp.callback_query(F.data == "main_menu")
async def back_to_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    text = get_text('start').format(start_emoji=EMOJI_IDS["start"])
    try:
        await call.message.delete()
    except:
        pass
    await send_photo_or_message(call.from_user.id, text, get_main_menu_kb())
    await call.answer()

@dp.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery):
    user_id = call.from_user.id
    balance = db.get_user_balance(user_id)
    referrals_count = db.get_referrals_count(user_id)
    username = db.get_user_username(user_id)
    text = get_text('profile').format(
        profile_icon=EMOJI_IDS["profile_icon"],
        id_icon=EMOJI_IDS["id_icon"],
        balance_icon=EMOJI_IDS["balance_icon"],
        star_icon=EMOJI_IDS["star_icon"],
        friends_icon=EMOJI_IDS["friends_icon"],
        username=username,
        user_id=user_id,
        balance=round(balance, 2),
        referrals_count=referrals_count
    )
    await send_photo_or_message_to_target(call, text, get_profile_kb())
    await call.answer()

@dp.callback_query(F.data == "earn")
async def show_earn_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    ref_bonus = float(db.get_setting('ref_bonus'))
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    text = get_text('invite').format(
        star_emoji=EMOJI_IDS["star"],
        link_emoji=EMOJI_IDS["link"],
        celebration_emoji=EMOJI_IDS["celebration"],
        ref_bonus=ref_bonus,
        ref_link=ref_link
    )
    await send_photo_or_message_to_target(call, text, get_invite_kb(ref_link))
    await call.answer()

@dp.callback_query(F.data == "invite_friends")
async def show_invite_menu(call: CallbackQuery, bot: Bot):
    ref_bonus = float(db.get_setting('ref_bonus'))
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    text = get_text('invite').format(
        star_emoji=EMOJI_IDS["star"],
        link_emoji=EMOJI_IDS["link"],
        celebration_emoji=EMOJI_IDS["celebration"],
        ref_bonus=ref_bonus,
        ref_link=ref_link
    )
    await send_photo_or_message_to_target(call, text, get_invite_kb(ref_link))
    await call.answer()

@dp.callback_query(F.data == "withdraw")
async def show_withdraw_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    balance = db.get_user_balance(user_id)
    referrals = db.get_referrals_count(user_id)
    
    if balance < 25:
        await call.answer(get_text('alert_insufficient_stars', balance=round(balance, 2)), show_alert=True)
        return
    
    text = get_text('withdraw_title').format(
        withdraw_emoji=EMOJI_IDS["withdraw"],
        card_icon=EMOJI_IDS["card_icon"],
        star_premium_icon=EMOJI_IDS["star_premium_icon"],
        balance=round(balance, 2),
        min_refs=MIN_REFERRALS_FOR_WITHDRAWAL,
        user_refs=referrals
    )
    await send_photo_or_message_to_target(call, text, get_withdraw_kb())
    await call.answer()

@dp.callback_query(F.data.startswith("withdraw_gift_"))
async def request_withdraw_gift(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    referrals_count = db.get_referrals_count(user_id)
    
    if referrals_count < MIN_REFERRALS_FOR_WITHDRAWAL:
        diff = MIN_REFERRALS_FOR_WITHDRAWAL - referrals_count
        await call.answer(get_text('alert_need_more_refs').format(diff=diff), show_alert=True)
        return
    
    if db.has_pending_withdrawal(user_id):
        await call.answer(get_text('alert_pending_withdrawal'), show_alert=True)
        return

    username = db.get_user_display_name(user_id)
    balance = db.get_user_balance(user_id)
    
    try:
        parts = call.data.split("_")
        cost = float(parts[2])
        gift_name = parts[3]
    except (ValueError, IndexError) as e:
        logging.error(f"Could not parse gift withdraw: {call.data}, Error: {e}")
        await call.answer("❌ Isleg işlenilende ýalňyşlyk ýüze çykdy.", show_alert=True)
        return
    
    if balance < cost:
        await call.answer(get_text('alert_insufficient_stars', balance=round(balance, 2)), show_alert=True)
        return

    request_id, request_uid = db.create_withdrawal_request(user_id, username, cost, gift_name)
    
    channel_text = get_payment_channel_status_text(request_id, user_id, cost, gift_name, "pending")
    channel_markup = get_payment_channel_kb(request_id)
    
    try:
        channel_message = await bot.send_message(PAYMENTS_CHANNEL_ID, channel_text, reply_markup=channel_markup)
        db.update_payment_channel_message_id(request_id, channel_message.message_id)
    except TelegramAPIError as e:
        logging.error(f"Could not send payment channel message: {e}")
    
    admin_text = (f"✨ Täze isleg (Sowgat) #{request_uid} ✨\n\n"
                  f"👤 <b>Ulanyjy:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                  f"🎁 <b>Sowgat:</b> {gift_name}\n💰 <b>Bahasy:</b> {cost} ⭐\n"
                  f"🕓 <b>Senesi:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        admin_kb = get_admin_withdraw_kb(request_id)
        await bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=admin_kb)
    except TelegramAPIError as e:
        logging.error(f"Could not send gift request to admin channel: {e}")
    
    confirmation_text = get_text("request_submitted_for_review").format(request_uid=request_uid)
    await send_photo_or_message_to_target(call, confirmation_text, get_withdraw_submitted_kb())
    await call.answer()

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment_input(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer(get_text("alert_action_canceled"))
    await show_withdraw_menu(call, state)

@dp.callback_query(F.data == "bonus")
async def claim_bonus(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    last_bonus_time = db.get_last_bonus_time(user_id)
    if last_bonus_time and datetime.now() - last_bonus_time < timedelta(hours=24):
        time_left = timedelta(hours=24) - (datetime.now() - last_bonus_time)
        hours, rem = divmod(time_left.seconds, 3600)
        minutes, _ = divmod(rem, 60)
        wait_text = get_text('bonus_wait').format(hours=hours, minutes=minutes)
        await call.answer(wait_text, show_alert=True)
    else:
        min_b, max_b = float(db.get_setting('daily_bonus_min')), float(db.get_setting('daily_bonus_max'))
        bonus_amount = round(random.uniform(min_b, max_b), 1)
        db.update_balance(user_id, bonus_amount)
        db.update_last_bonus_time(user_id)
        
        claim_text = get_text('bonus_claimed').format(bonus_amount=bonus_amount)
        await call.answer(claim_text, show_alert=True)
        
        try:
            await call.message.delete()
        except:
            pass
        
        await state.clear()
        text = get_text('start').format(start_emoji=EMOJI_IDS["start"])
        await send_photo_or_message(call.from_user.id, text, get_main_menu_kb())

@dp.callback_query(F.data == "promo")
async def show_promo_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.enter_promo_code)
    text = get_text('promo').format(gift_icon=EMOJI_IDS["gift_icon"])
    try:
        await call.message.delete()
    except:
        pass
    prompt_message = await send_photo_or_message(call.message.chat.id, text, get_back_kb("main_menu"))
    if prompt_message:
        await state.update_data(prompt_message_id=prompt_message.message_id)
    await call.answer()

@dp.message(UserStates.enter_promo_code, F.text)
async def process_promo_code(message: Message, state: FSMContext, bot: Bot):
    user_id, code = message.from_user.id, message.text.strip().upper()
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    await message.delete()
    if prompt_message_id:
        try:
            await bot.delete_message(message.chat.id, prompt_message_id)
        except TelegramAPIError:
            pass
    await state.clear()
    msg_text = ""
    if db.has_user_used_promo(user_id, code):
        msg_text = get_text('promo_fail_used')
    else:
        promo_data = db.get_promocode(code)
        if promo_data and promo_data[1] > 0:
            reward, _ = promo_data
            db.update_balance(user_id, reward)
            db.use_promocode(user_id, code)
            msg_text = get_text('promo_success').format(reward=reward)
        else:
            msg_text = get_text('promo_fail_general')
    
    final_msg = await message.answer(msg_text)
    await asyncio.sleep(4)
    try:
        await final_msg.delete()
    except TelegramAPIError:
        pass
    
    text = get_text('start').format(start_emoji=EMOJI_IDS["start"])
    await send_photo_or_message(message.chat.id, text, get_main_menu_kb())

@dp.callback_query(F.data == "top_referrals")
async def show_top_referrals(call: CallbackQuery):
    user_id = call.from_user.id
    top_referrers = db.get_top_by_referrals_last_24h(limit=5)
    text = get_text('top_referrals_title').format(top_emoji=EMOJI_IDS["top"])
    
    if not top_referrers:
        text += get_text('top_no_users')
    else:
        medal_emojis = ["🥇", "🥈", "🥉", "✨", "✨"]
        lines = []
        for i, (uid, ref_count, username, first_name) in enumerate(top_referrers[:5], 1):
            display_name = f"@{username}" if username else html.quote(first_name)
            medal = medal_emojis[i-1] if i <= len(medal_emojis) else "✨"
            lines.append(f"{medal} {display_name} | {ref_count}")
        text += "\n".join(lines)
    
    user_ref_count_24h = db.get_referrals_count_last_24h(user_id)
    user_in_top = any(uid == user_id for uid, _, _, _ in top_referrers)
    
    if not user_in_top:
        text += get_text('top_not_in_top', count=user_ref_count_24h)
    
    await send_photo_or_message_to_target(call, text, get_back_kb("main_menu"))
    await call.answer()

# --- ADMIN KANALI ONAY/RED İŞLEYİCİLERİ ---
@dp.callback_query(F.data.startswith("withdraw_approve_"), IsAdmin())
async def approve_withdraw(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[-1])
    admin_name = html.quote(call.from_user.username or call.from_user.first_name)
    request_data = db.get_withdrawal_request(request_id)
    if not request_data:
        await call.answer("❌ Isleg tapylmady.", show_alert=True)
        return
    uid, user_id, username, amount, gift_name, status, _, details, payment_msg_id = request_data
    if status != 'pending':
        await call.answer(f"⚠️ Bu isleg eýýäm işlenildi (ýagdaýy: {status}).", show_alert=True)
        return
    db.update_balance(user_id, -amount)
    db.update_withdrawal_status(request_id, 'approved')
    admin_channel_text = (f"✅ <b>#{uid} belgili isleg Tassyklandy</b> {admin_name} admin tarapyndan\n\n"
                          f"👤 <b>Ulanyjy:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Sowgat:</b> {gift_name}\n💰 <b>Aýyryldy:</b> {amount} ⭐")
    await call.message.edit_text(admin_channel_text, reply_markup=None)
    user_notification = get_text('status_approved').format(uid=uid, gift_name=gift_name, amount=amount)
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send approval notification to user {user_id}: {e}")
    await call.answer("✅ Tassyklandy.", show_alert=True)

@dp.callback_query(F.data.startswith("withdraw_decline_"), IsAdmin())
async def decline_withdraw_start(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[-1])
    request_data = db.get_withdrawal_request(request_id)
    if not request_data or request_data[5] != 'pending':
        await call.answer("⚠️ Bu isleg eýýäm işlenildi.", show_alert=True)
        return

    channel_chat_id = call.message.chat.id
    channel_message_id = call.message.message_id

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Sebäbini giriz",
        callback_data=f"decline_prompt_{request_id}_{channel_chat_id}_{channel_message_id}",
        icon_custom_emoji_id=EMOJI_IDS["edit"],
        style="danger"
    )

    try:
        await bot.send_message(
            chat_id=call.from_user.id,
            text=f"Siz #{request_data[0]} belgili islegi ret etmekçi bolýarsyňyz. Sebäbini görkezmek üçin aşakdaky düwmä basyň.",
            reply_markup=builder.as_markup()
        )
        await call.answer("Dowam etmek üçin bot bilen şahsy hat alyşmada düwmä basyň.", show_alert=True)
    except TelegramAPIError as e:
        await call.answer(f"❌ Şahsy hat ugradyp bolmady. Ýalňyşlyk: {e}", show_alert=True)
        logging.error(f"Could not send PM to admin {call.from_user.id}: {e}")

@dp.callback_query(F.data.startswith("decline_prompt_"), IsAdmin())
async def decline_reason_prompt(call: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        parts = call.data.split("_")
        request_id = int(parts[2])
        channel_chat_id = int(parts[3])
        channel_message_id = int(parts[4])
    except (ValueError, IndexError):
        await call.answer("❌ Maglumatlarda ýalňyşlyk. Gaýtadan synanşyň.", show_alert=True)
        logging.error(f"Could not parse decline_prompt callback data: {call.data}")
        return

    await state.set_state(AdminStates.decline_reason)
    await state.update_data(
        request_id=request_id,
        channel_chat_id=channel_chat_id,
        channel_message_id=channel_message_id
    )

    prompt_message = await call.message.edit_text(
        "Ret etmegiň sebäbini giriziň. Bu tekst ulanyja ugradylar.",
        reply_markup=get_back_to_admin_panel_kb()
    )
    await state.update_data(prompt_message_id=prompt_message.message_id)
    await call.answer()

@dp.message(AdminStates.decline_reason, IsAdmin())
async def process_decline_reason(message: Message, state: FSMContext, bot: Bot):
    reason = message.text
    await message.delete()
    await clean_prompt(state, message.chat.id, bot)
    data = await state.get_data()
    request_id, channel_chat_id, channel_message_id = data.get('request_id'), data.get('channel_chat_id'), data.get('channel_message_id')
    await state.clear()
    if not all([request_id, channel_chat_id, channel_message_id]):
        await bot.send_message(message.from_user.id, "❌ Ýalňyşlyk.")
        return
    admin_name = html.quote(message.from_user.username or message.from_user.first_name)
    request_data = db.get_withdrawal_request(request_id)
    if not request_data:
        await bot.send_message(message.from_user.id, f"❌ #{request_id} belgili isleg tapylmady.")
        return
    uid, user_id, username, amount, gift_name, status, _, details, payment_msg_id = request_data
    if status != 'pending':
        await bot.send_message(message.from_user.id, f"⚠️ #{uid} belgili isleg eýýäm işlenildi (Ýagdaýy: {status}).")
        return
    db.update_withdrawal_status(request_id, 'declined', reason)
    admin_channel_text = (f"❌ <b>#{uid} belgili isleg Ret edildi</b> {admin_name} admin tarapyndan\n\n"
                          f"👤 <b>Ulanyjy:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Sowgat:</b> {gift_name}\n💰 <b>Aýyryldy:</b> {amount} ⭐\n\n"
                          f"📝 <b>Sebäbi:</b> {html.quote(reason)}")
    try:
        await bot.edit_message_text(admin_channel_text, chat_id=channel_chat_id, message_id=channel_message_id, reply_markup=None)
    except TelegramAPIError as e:
        logging.error(f"Could not edit message in admin channel: {e}")
    user_notification = get_text('status_declined').format(uid=uid, reason=html.quote(reason))
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send decline notification to user {user_id}: {e}")
    await bot.send_message(message.from_user.id, f"✅ #{uid} belgili isleg ret edildi.", reply_markup=get_back_to_admin_panel_kb())

# --- ÖDEME KANALI İŞLEYİCİLERİ ---
@dp.callback_query(F.data.startswith("payment_send_"), IsAdmin())
async def payment_send_handler(call: CallbackQuery, bot: Bot):
    try:
        request_id = int(call.data.split("_")[-1])
    except (ValueError, IndexError):
        await call.answer("❌ Ýalňyşlyk: Nädogry isleg ID-si", show_alert=True)
        return
    
    request_data = db.get_withdrawal_request_by_id(request_id)
    if not request_data:
        await call.answer("❌ Isleg tapylmady", show_alert=True)
        return
    
    request_id_db, uid, user_id, username, amount, gift_name, status, decline_reason, details, payment_message_id = request_data
    
    if status != 'pending':
        await call.answer(f"⚠️ Bu isleg eýýäm işlenildi (ýagdaýy: {status})", show_alert=True)
        return
    
    db.update_balance(user_id, -amount)
    db.update_withdrawal_status(request_id, 'approved')
    
    if payment_message_id:
        try:
            new_text = get_payment_channel_status_text(request_id, user_id, amount, gift_name, "sent")
            await bot.edit_message_text(
                chat_id=PAYMENTS_CHANNEL_ID,
                message_id=payment_message_id,
                text=new_text,
                reply_markup=None
            )
        except TelegramAPIError as e:
            logging.error(f"Could not update payment channel message: {e}")
    
    user_notification = get_text('status_approved').format(uid=uid, gift_name=gift_name, amount=amount)
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send approval notification to user {user_id}: {e}")
    
    await call.answer("✅ Sowgat ugradyldy!", show_alert=True)

@dp.callback_query(F.data.startswith("payment_decline_"), IsAdmin())
async def payment_decline_handler(call: CallbackQuery, bot: Bot):
    try:
        request_id = int(call.data.split("_")[-1])
    except (ValueError, IndexError):
        await call.answer("❌ Ýalňyşlyk: Nädogry isleg ID-si", show_alert=True)
        return
    
    request_data = db.get_withdrawal_request_by_id(request_id)
    if not request_data:
        await call.answer("❌ Isleg tapylmady", show_alert=True)
        return
    
    request_id_db, uid, user_id, username, amount, gift_name, status, decline_reason, details, payment_message_id = request_data
    
    if status != 'pending':
        await call.answer(f"⚠️ Bu isleg eýýäm işlenildi (ýagdaýy: {status})", show_alert=True)
        return
    
    db.update_withdrawal_status(request_id, 'declined', "Administrator tarapyndan ret edildi")
    
    if payment_message_id:
        try:
            new_text = get_payment_channel_status_text(request_id, user_id, amount, gift_name, "declined")
            await bot.edit_message_text(
                chat_id=PAYMENTS_CHANNEL_ID,
                message_id=payment_message_id,
                text=new_text,
                reply_markup=None
            )
        except TelegramAPIError as e:
            logging.error(f"Could not update payment channel message: {e}")
    
    user_notification = get_text('status_declined').format(uid=uid, reason="Administrator tarapyndan ret edildi")
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send decline notification to user {user_id}: {e}")
    
    await call.answer("❌ Isleg ret edildi!", show_alert=True)

# --- YÖNETİCİ PANELİ ---
@dp.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("<tg-emoji emoji-id=\"5798587088077066898\">👋</tg-emoji> <b>Admin-panele hoş geldiňiz!</b>", reply_markup=get_admin_kb(message.from_user.id))

@dp.callback_query(F.data == "admin_panel", IsAdmin())
async def admin_panel_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("<tg-emoji emoji-id=\"5798587088077066898\">👋</tg-emoji> <b>Admin-panele hoş geldiňiz!</b>", reply_markup=get_admin_kb(call.from_user.id))
    await call.answer()

@dp.callback_query(F.data == "admin_ref_bonus", IsAdmin())
async def ref_bonus_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    current_bonus = db.get_setting('ref_bonus')
    text = (f"<tg-emoji emoji-id=\"{EMOJI_IDS['star']}\">⭐️</tg-emoji> <b>Referal bonusy</b>\n\n"
            f"Häzirki bonus: <b>{current_bonus}</b> ⭐\n\n"
            f"<blockquote>Her çagyrylan dost üçin ýyldyzlaryň sany.\n"
            f"Täze bahany giriziň (mysal üçin: <code>1.5</code>)</blockquote>")
    
    prompt_message = await call.message.edit_text(text, reply_markup=get_back_to_admin_panel_kb())
    if prompt_message:
        await state.update_data(prompt_message_id=prompt_message.message_id)
    await state.set_state(AdminStates.set_ref_bonus)
    await call.answer()

@dp.message(AdminStates.set_ref_bonus, IsAdmin())
async def set_ref_bonus_value(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    await clean_prompt(state, message.chat.id, bot)
    
    try:
        new_bonus = float(message.text.replace(',', '.'))
        
        if new_bonus <= 0:
            raise ValueError("Bonus must be positive")
        
        db.set_setting('ref_bonus', str(new_bonus))
        await message.answer(f"✅ Referal bonusy üýtgedildi: <b>{new_bonus}</b> ⭐", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
        
    except ValueError:
        await state.set_state(AdminStates.set_ref_bonus)
        prompt = await message.answer("❌ Nädogry format. San giriziň (mysal üçin: <code>1.5</code>).")
        await state.update_data(prompt_message_id=prompt.message_id)

@dp.callback_query(F.data == "admin_stats", IsAdmin())
async def admin_stats(call: CallbackQuery):
    stats = db.get_stats()
    text = (f"<tg-emoji emoji-id=\"{EMOJI_IDS['stats']}\">📊</tg-emoji> <b>Statistika:</b>\n\n"
            f"<b>Ulanyjylar:</b>\n"
            f"├ Jemi: <b>{stats['total_users']}</b>\n"
            f"└ 24 sagatda: <b>{stats['new_users_24h']}</b>\n\n"
            f"<b>Ykdysadyýet:</b>\n"
            f"├ Jemi ýyldyzlar: <b>{stats['total_balance']}</b> ⭐\n"
            f"└ Çykaryldy: <b>{stats['withdrawn_sum']}</b> ⭐\n\n"
            f"<b>Islegler:</b>\n"
            f"├ Garaşylýar: <b>{stats['withdraw_pending']}</b>\n"
            f"├ Tassyklandy: <b>{stats['withdraw_approved']}</b>\n"
            f"└ Ret edildi: <b>{stats['withdraw_declined']}</b>")
    await call.message.edit_text(text, reply_markup=get_back_to_admin_panel_kb())
    await call.answer()

@dp.callback_query(F.data == "admin_broadcast", IsAdmin())
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.broadcast_message)
    await call.message.edit_text("📢 Ýaýratmak üçin haty ugradyň:", reply_markup=get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.broadcast_message, IsAdmin())
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = db.get_all_user_ids()
    sent, failed = 0, 0
    status_message = await message.answer(f"🚀 {len(user_ids)} ulanyja ugradylýar...")
    for user_id in user_ids:
        try:
            await bot.copy_message(user_id, message.chat.id, message.message_id)
            sent += 1
        except Exception as e:
            failed += 1
            logging.error(f"Broadcast fail to {user_id}: {e}")
        await asyncio.sleep(0.1)
    await status_message.edit_text(f"✅ Hat ýaýratmak tamamlandy!\n\n📬 Ugradyldy: {sent}\n❌ Ugradylmady: {failed}", reply_markup=get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_bonus_settings", IsAdmin())
async def bonus_settings(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.set_bonus_amount)
    min_b, max_b = db.get_setting('daily_bonus_min'), db.get_setting('daily_bonus_max')
    text = (f"<tg-emoji emoji-id=\"{EMOJI_IDS['edit']}\">⚙️</tg-emoji> <b>Bonus sazlamalary</b>\n\nHäzirki aralyk: <b>{min_b}</b>-den <b>{max_b}</b>⭐ çenli\n\n"
            f"<blockquote>Täze aralygy <code>min-maks</code> formatynda giriziň\nMysal üçin: <code>0.5-2.5</code></blockquote>")
    prompt_message = await call.message.edit_text(text, reply_markup=get_back_to_admin_panel_kb())
    if prompt_message:
        await state.update_data(prompt_message_id=prompt_message.message_id)
    await call.answer()

@dp.message(AdminStates.set_bonus_amount, IsAdmin())
async def set_bonus_amount(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    await clean_prompt(state, message.chat.id, bot)
    try:
        min_b_str, max_b_str = message.text.replace(',', '.').split('-')
        min_b, max_b = float(min_b_str), float(max_b_str)
        if not (0 <= min_b <= max_b):
            raise ValueError("Incorrect range")
        db.set_setting('daily_bonus_min', str(min_b))
        db.set_setting('daily_bonus_max', str(max_b))
        await message.answer(f"✅ Bonus aralygy üýtgedildi: <code>{min_b}-{max_b}</code>.", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except (ValueError, TypeError):
        await state.set_state(AdminStates.set_bonus_amount)
        prompt = await message.answer("❌ Nädogry format. Iki sany kese çyzyk arkaly giriziň (mysal üçin, <code>0.5-2.5</code>).")
        await state.update_data(prompt_message_id=prompt.message_id)

@dp.callback_query(F.data == "admin_manage_admins", IsChiefAdmin())
async def admin_manage_admins_menu(call: CallbackQuery):
    admins = db.get_admins()
    text = "<tg-emoji emoji-id=\"{lock_emoji}\">👑</tg-emoji> <b>Adminleri dolandyrmak</b>\n\n".format(lock_emoji=EMOJI_IDS["lock"])
    builder = InlineKeyboardBuilder()
    admin_lines = []
    for admin_id, is_chief in admins:
        admin_info = f"<code>{admin_id}</code>"
        if is_chief:
            admin_info += " (👑 Baş admin)"
        else:
            builder.button(text=f"Aýyr {admin_id}", callback_data=f"admin_remove_admin_{admin_id}", icon_custom_emoji_id=EMOJI_IDS["remove"], style="danger")
        admin_lines.append(f"▪️ {admin_info}")
    text += "\n".join(admin_lines)
    builder.button(text="Admin goş", callback_data="admin_add_admin", icon_custom_emoji_id=EMOJI_IDS["add"], style="success")
    builder.button(text="Yza", callback_data="admin_panel", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_add_admin", IsChiefAdmin())
async def admin_add_admin_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_admin_id)
    await call.answer()
    prompt = await call.message.edit_text("<blockquote>Täze administratoryň Telegram ID-sini ugradyň.</blockquote>", reply_markup=get_back_to_admin_panel_kb())
    await state.update_data(prompt_message_id=prompt.message_id)

@dp.message(AdminStates.add_admin_id, IsChiefAdmin())
async def admin_add_admin_process(message: Message, state: FSMContext, bot: Bot):
    await clean_prompt(state, message.chat.id, bot)
    if not message.text.isdigit():
        await message.answer("❌ Nädogry format. Sanly ID giriziň.", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
        return
    new_admin_id = int(message.text)
    if db.is_admin(new_admin_id):
        await message.answer(f"⚠️ <code>{new_admin_id}</code> ulanyjy eýýäm administrator.", reply_markup=get_back_to_admin_panel_kb())
    else:
        db.add_admin(new_admin_id)
        await message.answer(f"✅ Administrator <code>{new_admin_id}</code> goşuldy!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

@dp.callback_query(F.data.startswith("admin_remove_admin_"), IsChiefAdmin())
async def admin_remove_admin(call: CallbackQuery):
    admin_id_to_remove = int(call.data.split("_")[-1])
    if admin_id_to_remove == call.from_user.id:
        await call.answer("❌ Siz öz-özüňizi aýyryp bilmersiňiz.", show_alert=True)
        return
    db.remove_admin(admin_id_to_remove)
    await call.answer(f"✅ Administrator {admin_id_to_remove} aýyryldy", show_alert=True)
    await admin_manage_admins_menu(call)

@dp.callback_query(F.data == "admin_balance_change", IsAdmin())
async def balance_change_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.balance_change_user_id)
    await call.answer()
    prompt = await call.message.edit_text("<tg-emoji emoji-id=\"{money_emoji}\">💰</tg-emoji> <b>Balansy üýtgetmek</b>\n\n<blockquote>Ulanyjynyň Telegram ID-sini giriziň.</blockquote>".format(money_emoji=EMOJI_IDS["money"]), reply_markup=get_back_to_admin_panel_kb())
    await state.update_data(prompt_message_id=prompt.message_id)

@dp.message(AdminStates.balance_change_user_id, IsAdmin())
async def balance_change_get_id(message: Message, state: FSMContext, bot: Bot):
    await clean_prompt(state, message.chat.id, bot)
    await message.delete()
    if not message.text.isdigit():
        await state.clear()
        await message.answer("❌ Nädogry format. Sanly ID giriziň.", reply_markup=get_back_to_admin_panel_kb())
        return
    user_id = int(message.text)
    if not db.user_exists(user_id):
        await state.clear()
        await message.answer(f"❌ <code>{user_id}</code> ulanyjy tapylmady.", reply_markup=get_back_to_admin_panel_kb())
        return
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminStates.balance_change_amount)
    current_balance = db.get_user_balance(user_id)
    prompt_text = (f"Ulanyjy: <code>{user_id}</code>\nBalans: <b>{round(current_balance, 2)}</b> ⭐\n\n"
                   f"<blockquote>Üýtgetmek üçin möçberi giriziň. Azaltmak üçin minus ulanyň (mysal üçin, <code>-50</code>).</blockquote>")
    prompt = await message.answer(prompt_text, reply_markup=get_back_to_admin_panel_kb())
    await state.update_data(prompt_message_id=prompt.message_id)

@dp.message(AdminStates.balance_change_amount, IsAdmin())
async def balance_change_get_amount(message: Message, state: FSMContext, bot: Bot):
    await clean_prompt(state, message.chat.id, bot)
    await message.delete()
    data = await state.get_data()
    user_id = data.get("target_user_id")
    try:
        amount = float(message.text.replace(",", "."))
    except (ValueError, TypeError):
        await state.clear()
        await message.answer("❌ Möçberiň formaty nädogry.", reply_markup=get_back_to_admin_panel_kb())
        return
    old_balance = db.get_user_balance(user_id)
    db.update_balance(user_id, amount)
    new_balance = db.get_user_balance(user_id)
    await state.clear()
    await message.answer(f"✅ <code>{user_id}</code> ulanyjynyň balansy üýtgedildi.\n"
                         f"<i>Öň:</i> <b>{round(old_balance, 2)}</b> ⭐\n"
                         f"<i>Indi:</i> <b>{round(new_balance, 2)}</b> ⭐", reply_markup=get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_promo_menu", IsAdmin())
async def promo_management_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="Promokod döret", callback_data="admin_create_promo", icon_custom_emoji_id=EMOJI_IDS["add"], style="success")
    builder.button(text="Sanaw/Poz", callback_data="admin_list_promo", icon_custom_emoji_id=EMOJI_IDS["list"], style="primary")
    builder.button(text="Yza", callback_data="admin_panel", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(1)
    await call.message.edit_text("<tg-emoji emoji-id=\"{promo_emoji}\">🎟️</tg-emoji> <b>Promokodlary dolandyrmak</b>".format(promo_emoji=EMOJI_IDS["promo"]), reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_list_promo", IsAdmin())
async def list_promocodes(call: CallbackQuery):
    promocodes = db.get_all_promocodes()
    if not promocodes:
        await call.answer("📭 Işjeň promokodlar ýok.", show_alert=True)
        return
    text = "📄 <b>Işjeň promokodlar:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for code, reward, activations in promocodes:
        text += f"▪️ <code>{code}</code> | <b>{reward}⭐</b> | {activations} işjeňleşdirme\n"
        builder.button(text=f"Poz {code}", callback_data=f"admin_delete_promo_{code}", icon_custom_emoji_id=EMOJI_IDS["remove"], style="danger")
    builder.button(text="Yza", callback_data="admin_promo_menu", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_delete_promo_"), IsAdmin())
async def delete_promocode_handler(call: CallbackQuery):
    code_to_delete = call.data.split("_")[-1]
    db.delete_promocode(code_to_delete)
    await call.answer(f"✅ Promokod {code_to_delete} pozuldy.", show_alert=True)
    await list_promocodes(call)

@dp.callback_query(F.data == "admin_create_promo", IsAdmin())
async def create_promo_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.create_promo_code)
    text = "<tg-emoji emoji-id=\"{promo_emoji}\">🎟️</tg-emoji> <b>Promokod döretmek</b>\n\n<blockquote>Promokodyň adyny giriziň.\nÝa-da awtomatiki döretmek üçin <code>random</code> ýazyň.</blockquote>".format(promo_emoji=EMOJI_IDS["promo"])
    prompt_message = await call.message.edit_text(text, reply_markup=get_back_to_admin_panel_kb())
    if prompt_message:
        await state.update_data(prompt_message_id=prompt_message.message_id)
    await call.answer()

@dp.message(AdminStates.create_promo_code, F.text, IsAdmin())
async def create_promo_code(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    code = message.text.strip().upper()
    if code == 'RANDOM':
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    await state.update_data(promo_code=code)
    await state.set_state(AdminStates.create_promo_reward)
    prompt_text = f"Kod: <code>{code}</code>.\n\n<blockquote>⭐ Ýyldyz görnüşinde baýragy giriziň:</blockquote>"
    if prompt_message_id:
        await bot.edit_message_text(text=prompt_text, chat_id=message.chat.id, message_id=prompt_message_id)
    else:
        await state.update_data(prompt_message_id=(await message.answer(prompt_text)).message_id)

@dp.message(AdminStates.create_promo_reward, F.text, IsAdmin())
async def create_promo_reward(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    try:
        reward = float(message.text.replace(',', '.'))
        if reward <= 0:
            raise ValueError("Reward must be positive")
    except ValueError:
        error_text = "❌ Nädogry format. Oňyn san giriziň."
        if prompt_message_id:
            await bot.edit_message_text(text=error_text, chat_id=message.chat.id, message_id=prompt_message_id)
        else:
            await message.answer(error_text)
        return
    await state.update_data(promo_reward=reward)
    await state.set_state(AdminStates.create_promo_activations)
    prompt_text = "<blockquote>Işjeňleşdirmeleriň sanyny giriziň (näçe gezek ulanyp bolýandygyny):</blockquote>"
    if prompt_message_id:
        await bot.edit_message_text(text=prompt_text, chat_id=message.chat.id, message_id=prompt_message_id)
    else:
        await state.update_data(prompt_message_id=(await message.answer(prompt_text)).message_id)

@dp.message(AdminStates.create_promo_activations, F.text, IsAdmin())
async def create_promo_activations(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    await clean_prompt(state, message.chat.id, bot)
    if not message.text.isdigit() or int(message.text) <= 0:
        await state.set_state(AdminStates.create_promo_activations)
        prompt = await message.answer("❌ Nädogry format. Oňyn bitin san giriziň.")
        await state.update_data(prompt_message_id=prompt.message_id)
        return
    data = await state.get_data()
    db.create_promocode(data['promo_code'], data['promo_reward'], int(message.text))
    await state.clear()
    await message.answer(f"✅ Promokod <code>{data['promo_code']}</code> döredildi!\n⭐ Baýrak: {data['promo_reward']}\n🔄 Işjeňleşdirme sany: {message.text}", reply_markup=get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_req_subs", IsAdmin())
async def admin_req_subs_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="Kanal goş", callback_data="admin_add_req_sub", icon_custom_emoji_id=EMOJI_IDS["add"], style="success")
    builder.button(text="Sanaw/Poz", callback_data="admin_list_req_subs", icon_custom_emoji_id=EMOJI_IDS["list"], style="primary")
    builder.button(text="Yza", callback_data="admin_panel", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(1)
    await call.message.edit_text("<tg-emoji emoji-id=\"{lock_emoji}\">🔗</tg-emoji> <b>Agza bolmak üçin hökmany kanallar</b>".format(lock_emoji=EMOJI_IDS["lock"]), reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_add_req_sub", IsAdmin())
async def add_req_sub_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_req_channel_name)
    text = "<b>Ädim 1/3: Ady</b>\n\n<blockquote>Kanalyň adyny giriziň (ulanyja nähili görünjekdigini).</blockquote>"
    prompt_message = await call.message.edit_text(text, reply_markup=get_back_to_admin_panel_kb())
    if prompt_message:
        await state.update_data(prompt_message_id=prompt_message.message_id)
    await call.answer()

@dp.message(AdminStates.add_req_channel_name, F.text, IsAdmin())
async def add_req_sub_get_name(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    await state.update_data(req_channel_name=message.text)
    await state.set_state(AdminStates.add_req_channel_entry)
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    prompt_text = "<b>Ädim 2/3: Kanal</b>\n\n<blockquote>Kanalyň ID-sini ýa-da ulanyjy adyny giriziň (mysal üçin, <code>@durov</code>)\nBot kanalda administrator bolmaly.</blockquote>"
    if prompt_message_id:
        await bot.edit_message_text(text=prompt_text, chat_id=message.chat.id, message_id=prompt_message_id)
    else:
        await state.update_data(prompt_message_id=(await message.answer(prompt_text)).message_id)

async def get_chat_and_check_admin(chat_id_or_username: str, bot: Bot) -> tuple[Chat | None, str | None]:
    try:
        chat = await bot.get_chat(chat_id_or_username)
        
        try:
            member = await bot.get_chat_member(chat.id, bot.id)
            if member.status not in ['administrator', 'creator']:
                return None, "Bot kanalyň administratory däl."
        except TelegramAPIError as e:
            logging.error(f"Error checking bot admin status: {e}")
            return None, "Botuň hukuklaryny barlap bolmady. Botuň kanala administrator hökmünde goşulandygyna göz ýetiriň."
        
        return chat, None
        
    except ClientDecodeError as e:
        logging.warning(f"ClientDecodeError getting chat {chat_id_or_username}, but channel might still be valid: {e}")
        try:
            if chat_id_or_username.startswith('@'):
                username = chat_id_or_username[1:]
                member = await bot.get_chat_member(chat_id=chat_id_or_username, user_id=bot.id)
                if member.status in ['administrator', 'creator']:
                    chat = type('Chat', (), {
                        'id': chat_id_or_username,
                        'username': username,
                        'title': username,
                        'type': 'channel'
                    })()
                    return chat, None
                else:
                    return None, "Bot kanalyň administratory däl."
            else:
                return None, "Haýyş, kanalyň ulanyjy adyny (username) ulanyň (mysal üçin: @channelname)."
        except Exception as ex:
            return None, f"Ýalňyşlyk: {ex}"
    except Exception as e:
        return None, f"Kanaly almagyň ýalňyşlygy: {e}"

@dp.message(AdminStates.add_req_channel_entry, F.text, IsAdmin())
async def add_req_sub_get_entry(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    channel_input = message.text.strip()
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    
    chat, error = await get_chat_and_check_admin(channel_input, bot)
    if error or not chat:
        err_msg = f"❌ {error or 'Kanaly tapyp bolmady'}"
        if prompt_message_id:
            await bot.edit_message_text(text=err_msg, chat_id=message.chat.id, message_id=prompt_message_id, reply_markup=get_back_to_admin_panel_kb())
        else:
            await message.answer(err_msg, reply_markup=get_back_to_admin_panel_kb())
        return
        
    channel_id = str(chat.id)
    channel_url = f"https://t.me/{chat.username}" if chat.username else ""
    
    if channel_url:
        db.add_required_channel(data['req_channel_name'], channel_id, channel_url)
        await state.clear()
        success_msg = f"✅ <b>{data['req_channel_name']}</b> kanaly üstünlikli goşuldy!"
        if prompt_message_id:
            await bot.edit_message_text(text=success_msg, chat_id=message.chat.id, message_id=prompt_message_id, reply_markup=get_back_to_admin_panel_kb())
        else:
            await message.answer(success_msg, reply_markup=get_back_to_admin_panel_kb())
    else:
        await state.update_data(req_channel_id=channel_id)
        await state.set_state(AdminStates.add_req_private_link)
        prompt_text = "<b>Ädim 3/3: Ssylkq</b>\n\n<blockquote>Kanal ýapyk (hususy). Çakylyk ssylkasyny ugradyň (mysal üçin, <code>https://t.me/+...</code>).</blockquote>"
        if prompt_message_id:
            await bot.edit_message_text(text=prompt_text, chat_id=message.chat.id, message_id=prompt_message_id)
        else:
            await state.update_data(prompt_message_id=(await message.answer(prompt_text)).message_id)

@dp.message(AdminStates.add_req_private_link, F.text, IsAdmin())
async def add_req_sub_get_private_link(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    channel_url = message.text.strip()
    
    db.add_required_channel(data['req_channel_name'], data['req_channel_id'], channel_url)
    await state.clear()
    success_msg = f"✅ <b>{data['req_channel_name']}</b> kanal üstünlikli goşuldy!"
    if prompt_message_id:
        await bot.edit_message_text(text=success_msg, chat_id=message.chat.id, message_id=prompt_message_id, reply_markup=get_back_to_admin_panel_kb())
    else:
        await message.answer(success_msg, reply_markup=get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_list_req_subs", IsAdmin())
async def list_req_subs(call: CallbackQuery):
    channels = db.get_required_channels()
    if not channels:
        await call.answer("📭 Kanallaryň sanawy boş.", show_alert=True)
        return
    text = "📄 <b>Hökmany kanallar:</b>\n\n"
    builder = InlineKeyboardBuilder()
    for pk_id, name, channel_id, url in channels:
        text += f"▪️ <b>{name}</b> ({channel_id})\n🔗 {url}\n\n"
        builder.button(text=f"Aýyr {name}", callback_data=f"admin_del_req_sub_{pk_id}", icon_custom_emoji_id=EMOJI_IDS["remove"], style="danger")
    builder.button(text="Yza", callback_data="admin_req_subs", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    builder.adjust(1)
    await call.message.edit_text(text, reply_markup=builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_del_req_sub_"), IsAdmin())
async def delete_req_sub(call: CallbackQuery):
    pk_id = int(call.data.split("_")[-1])
    db.delete_required_channel(pk_id)
    await call.answer("✅ Kanal aýyryldy.", show_alert=True)
    await list_req_subs(call)

@dp.callback_query(F.data == "admin_download_db", IsChiefAdmin())
async def download_db_handler(call: CallbackQuery):
    db_file = FSInputFile(DB_FILE)
    await call.message.answer_document(db_file, caption="📦 Database ätiýaçlyk nusgasy (Backup).")
    await call.answer()

@dp.callback_query(F.data == "admin_upload_db", IsChiefAdmin())
async def upload_db_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.upload_db_file)
    prompt = await call.message.edit_text("📥 Database dikeltmek üçin onuň faýlyny (.db) ugradyň.", reply_markup=get_back_to_admin_panel_kb())
    await state.update_data(prompt_message_id=prompt.message_id)
    await call.answer()

@dp.message(AdminStates.upload_db_file, F.document, IsChiefAdmin())
async def upload_db_process(message: Message, state: FSMContext, bot: Bot):
    await clean_prompt(state, message.chat.id, bot)
    if not message.document.file_name.endswith('.db'):
        prompt = await message.answer("❌ .db giňeltmeli faýly ugradyň.", reply_markup=get_back_to_admin_panel_kb())
        await state.update_data(prompt_message_id=prompt.message_id)
        return
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, DB_FILE)
    await message.answer("✅ Database üstünlikli dikeldildi!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running!"

def run_server():
    app.run(host="0.0.0.0", port=8080)

async def main():
    Thread(target=run_server, daemon=True).start()
    dp.message.middleware(MasterMiddleware())
    dp.callback_query.middleware(MasterMiddleware())
    
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())