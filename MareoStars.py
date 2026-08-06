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
ADMIN_IDS = [7315359232]
CHIEF_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None
ADMIN_CHANNEL_ID = -1004347969397
PAYMENTS_CHANNEL_ID = -1003870504084
PAYMENTS_CHANNEL_LINK = "https://t.me/MAREO_STARSPAY"
MIN_REFERRALS_FOR_WITHDRAWAL = 0
DB_FILE = "MareoStars.db"

# milas
START_PHOTO_URL = "https://freeimage.host/i/CkFEO4S"

# milas
TGRASS_API_KEY = "4473937fc919414daf11f42342aa4b18"

# flyer FL-pndrjg-ntIPBY-zRAOfM-ELiFkA
FLYER_API_KEY = ""

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
    "start": "<tg-emoji emoji-id=\"{start_emoji}\">😎</tg-emoji> <b>Добро пожаловать</b>",
    "profile": "<tg-emoji emoji-id=\"{profile_icon}\">👤</tg-emoji> <b>Имя:</b> @{username}\n"
               "<tg-emoji emoji-id=\"{id_icon}\">💳</tg-emoji> <b>ID:</b> <code>{user_id}</code>\n"
               "<tg-emoji emoji-id=\"{balance_icon}\">💰</tg-emoji> <b>Баланс:</b> {balance} <tg-emoji emoji-id=\"{star_icon}\">⭐️</tg-emoji>\n"
               "<tg-emoji emoji-id=\"{friends_icon}\">👥</tg-emoji> <b>Приглашено друзей:</b> {referrals_count}",
    "invite": "<tg-emoji emoji-id=\"{star_emoji}\">⭐️</tg-emoji> <b>Пригласить друзей</b>\n\n"
              "За каждого друга, который перейдет по твоей ссылке, ты получаешь <b>{ref_bonus}</b> <tg-emoji emoji-id=\"{star_emoji}\">⭐️</tg-emoji>!\n\n"
              "<tg-emoji emoji-id=\"{link_emoji}\">🔗</tg-emoji> <b>Твоя реферальная ссылка:</b>\n"
              "<code>{ref_link}</code>\n\n"
              "<tg-emoji emoji-id=\"{celebration_emoji}\">🎉</tg-emoji> Приглашай по этой ссылке своих друзей, отправляй её во все чаты и зарабатывай Звёзды!",
    "withdraw_title": "<tg-emoji emoji-id=\"{withdraw_emoji}\">📤</tg-emoji> <b>Вывод средств</b>\n\nОбменяйте ваши звёзды на подарки!\n\n"
                      "<blockquote><tg-emoji emoji-id=\"{card_icon}\">💳</tg-emoji> <b>Ваш баланс:</b> {balance} <tg-emoji emoji-id=\"{star_premium_icon}\">⭐️</tg-emoji></blockquote>\n\n",
    "bonus": "<tg-emoji emoji-id=\"{bonus_emoji}\">🎁</tg-emoji> <b>Ежедневный бонус</b>\n\n"
             "<blockquote>Вы можете получить случайный бонус один раз в 24 часа! Нажмите на кнопку, чтобы испытать удачу.</blockquote>",
    "bonus_claimed": "🎁 Поздравляем! Вы получили {bonus_amount} ⭐!",
    "bonus_wait": "😔 Следующий бонус через {hours} ч. {minutes} мин.",
    "promo": "<tg-emoji emoji-id=\"{gift_icon}\">🎁</tg-emoji> <b>Введите промокод:</b>\n\n<blockquote>Пример: <code>STAR50</code></blockquote>",
    "promo_success": "✅ Промокод активирован! Вам начислено {reward} ⭐.",
    "promo_fail_used": "🚫 Вы уже использовали этот промокод.",
    "promo_fail_general": "❌ Промокод не существует или истек.",
    "top": "<tg-emoji emoji-id=\"{top_emoji}\">🥇</tg-emoji> <b>Топ пользователей</b>\n\n<blockquote>Кто здесь самый активный? Узнайте лидеров по звёздам и приглашениям.</blockquote>",
    "top_balance_title": "<tg-emoji emoji-id=\"{top_emoji}\">🥇</tg-emoji> <b>Топ-5 по звёздам:</b>\n\n",
    "top_referrals_title": "<tg-emoji emoji-id=\"{top_emoji}\">🥇</tg-emoji> <b>Топ 5 рефералов за 24 часа:</b>\n\n",
    "top_no_users": "<i>Никого нет.</i>",
    "top_not_in_top": "\n\n🚫 Ты не попал в топ! | {count} рефералов за 24ч.",
    "request_submitted_for_review": "✅ Твоя заявка <code>#{request_uid}</code> отправлена на рассмотрение. Ожидай одобрения от администратора в течении нескольких дней.",
    "btn_earn": "Пригласить друга",
    "btn_withdraw": "Вывести",
    "btn_profile": "Мой профиль",
    "btn_bonus": "Бонус",
    "btn_promo": "Промокод",
    "btn_top": "Топ",
    "btn_invite": "Пригласить друзей",
    "btn_back": "Назад",
    "btn_back_to_menu": "Вернуться в меню",
    "btn_copy_link": "Реф ссылка",
    "btn_cancel": "Отмена",
    "btn_top_balance": "Топ по звёздам",
    "btn_top_referrals": "Топ по рефералам",
    "btn_check_status": "Канал выплат",
    "sub_check_fail": "<tg-emoji emoji-id=\"{warning_icon}\">❗️</tg-emoji> <b>Для использования бота необходимо подписаться на каналы:</b>",
    "sub_check_button": "Я подписался",
    "sub_check_success": "✅ Спасибо за подписку!",
    "sub_check_not_yet": "❗️ Вы еще не подписались на все каналы.",
    "referral_notification": "🎉 По вашей ссылке присоединился новый пользователь: {new_user_display}!\nВам начислено <b>{ref_bonus}</b> ⭐.",
    "alert_action_canceled": "Действие отменено",
    "alert_need_more_refs": "❗️ Для вывода нужно пригласить ещё {diff} друзей.",
    "alert_pending_withdrawal": "❗️ У вас уже есть заявка на рассмотрении.",
    "alert_insufficient_stars": "❌ Минимальная сумма вывода 25⭐. У вас: {balance}⭐",
    "status_approved": "✅ Ваша заявка (#{uid}) одобрена! Списано {amount} ⭐ за «{gift_name}».",
    "status_declined": "❌ Ваша заявка (#{uid}) отклонена.\n\nПричина: {reason}",
    "link_copied": "✅ Реферальная ссылка скопирована в буфер обмена!",
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
    
    while s_count > 0:
        if s_count >= 2:
            sizes.append(2)
            s_count -= 2
        else:
            sizes.append(1)
            s_count -= 1
            
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
    builder.button(text="Рассылка", callback_data="admin_broadcast", icon_custom_emoji_id=EMOJI_IDS["broadcast"], style="primary")
    builder.button(text="Статистика", callback_data="admin_stats", icon_custom_emoji_id=EMOJI_IDS["stats"], style="primary")
    builder.button(text="Статистика TGrass", callback_data="admin_stats_tgrass", icon_custom_emoji_id=EMOJI_IDS["stats"], style="primary")
    builder.button(text="Статистика PiarFlow", callback_data="admin_stats_piarflow", icon_custom_emoji_id=EMOJI_IDS["stats"], style="primary")
    builder.button(text="Бонус настройки", callback_data="admin_bonus_settings", icon_custom_emoji_id=EMOJI_IDS["edit"], style="primary")
    builder.button(text="Промокоды", callback_data="admin_promo_menu", icon_custom_emoji_id=EMOJI_IDS["promo"], style="primary")
    builder.button(text="Каналы", callback_data="admin_req_subs", icon_custom_emoji_id=EMOJI_IDS["lock"], style="primary")
    builder.button(text="Баланс", callback_data="admin_balance_change", icon_custom_emoji_id=EMOJI_IDS["money"], style="primary")
    builder.button(text="Реферальный бонус", callback_data="admin_ref_bonus", icon_custom_emoji_id=EMOJI_IDS["star"], style="primary")    
    if db.is_chief_admin(user_id):
        builder.button(text="Админы", callback_data="admin_manage_admins", icon_custom_emoji_id=EMOJI_IDS["lock"], style="primary")
    builder.button(text="Скачать БД", callback_data="admin_download_db", icon_custom_emoji_id=EMOJI_IDS["db_download"], style="primary")
    builder.button(text="Установить БД", callback_data="admin_upload_db", icon_custom_emoji_id=EMOJI_IDS["db_upload"], style="primary")
    builder.adjust(2)
    return builder.as_markup()

def get_back_to_admin_panel_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад в админ-панель", callback_data="admin_panel", icon_custom_emoji_id=EMOJI_IDS["back"], style="danger")
    return builder.as_markup()

def get_admin_withdraw_kb(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Одобрить", callback_data=f"withdraw_approve_{request_id}", icon_custom_emoji_id=EMOJI_IDS["check"], style="success")
    builder.button(text="Отклонить", callback_data=f"withdraw_decline_{request_id}", icon_custom_emoji_id=EMOJI_IDS["remove"], style="danger")
    builder.adjust(2)
    return builder.as_markup()

def get_payment_channel_kb(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data=f"payment_send_{request_id}", style="success")
    builder.button(text="❌ Отключить", callback_data=f"payment_decline_{request_id}", style="danger")
    builder.adjust(2)
    return builder.as_markup()

def get_payment_channel_status_text(request_id: int, user_id: int, amount: float, gift_name: str, status: str = "pending"):
    username = db.get_user_username(user_id)
    
    if status == "pending":
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['status_icon']}\">🔄</tg-emoji> Ожидает обработки <tg-emoji emoji-id=\"{EMOJI_IDS['status_wait']}\">⚙️</tg-emoji>"
    elif status == "sent":
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['gift_sent']}\">🎁</tg-emoji> Подарок отправлен"
    elif status == "declined":
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['declined']}\">🚫</tg-emoji> Отказано"
    else:
        status_text = f"<tg-emoji emoji-id=\"{EMOJI_IDS['status_icon']}\">🔄</tg-emoji> Ожидает обработки"
    
    text = (
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['check_premium']}\">✅</tg-emoji> <b>Заявка на вывод №{request_id}</b>\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['user_icon']}\">👤</tg-emoji> <b>Пользователь:</b> @{username} | ID {user_id}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['star_premium']}\">⭐️</tg-emoji> <b>Сумма:</b> {amount} ⭐\n"
        f"<tg-emoji emoji-id=\"{EMOJI_IDS['gift_icon']}\">🎁</tg-emoji> <b>Подарок:</b> {gift_name}\n\n"
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

# --- TGRASS VE PIARFLOW İSTATİSTİK APİ FONKSİYONLARI ---
async def get_tgrass_statistics():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://tgrass.space/statistics?date={today}"
    headers = {
        "Auth": TGRASS_API_KEY
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"TGrass stats error: {e}")
        return None

async def get_piarflow_statistics():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://piarflow.com/v1/traffic_bot/stats?date={today}"
    headers = {
        "Authorization": f"Bearer {PIARFLOW_API_KEY}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logging.error(f"PiarFlow stats error: {e}")
        return None

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
                                                'name': "Спонсор",
                                                'url': link,
                                                'icon_custom_emoji_id': "6039381989985882045"
                                            })
                                else:
                                    for s in sponsors:
                                        if s.get("status") != "subscribed" and s.get("link"):
                                            not_subbed.append({
                                                'name': "Спонсор",
                                                'url': s.get("link"),
                                                'icon_custom_emoji_id': "6039381989985882045"
                                            })
                        else:
                            for s in sponsors:
                                if s.get("status") != "subscribed" and s.get("link"):
                                    not_subbed.append({
                                        'name': "Спонсор",
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
                             not_subscribed_channels.append({'name': f" {offer.get('title', 'Спонсор')}", 'url': offer['link'], 'icon_custom_emoji_id': "6039381989985882045"})
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
                                task_name = task.get("name") or task.get("title") or "Спонсор"
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

# --- ARA YAZILIM (ИСПРАВЛЕНА ЗАЩИТА: КНОПКИ АДМИНОВ НЕ ПРОВЕРЯЮТ СПОНСОРОВ И НЕ УДАЛЯЮТ СООБЩЕНИЯ В ЧАТАХ/КАНАЛАХ) ---
class MasterMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: types.TelegramObject, data: Dict) -> Any:
        user = data.get('event_from_user')
        if not user:
            return await handler(event, data)

        db.update_user_info(user.id, user.username, user.first_name)

        # Полностью исключаем любые кнопки админ-панели, одобрения, отклонения и отправки для администратора!
        if db.is_admin(user.id):
            if (isinstance(event, types.Message) and event.text and event.text.startswith('/admin')) or \
               (isinstance(event, types.CallbackQuery) and event.data and (
                   event.data.startswith('admin_') or 
                   event.data.startswith('withdraw_approve_') or 
                   event.data.startswith('withdraw_decline_') or 
                   event.data.startswith('decline_prompt_') or 
                   event.data.startswith('payment_send_') or 
                   event.data.startswith('payment_decline_')
               )) or \
               (isinstance(event, types.CallbackQuery) and event.message and event.message.chat.id in [ADMIN_CHANNEL_ID, PAYMENTS_CHANNEL_ID]):
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
        await call.answer("❌ Ошибка при обработке запроса.", show_alert=True)
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
    
    admin_text = (f"✨ Новая заявка (Подарок) #{request_uid} ✨\n\n"
                  f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                  f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Стоимость:</b> {cost} ⭐\n"
                  f"🕓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
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
        await call.answer("❌ Запрос не найден.", show_alert=True)
        return
    uid, user_id, username, amount, gift_name, status, _, details, payment_msg_id = request_data
    if status != 'pending':
        await call.answer(f"⚠️ Этот запрос уже был обработан (статус: {status}).", show_alert=True)
        return
    db.update_balance(user_id, -amount)
    db.update_withdrawal_status(request_id, 'approved')
    admin_channel_text = (f"✅ <b>Заявка #{uid} Одобрена</b> админом {admin_name}\n\n"
                          f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Списано:</b> {amount} ⭐")
    await call.message.edit_text(admin_channel_text, reply_markup=None)
    user_notification = get_text('status_approved').format(uid=uid, gift_name=gift_name, amount=amount)
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send approval notification to user {user_id}: {e}")
    await call.answer("✅ Одобрено.", show_alert=True)

@dp.callback_query(F.data.startswith("withdraw_decline_"), IsAdmin())
async def decline_withdraw_start(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[-1])
    request_data = db.get_withdrawal_request(request_id)
    if not request_data or request_data[5] != 'pending':
        await call.answer("⚠️ Этот запрос уже был обработан.", show_alert=True)
        return

    channel_chat_id = call.message.chat.id
    channel_message_id = call.message.message_id

    builder = InlineKeyboardBuilder()
    builder.button(
        text="Ввести причину",
        callback_data=f"decline_prompt_{request_id}_{channel_chat_id}_{channel_message_id}",
        icon_custom_emoji_id=EMOJI_IDS["edit"],
        style="danger"
    )

    try:
        await bot.send_message(
            chat_id=call.from_user.id,
            text=f"Вы собираетесь отклонить заявку #{request_data[0]}. Нажмите кнопку ниже, чтобы указать причину.",
            reply_markup=builder.as_markup()
        )
        await call.answer("Нажмите кнопку в личном чате с ботом, чтобы продолжить.", show_alert=True)
    except TelegramAPIError as e:
        await call.answer(f"❌ Не удалось отправить сообщение в ЛС. Ошибка: {e}", show_alert=True)
        logging.error(f"Could not send PM to admin {call.from_user.id}: {e}")

@dp.callback_query(F.data.startswith("decline_prompt_"), IsAdmin())
async def decline_reason_prompt(call: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        parts = call.data.split("_")
        request_id = int(parts[2])
        channel_chat_id = int(parts[3])
        channel_message_id = int(parts[4])
    except (ValueError, IndexError):
        await call.answer("❌ Ошибка в данных. Попробуйте снова.", show_alert=True)
        logging.error(f"Could not parse decline_prompt callback data: {call.data}")
        return

    await state.set_state(AdminStates.decline_reason)
    await state.update_data(
        request_id=request_id,
        channel_chat_id=channel_chat_id,
        channel_message_id=channel_message_id
    )

    prompt_message = await call.message.edit_text(
        "Введите причину отклонения. Этот текст будет отправлен пользователю.",
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
        await bot.send_message(message.from_user.id, "❌ Ошибка.")
        return
    admin_name = html.quote(message.from_user.username or message.from_user.first_name)
    request_data = db.get_withdrawal_request(request_id)
    if not request_data:
        await bot.send_message(message.from_user.id, f"❌ Заявка #{request_id} не найдена.")
        return
    uid, user_id, username, amount, gift_name, status, _, details, payment_msg_id = request_data
    if status != 'pending':
        await bot.send_message(message.from_user.id, f"⚠️ Заявка #{uid} уже обработана (Статус: {status}).")
        return
    db.update_withdrawal_status(request_id, 'declined', reason)
    admin_channel_text = (f"❌ <b>Заявка #{uid} Отклонена</b> админом {admin_name}\n\n"
                          f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Списано:</b> {amount} ⭐\n\n"
                          f"📝 <b>Причина:</b> {html.quote(reason)}")
    try:
        await bot.edit_message_text(admin_channel_text, chat_id=channel_chat_id, message_id=channel_message_id, reply_markup=None)
    except TelegramAPIError as e:
        logging.error(f"Could not edit message in admin channel: {e}")
    user_notification = get_text('status_declined').format(uid=uid, reason=html.quote(reason))
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send decline notification to user {user_id}: {e}")
    await bot.send_message(message.from_user.id, f"✅ Заявка #{uid} отклонена.", reply_markup=get_back_to_admin_panel_kb())

# --- ÖDEME KANALI İŞLEYİCİLERİ ---
@dp.callback_query(F.data.startswith("payment_send_"), IsAdmin())
async def payment_send_handler(call: CallbackQuery, bot: Bot):
    try:
        request_id = int(call.data.split("_")[-1])
    except (ValueError, IndexError):
        await call.answer("❌ Ошибка ID заявки", show_alert=True)
        return
    
    request_data = db.get_withdrawal_request_by_id(request_id)
    if not request_data:
        await call.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    request_id_db, uid, user_id, username, amount, gift_name, status, decline_reason, details, payment_message_id = request_data
    
    if status != 'pending':
        await call.answer(f"⚠️ Этот запрос уже был обработан (статус: {status})", show_alert=True)
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
    await call.answer("✅ Отправлено!", show_alert=True)

@dp.callback_query(F.data.startswith("payment_decline_"), IsAdmin())
async def payment_decline_handler(call: CallbackQuery, bot: Bot):
    try:
        request_id = int(call.data.split("_")[-1])
    except (ValueError, IndexError):
        await call.answer("❌ Ошибка ID заявки", show_alert=True)
        return
    
    request_data = db.get_withdrawal_request_by_id(request_id)
    if not request_data:
        await call.answer("❌ Заявка не найдена", show_alert=True)
        return
    
    request_id_db, uid, user_id, username, amount, gift_name, status, decline_reason, details, payment_message_id = request_data
    
    if status != 'pending':
        await call.answer(f"⚠️ Этот запрос уже был обработан (статус: {status})", show_alert=True)
        return
    
    db.update_withdrawal_status(request_id, 'declined', 'Отклонено администратором')
    
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
    
    user_notification = get_text('status_declined').format(uid=uid, reason="Отклонено администратором")
    try:
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e:
        logging.warning(f"Failed to send decline notification to user {user_id}: {e}")
    await call.answer("❌ Отклонено!", show_alert=True)

# --- АДМИН ПАНЕЛЬ ---
@dp.message(Command("admin"), IsAdmin())
async def admin_panel_cmd(message: Message, state: FSMContext):
    await state.clear()
    text = "⚙️ <b>Панель администратора</b>\n\nВыберите необходимое действие:"
    await send_photo_or_message(message.chat.id, text, get_admin_kb(message.from_user.id))

@dp.callback_query(F.data == "admin_panel", IsAdmin())
async def admin_panel_call(call: CallbackQuery, state: FSMContext):
    await state.clear()
    text = "⚙️ <b>Панель администратора</b>\n\nВыберите необходимое действие:"
    await send_photo_or_message_to_target(call, text, get_admin_kb(call.from_user.id))
    await call.answer()

@dp.callback_query(F.data == "admin_stats", IsAdmin())
async def admin_stats_call(call: CallbackQuery):
    stats = db.get_stats()
    text = (f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
            f"🟢 Новых за 24ч: <b>{stats['new_users_24h']}</b>\n"
            f"💰 Общий баланс: <b>{stats['total_balance']} ⭐</b>\n\n"
            f"📥 Заявок на рассмотрении: <b>{stats['withdraw_pending']}</b>\n"
            f"✅ Одобрено заявок: <b>{stats['withdraw_approved']}</b>\n"
            f"❌ Отклонено заявок: <b>{stats['withdraw_declined']}</b>\n"
            f"📤 Выведено всего: <b>{stats['withdrawn_sum']} ⭐</b>")
    await send_photo_or_message_to_target(call, text, get_back_to_admin_panel_kb())
    await call.answer()

@dp.callback_query(F.data == "admin_stats_tgrass", IsAdmin())
async def admin_stats_tgrass_handler(call: CallbackQuery):
    await call.answer("Загрузка статистики TGrass...")
    data = await get_tgrass_statistics()
    today = datetime.now().strftime('%Y-%m-%d')
    if data:
        subs = data.get("subs_count", 0)
        unsubs = data.get("unsubs_count", 0)
        income = data.get("income", 0.0)
        text = (
            f"📊 <b>Статистика TGrass за {today}:</b>\n\n"
            f"➕ <b>Подписок:</b> {subs}\n"
            f"➖ <b>Отписок:</b> {unsubs}\n"
            f"💰 <b>Доход:</b> {income} ₽"
        )
    else:
        text = "❌ Не удалось получить статистику TGrass или данные отсутствуют."
    await send_photo_or_message_to_target(call, text, get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_stats_piarflow", IsAdmin())
async def admin_stats_piarflow_handler(call: CallbackQuery):
    await call.answer("Загрузка статистики PiarFlow...")
    data = await get_piarflow_statistics()
    today = datetime.now().strftime('%Y-%m-%d')
    if data and data.get("status") == "ok":
        bot_info = data.get("bot", {})
        stats_info = data.get("stats", {})
        
        sold_today = stats_info.get("sold_subs", 0)
        earned_today = stats_info.get("earned", 0)
        
        total_sold = bot_info.get("sold_subs", 0)
        total_earned = bot_info.get("earned", 0)
        
        text = (
            f"📊 <b>Статистика PiarFlow</b>\n\n"
            f"📅 <b>За сегодня ({today}):</b>\n"
            f"➕ <b>Продано подписок:</b> {sold_today}\n"
            f"💰 <b>Заработано:</b> {earned_today} ₽\n\n"
            f"📈 <b>За все время:</b>\n"
            f"➕ <b>Всего подписок:</b> {total_sold}\n"
            f"💰 <b>Всего заработано:</b> {total_earned} ₽"
        )
    else:
        text = "❌ Не удалось получить статистику PiarFlow или данные отсутствуют."
    await send_photo_or_message_to_target(call, text, get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_broadcast", IsAdmin())
async def admin_broadcast_call(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.broadcast_message)
    text = "📢 <b>Рассылка сообщений</b>\n\nОтправьте текст, фото или видео с текстом, которое хотите разослать всем пользователям:"
    await send_photo_or_message_to_target(call, text, get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.broadcast_message, IsAdmin())
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = db.get_all_user_ids()
    sent, failed = 0, 0
    await message.answer(f"⏳ Рассылка началась для <b>{len(users)}</b> пользователей...")
    for user_id in users:
        try:
            await message.copy_to(user_id)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await message.answer(f"✅ <b>Рассылка завершена!</b>\n\nУспешно отправлено: <b>{sent}</b>\nНе доставлено: <b>{failed}</b>", reply_markup=get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_bonus_settings", IsAdmin())
async def admin_bonus_settings_call(call: CallbackQuery):
    min_b = db.get_setting('daily_bonus_min')
    max_b = db.get_setting('daily_bonus_max')
    text = f"🎁 <b>Настройки ежедневного бонуса</b>\n\nТекущий диапазон: <b>от {min_b} до {max_b} ⭐</b>\n\nВыберите параметр для изменения:"
    builder = InlineKeyboardBuilder()
    builder.button(text="Мин. бонус", callback_data="admin_set_bonus_min", style="primary")
    builder.button(text="Макс. бонус", callback_data="admin_set_bonus_max", style="primary")
    builder.button(text="Назад в админ-панель", callback_data="admin_panel", style="danger")
    builder.adjust(2, 1)
    await send_photo_or_message_to_target(call, text, builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_set_bonus_"), IsAdmin())
async def admin_set_bonus_val(call: CallbackQuery, state: FSMContext):
    param = call.data.split("_")[-1]
    await state.set_state(AdminStates.set_bonus_amount)
    await state.update_data(bonus_param=param)
    text = f"Введите новое значение для <b>{'минимального' if param == 'min' else 'максимального'}</b> бонуса (например, <code>0.5</code>):"
    await send_photo_or_message_to_target(call, text, get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.set_bonus_amount, IsAdmin())
async def process_set_bonus_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    param = data.get("bonus_param", "min")
    try:
        val = float(message.text.strip().replace(',', '.'))
        db.set_setting(f'daily_bonus_{param}', str(val))
        await message.answer(f"✅ Успешно обновлено значение до <b>{val} ⭐</b>", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Ошибка. Введите корректное число (например, 0.5):")

@dp.callback_query(F.data == "admin_promo_menu", IsAdmin())
async def admin_promo_menu(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать промокод", callback_data="admin_promo_create", style="success")
    builder.button(text="Список промокодов", callback_data="admin_promo_list", style="primary")
    builder.button(text="Назад в админ-панель", callback_data="admin_panel", style="danger")
    builder.adjust(1)
    await send_photo_or_message_to_target(call, "🎁 <b>Управление промокодами</b>\n\nВыберите действие:", builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_promo_create", IsAdmin())
async def admin_promo_create_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.create_promo_code)
    await send_photo_or_message_to_target(call, "Введите код промокода (например, <code>STAR50</code>):", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.create_promo_code, IsAdmin())
async def admin_promo_create_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AdminStates.create_promo_reward)
    await message.answer("Введите сумму награды в звёздах (например, <code>10</code>):")

@dp.message(AdminStates.create_promo_reward, IsAdmin())
async def admin_promo_create_reward(message: Message, state: FSMContext):
    try:
        reward = float(message.text.strip().replace(',', '.'))
        await state.update_data(reward=reward)
        await state.set_state(AdminStates.create_promo_activations)
        await message.answer("Введите количество активаций (например, <code>100</code>):")
    except ValueError:
        await message.answer("❌ Введите корректное число:")

@dp.message(AdminStates.create_promo_activations, IsAdmin())
async def admin_promo_create_activations(message: Message, state: FSMContext):
    try:
        activations = int(message.text.strip())
        data = await state.get_data()
        db.create_promocode(data['code'], data['reward'], activations)
        await message.answer(f"✅ Промокод <code>{data['code']}</code> создан!\nНаграда: {data['reward']} ⭐\nАктиваций: {activations}", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите целое число:")

@dp.callback_query(F.data == "admin_promo_list", IsAdmin())
async def admin_promo_list_call(call: CallbackQuery):
    promos = db.get_all_promocodes()
    if not promos:
        await send_photo_or_message_to_target(call, "<i>Список промокодов пуст.</i>", get_back_to_admin_panel_kb())
    else:
        builder = InlineKeyboardBuilder()
        text = "🎁 <b>Активные промокоды:</b>\n\n"
        for code, reward, left in promos:
            text += f"• <code>{code}</code> — {reward} ⭐ (Осталось: {left})\n"
            builder.button(text=f"Удалить {code}", callback_data=f"admin_promo_del_{code}", style="danger")
        builder.button(text="Назад в админ-панель", callback_data="admin_panel", style="danger")
        builder.adjust(1)
        await send_photo_or_message_to_target(call, text, builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_promo_del_"), IsAdmin())
async def admin_promo_del(call: CallbackQuery):
    code = call.data.split("_")[-1]
    db.delete_promocode(code)
    await call.answer(f"✅ Промокод {code} удалён!", show_alert=True)
    await admin_promo_list_call(call)

@dp.callback_query(F.data == "admin_req_subs", IsAdmin())
async def admin_req_subs_call(call: CallbackQuery):
    channels = db.get_required_channels()
    text = "🔒 <b>Управление обязательной подпиской</b>\n\nТекущие каналы в базе:\n"
    builder = InlineKeyboardBuilder()
    for pk, name, cid, url in channels:
        text += f"• {name} (<code>{cid}</code>) -> {url}\n"
        builder.button(text=f"Удалить: {name}", callback_data=f"admin_req_del_{pk}", style="danger")
    builder.button(text="Добавить канал", callback_data="admin_req_add", style="success")
    builder.button(text="Назад в админ-панель", callback_data="admin_panel", style="danger")
    builder.adjust(1)
    await send_photo_or_message_to_target(call, text, builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_req_add", IsAdmin())
async def admin_req_add_call(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_req_channel_name)
    await send_photo_or_message_to_target(call, "Введите название кнопки для канала (например, <code>Наш канал</code>):", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.add_req_channel_name, IsAdmin())
async def admin_req_add_name(message: Message, state: FSMContext):
    await state.update_data(c_name=message.text.strip())
    await state.set_state(AdminStates.add_req_channel_entry)
    await message.answer("Перешлите любое сообщение из канала или введите его ID/Юзернейм (например, <code>-1001234567890</code> или <code>@mychannel</code>):")

@dp.message(AdminStates.add_req_channel_entry, IsAdmin())
async def admin_req_add_entry(message: Message, state: FSMContext, bot: Bot):
    c_id = None
    if message.forward_from_chat:
        c_id = str(message.forward_from_chat.id)
    else:
        c_id = message.text.strip()
    
    try:
        chat = await bot.get_chat(c_id)
        cid_str = str(chat.id)
        invite_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
        data = await state.get_data()
        if invite_link:
            db.add_required_channel(data['c_name'], cid_str, invite_link)
            await message.answer(f"✅ Канал <b>{data['c_name']}</b> успешно добавлен!", reply_markup=get_back_to_admin_panel_kb())
            await state.clear()
        else:
            await state.update_data(cid=cid_str)
            await state.set_state(AdminStates.add_req_private_link)
            await message.answer("Канал закрытый. Введите ссылку-приглашение для этого канала:")
    except Exception as e:
        await message.answer(f"❌ Не удалось найти канал или бот не администратор в нём.\nОшибка: <code>{e}</code>")

@dp.message(AdminStates.add_req_private_link, IsAdmin())
async def admin_req_add_priv_link(message: Message, state: FSMContext):
    data = await state.get_data()
    url = message.text.strip()
    db.add_required_channel(data['c_name'], data['cid'], url)
    await message.answer(f"✅ Канал <b>{data['c_name']}</b> успешно добавлен!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

@dp.callback_query(F.data.startswith("admin_req_del_"), IsAdmin())
async def admin_req_del_call(call: CallbackQuery):
    pk = int(call.data.split("_")[-1])
    db.delete_required_channel(pk)
    await call.answer("✅ Канал удалён!", show_alert=True)
    await admin_req_subs_call(call)

@dp.callback_query(F.data == "admin_balance_change", IsAdmin())
async def admin_balance_change_call(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.balance_change_user_id)
    await send_photo_or_message_to_target(call, "Введите Telegram ID пользователя, которому хотите изменить баланс:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.balance_change_user_id, IsAdmin())
async def admin_balance_change_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите корректный ID из цифр:")
        return
    user_id = int(message.text)
    if not db.user_exists(user_id):
        await message.answer("❌ Пользователь с таким ID не найден в базе!")
        return
    await state.update_data(target_id=user_id)
    await state.set_state(AdminStates.balance_change_amount)
    await message.answer("Введите сумму, которую хотите <b>добавить</b> (или отрицательное число чтобы забрать, например <code>-20</code>):")

@dp.message(AdminStates.balance_change_amount, IsAdmin())
async def admin_balance_change_val(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(',', '.'))
        data = await state.get_data()
        target_id = data['target_id']
        db.update_balance(target_id, amount)
        new_bal = db.get_user_balance(target_id)
        await message.answer(f"✅ Баланс пользователя <code>{target_id}</code> изменён на <b>{amount} ⭐</b>.\nТекущий баланс: <b>{new_bal} ⭐</b>", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректное число:")

@dp.callback_query(F.data == "admin_ref_bonus", IsAdmin())
async def admin_ref_bonus_call(call: CallbackQuery, state: FSMContext):
    current = db.get_setting('ref_bonus')
    await state.set_state(AdminStates.set_ref_bonus)
    await send_photo_or_message_to_target(call, f"⭐️ <b>Настройка реферального бонуса</b>\n\nТекущий бонус за реферала: <b>{current} ⭐</b>\n\nВведите новое значение:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.set_ref_bonus, IsAdmin())
async def admin_ref_bonus_val(message: Message, state: FSMContext):
    try:
        val = float(message.text.strip().replace(',', '.'))
        db.set_setting('ref_bonus', str(val))
        await message.answer(f"✅ Успешно установлено значение реферального бонуса: <b>{val} ⭐</b>", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число (например, 1.5):")

@dp.callback_query(F.data == "admin_manage_admins", IsChiefAdmin())
async def admin_manage_admins_call(call: CallbackQuery):
    admins = db.get_admins()
    text = "🔐 <b>Управление администраторами</b>\n\nТекущие админы:\n"
    builder = InlineKeyboardBuilder()
    for uid, is_chief in admins:
        role = "(Главный)" if is_chief else ""
        text += f"• <code>{uid}</code> {role}\n"
        if not is_chief:
            builder.button(text=f"Удалить {uid}", callback_data=f"admin_del_admin_{uid}", style="danger")
    builder.button(text="Добавить админа", callback_data="admin_add_admin", style="success")
    builder.button(text="Назад в админ-панель", callback_data="admin_panel", style="danger")
    builder.adjust(1)
    await send_photo_or_message_to_target(call, text, builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_add_admin", IsChiefAdmin())
async def admin_add_admin_call(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_admin_id)
    await send_photo_or_message_to_target(call, "Введите Telegram ID нового администратора:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.add_admin_id, IsChiefAdmin())
async def admin_add_admin_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID должен состоять из цифр:")
        return
    uid = int(message.text)
    db.add_admin(uid)
    await message.answer(f"✅ Пользователь <code>{uid}</code> назначен администратором!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

@dp.callback_query(F.data.startswith("admin_del_admin_"), IsChiefAdmin())
async def admin_del_admin_call(call: CallbackQuery):
    uid = int(call.data.split("_")[-1])
    db.remove_admin(uid)
    await call.answer("✅ Администратор удалён!", show_alert=True)
    await admin_manage_admins_call(call)

@dp.callback_query(F.data == "admin_download_db", IsAdmin())
async def admin_download_db_call(call: CallbackQuery):
    if os.path.exists(DB_FILE):
        file = FSInputFile(DB_FILE)
        await call.message.answer_document(file, caption="💾 Резервная копия базы данных MareoStars.db")
    else:
        await call.answer("❌ Файл базы данных не найден!", show_alert=True)
    await call.answer()

@dp.callback_query(F.data == "admin_upload_db", IsAdmin())
async def admin_upload_db_call(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.upload_db_file)
    await send_photo_or_message_to_target(call, "📤 Отправьте файл новой базы данных (с названием <code>MareoStars.db</code>) как документ:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.upload_db_file, IsAdmin(), F.document)
async def admin_upload_db_file(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    if doc.file_name != DB_FILE:
        await message.answer(f"❌ Название файла должно быть ровно <code>{DB_FILE}</code>!")
        return
    file_info = await bot.get_file(doc.file_id)
    await bot.download_file(file_info.file_path, DB_FILE)
    db.setup_database()
    await message.answer("✅ База данных успешно загружена и применена!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

# --- KEEP ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- MAIN ---
async def main():
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    dp.message.middleware(MasterMiddleware())
    dp.callback_query.middleware(MasterMiddleware())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())