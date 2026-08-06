import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
import random
import string
import uuid
import os
import threading
import aiohttp 

from flask import Flask, request, jsonify

from aiogram import Bot, Dispatcher, types, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.types import Message, CallbackQuery, Chat, User, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable, Union

logging.basicConfig(level=logging.INFO)

# --- AYARLAR ---
BOT_TOKEN = "8543293031:AAGQbDsMtQngKcZGiVLjIKE6q3ApJckGNm4"
ADMIN_IDS = [7315359232]
CHIEF_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else None
ADMIN_CHANNEL_ID = -1004382080672
PAYMENTS_CHANNEL_ID = -1004382080672
PAYMENTS_CHANNEL_LINK = "https://t.me/LeopardStarsPay"
MIN_REFERRALS_FOR_WITHDRAWAL = 5
DB_FILE = "LeopardStars.db"

# --- TGRASS & PIARFLOW AYARLARI ---
TGRASS_API_KEY = "2924f4d8ddca414b8b8348892af196f1"
PIARFLOW_API_KEY = "egf1YYGLm1e75doP0dtic1BomOEwQte8"
PIARFLOW_API_URL = "https://piarflow.com/v1"
PORT = 8080

# --- METİNLER & DİLLER ---
LANG_TEXTS = {
    'ru': {
        # General
        "start": "👋 <b>Привет, {user_name}!</b>\n\n"
                 "Добро пожаловать в бота для заработка звёзд! ✨\n\n"
                 "<blockquote>Здесь ты можешь выполнять задания, приглашать друзей и получать за это звёзды, "
                 "которые можно обменять на подарки или реальные деньги. 🎁</blockquote>\n"
                 "🧸 Ваш баланс: <b>{balance}</b> ⭐",
        "profile": "👤 <b>Ваш профиль:</b>\n\n"
                   "🆔 <b>Ваш ID:</b> <code>{user_id}</code>\n"
                   "🧸 <b>Баланс:</b> <b>{balance}</b> ⭐\n"
                   "👥 <b>Приглашено друзей:</b> <b>{referrals_count}</b>",
        "earn": "💸 <b>Как заработать звёзды?</b>\n\n"
                "<blockquote>Здесь собраны все способы получения ⭐. Выберите тот, что вам по душе, и начните зарабатывать!</blockquote>",
        "invite": "🤝 <b>Пригласить друзей</b>\n\n"
                  "Приглашайте друзей и получайте <b>{ref_bonus}</b> ⭐ за каждого, кто присоединится по вашей ссылке и подпишется на каналы!\n\n"
                  "🔗 <i>Ваша реферальная ссылка доступна по кнопке ниже:</i>\n\n"
                  "🔗 <i>Ваша ссылка для копирования:</i>\n{ref_link}",
        "tasks_hub": "📝 <b>Выполнение заданий</b>\n\n"
                     "<blockquote>Подписывайтесь на каналы, предложенные ниже, и получайте награду. Если задание не интересно, просто пропустите его.</blockquote>",
        "task_instruction": "<blockquote>Подпишитесь на канал, а затем вернитесь в бота и нажмите «Подтвердить», чтобы забрать награду.</blockquote>\n\n",
        "task_reward": "💰 <b>Награда:</b> +{task_reward}⭐",
        "no_tasks": "🎉 <b>Все задания выполнены!</b>\n\nВы справились со всеми доступными заданиями. Заглядывайте позже, скоро появятся новые!",
        "withdraw_type_title": "🎁 <b>Вывод средств</b>\n\nПожалуйста, выберите тип вывода:",
        "withdraw": "Обменяйте ваши звёзды на подарки или манаты! Выберите один из вариантов ниже.\n\n"
                    "<i>ℹ️ Для вывода необходимо пригласить минимум {min_refs} друзей. У вас: {user_refs}</i>\n\n"
                    "Ваш баланс: <b>{balance}</b> ⭐",
        "bonus": "🎉 <b>Ежедневный бонус</b>\n\n"
                 "<blockquote>Вы можете получить случайный бонус один раз в 24 часа! Нажмите на кнопку, чтобы испытать удачу.</blockquote>",
        "bonus_claimed": "🎉 Поздравляем! Вы получили {bonus_amount} ⭐!",
        "bonus_wait": "😔 Следующий бонус через {hours} ч. {minutes} мин.",
        "promo": "🎟️ <b>Активация промокода</b>\n\n"
                 "<blockquote>Если у вас есть промокод, введите его в поле для ввода, чтобы получить приятный бонус!</blockquote>",
        "promo_success": "✅ Промокод активирован! Вам начислено {reward} ⭐.",
        "promo_fail_used": "🚫 Вы уже использовали этот промокод.",
        "promo_fail_general": "❌ Промокод не существует или истек.",
        "top": "🏆 <b>Топ пользователей</b>\n\n<blockquote>Кто здесь самый активный? Узнайте лидеров по звёздам и приглашениям.</blockquote>",
        "top_balance_title": "🏆 <b>Топ-10 по звёздам:</b>\n\n",
        "top_referrals_title": "👥 <b>Топ-10 по приглашениям:</b>\n\n",
        "top_no_users": "<i>Никого нет.</i>",
        "enter_payment_details": "📋 <b>Введите реквизиты</b>\n\n"
                                 "<blockquote>Отправьте номер телефона для получения выплаты.\n\n"
                                 "<i>Пример:</i> <code>65123456</code></blockquote>\n"
                                 "Вы сможете отменить операцию в любой момент.",
        "request_submitted_for_review": "✅ Твоя заявка <code>#{request_uid}</code> отправлена на рассмотрение. Ожидай одобрения от администратора в течении нескольких дней.",
        "lang_select": "🌐 Пожалуйста, выберите язык:",
        "lang_changed": "✅ Язык успешно изменен на Русский.",
        # Buttons
        "btn_earn": "💸 Заработать звёзды", "btn_withdraw": "🎁 Вывод средств", "btn_profile": "👤 Профиль",
        "btn_bonus": "🎉 Ежедневный бонус", "btn_promo": "🎟️ Промокод", "btn_top": "🏆 Топ",
        "btn_invite": "🤝 Пригласить друзей", "btn_tasks": "📝 Задания", "btn_back": "⬅️ Назад",
        "btn_back_to_menu": "⬅️ Вернуться в меню", "btn_share": "📲 Поделиться",
        "btn_cancel": "❌ Отмена",
        "btn_top_balance": "🏆 Топ по звёздам", "btn_top_referrals": "👥 Топ по рефералам",
        "btn_withdraw_rub": "TMT🇹🇲 Денги", "btn_withdraw_gift": "🎁 Подарки",
        "btn_change_lang": "🌐 Сменить язык", "btn_lang_ru": "Русский 🇷🇺", "btn_lang_tr": "Türkmen 🇹🇲",
        "btn_lang_uz": "Узбекский 🇺🇿",
        "btn_task_perform": "➡️ Выполнить", "btn_task_confirm": "✅ Подтвердить", "btn_task_skip": "⏩ Пропустить",
        "btn_check_status": "💸 Канал выплат",
        # Subscription check
        "sub_check_fail": "❗️ <b>Для использования бота необходимо подписаться на каналы:</b>",
        "sub_check_button": "✅ Я подписался",
        "sub_check_success": "✅ Спасибо за подписку!",
        "sub_check_not_yet": "❗️ Вы еще не подписались на все каналы.",
        "referral_notification": "🎉 По вашей ссылке присоединился новый пользователь: {new_user_display}!\nВам начислено <b>{ref_bonus}</b> ⭐.",
        # Alerts
        "alert_action_canceled": "Действие отменено",
        "alert_task_skipped": "⏭️ Задание пропущено",
        "alert_task_already_done": "✅ Вы уже выполнили это задание!",
        "alert_task_not_found": "❌ Задание больше не актуально.",
        "alert_not_subscribed": "❗️ Вы еще не подписались на канал «{task_name}». Попробуйте снова.",
        "alert_sub_check_failed": "❌ Не удалось проверить подписку.",
        "alert_need_more_refs": "❗️ Для вывода нужно пригласить ещё {diff} друзей.",
        "alert_pending_withdrawal": "❗️ У вас уже есть заявка на рассмотрении.",
        "alert_insufficient_stars": "😔 У вас недостаточно звёзд.",
        "alert_request_sent": "✅ Ваш запрос отправлен.",
        "status_pending": "⏳ Ваша заявка (#{uid}) всё ещё на рассмотрении. Пожалуйста, ожидайте.",
        "status_approved": "✅ Ваша заявка (#{uid}) одобрена! Списано {amount} ⭐ за «{gift_name}».",
        "status_declined": "❌ Ваша заявка (#{uid}) отклонена.\n\nПричина: {reason}",
        "status_not_found": "🤷‍♀️ Заявка с номером #{uid} не найдена.",
    },
    'tr': {
        "start": "👋 <b>Salam, {user_name}!</b>\n\n"
                 "Turkmen Stars botuna hoş geldiňiz! ✨\n\n"
                 "<blockquote>Bu ýerde ÿumuşlary ýerine ýetirip, dostlaryňyzy çagyryp ýyldyz gazanyp bilersiňiz. "
                 "Bu ýyldyzlary sowgatlara ýa-da hakyky pula öwrüp bilersiňiz. 🎁</blockquote>\n"
                 "🧸 Balansyňyz: <b>{balance}</b> ⭐",
        "profile": "👤 <b>Profiliňiz:</b>\n\n"
                   "🆔 <b>ID-iňiz:</b> <code>{user_id}</code>\n"
                   "🧸 <b>Balans:</b> <b>{balance}</b> ⭐\n"
                   "👥 <b>Çagyrylan dostlar:</b> <b>{referrals_count}</b>",
        "earn": "💸 <b>Nädip ýyldyz gazanmaly?</b>\n\n"
                "<blockquote>⭐ gazanmagyň ähli ýollary bu ýerde ýygnan. Size laýyk bolanyny saýlaň we gazanmaga başlaň!</blockquote>",
        "invite": "🤝 <b>Dost çagyrmak</b>\n\n"
                  "Dostlaryňyzy çagyryň we siziň baglanyşygyňyz bilen goşulyp, kanallara agza bolan her bir adam üçin <b>{ref_bonus}</b> ⭐ gazanyň!\n\n"
                  "🔗 <i>Çagyryş baglanyşygyňyz aşakdaky düwmä basyň.</i>\n\n"
                  "🔗 Göçürmek üçin baglanyşygyňyz:\n{ref_link}",
        "tasks_hub": "📝 <b>ýumuşleri ýerine ýetirmek</b>\n\n"
                     "<blockquote>Aşakda teklip edilýän kanallara agza boluň we baýragyňyzy alyň. ýumuş sizi gyzyklandyrmasa, geçiň.</blockquote>",
        "task_instruction": "<blockquote>Baýragy almak üçin kanala agza boluň, soňra bota gaýdyp gelip we «Tassyklat» düwmesine basyň.</blockquote>\n\n",
        "task_reward": "💰 <b>Baýrak:</b> +{task_reward}⭐",
        "no_tasks": "🎉 <b>Ähli ýumuşler tamamlandy!</b>\n\nÄhli elýeterli ýumuşleri ýerine ýetirdiňiz. Soňra ýene barlaň, ýakyn wagtda täzeleri goşular!",
        "withdraw_type_title": "🎁 <b>çykarmak</b>\n\nçykarma görnüşini saýlaň:",
        "withdraw": "Ýyldyzlaryňyzy sowgatlara ýa-da pula öwrüň! Aşakdaky saýlawlardan birini saýlaň.\n\n"
                    "<i>ℹ️ Pul çykarmak üçin iň az {min_refs} dost çagyrmaly. Siziň çagyryş sanyňyz: {user_refs}</i>\n\n"
                    "Balansyňyz: <b>{balance}</b> ⭐",
        "bonus": "🎉 <b>Günlük Bonus</b>\n\n"
                 "<blockquote>Her 24 sagatda bonus alyp bilersiňiz! Şansyňyzy synap görmek üçin düwmä basyň.</blockquote>",
        "bonus_claimed": "🎉 Gutly bolsun! {bonus_amount} ⭐ gazandyňyz!",
        "bonus_wait": "😔 Indiki bonus üçin {hours} sagat {minutes} minut soň ýene synap görüň.",
        "promo": "🎟️ <b>Promokod Aktiwleşdirmek</b>\n\n"
                 "<blockquote>Eger promokodyňyz bar bolsa, gowy bonus almak üçin giriş meýdançasyna ýazyň!</blockquote>",
        "promo_success": "✅ Promokod aktiwleşdirildi! Hasabyňyza {reward} ⭐ goşuldy.",
        "promo_fail_used": "🚫 Bu promokody eýýäm ulandyňyz.",
        "promo_fail_general": "❌ Promokod ýok ýa-da möhleti gutardy.",
        "top": "🏆 <b>Iň Gowy Ulanyjylar</b>\n\n<blockquote>Bu ýerde iň işjeň kim? Ýyldyz we çagyryş liderlerini öwreniň.</blockquote>",
        "top_balance_title": "🏆 <b>Ýyldyz Boýunça Iň Görnükli:</b>\n\n",
        "top_referrals_title": "👥 <b>Çagyryş Boýunça Iň Görnükli:</b>\n\n",
        "top_no_users": "<i>Hiç kim ýok.</i>",
        "enter_payment_details": "📋 <b>Töleg maglumatlaryňyzy giriziň</b>\n\n"
                                 "<blockquote>Töleg almak üçin telefon nomeriňizi iberiň.\n\n"
                                 "<i>Meselem:</i> <code>65123456</code></blockquote>\n"
                                 "Işlemi islendik wagt ýatyryp bilersiňiz.",
        "request_submitted_for_review": "✅ Talabyňyz <code>#{request_uid}</code> barlag üçin iberildi. Dolandyryjynyň birnäçe gün içinde tassyklamagyny garaşyň.",
        "lang_select": "🌐 dil saýlaň:",
        "lang_changed": "✅ Dil üstünlikli Türkmen diline çalşyldy.",
        # Buttons
        "btn_earn": "💸 Ýyldyz Gazan", "btn_withdraw": "🎁 Çykar", "btn_profile": "👤 Profil",
        "btn_bonus": "🎉 Günlük Bonus", "btn_promo": "🎟️ Promokod", "btn_top": "🏆 TOP",
        "btn_invite": "🤝 Dost Çagyrmak", "btn_tasks": "📝 ýumuşlar", "btn_back": "⬅️ Yzyna",
        "btn_back_to_menu": "⬅️ Menýu gaýdyp gel", "btn_share": "📲 Paýlaş",
        "btn_cancel": "❌ Ýatyrmak",
        "btn_top_balance": "🏆 Ýyldyz TOP", "btn_top_referrals": "👥 Çagyryş TOP",
        "btn_withdraw_rub": "TMT🇹🇲 Pul", "btn_withdraw_gift": "🎁 Sowgatlar",
        "btn_change_lang": "🌐 Dili Çalyş", "btn_lang_ru": "Русский 🇷🇺", "btn_lang_tr": "Türkmençe 🇹🇲",
        "btn_lang_uz": "Özbekçе 🇺🇿",
        "btn_task_perform": "➡️ Et", "btn_task_confirm": "✅ Tassyklat", "btn_task_skip": "⏩ Geç",
        "btn_check_status": "💸 Töleg Kanaly",
        # Subscription check
        "sub_check_fail": "❗️ <b>Boty ulanmak üçin kanallara agza bolmaly:</b>",
        "sub_check_button": "✅ Agza boldum",
        "sub_check_success": "✅ Agza bolanyňyz üçin sag boluň!",
        "sub_check_not_yet": "❗️ Heniz ähli kanallara agza bolmadyňyz.",
        "referral_notification": "🎉 Siziň baglanyşygyňyz bilen täze ulanyjy goşuldy: {new_user_display}!\nHasabyňyza <b>{ref_bonus}</b> ⭐ goşuldy.",
        # Alerts
        "alert_action_canceled": "Iş ýatyryldy",
        "alert_task_skipped": "⏭️ ýumuş geçildi",
        "alert_task_already_done": "✅ Bu ýumuşi eýýäm ýerine ýetirdiňiz!",
        "alert_task_not_found": "❌ ýumuş ýapyldy",
        "alert_not_subscribed": "❗️ «{task_name}» kanalyna henüz agza bolmadyňyz. Ýene synap görüň.",
        "alert_sub_check_failed": "❌ Agzalyk barlanylmady.",
        "alert_need_more_refs": "❗️ Pul çykarmak üçin {diff} dost çagyrmaly.",
        "alert_pending_withdrawal": "❗️ Eýýäm garaşylýan pul çykarma talabyňyz bar.",
        "alert_insufficient_stars": "😔 Ýeterlik ýyldyzyňyz ýok.",
        "alert_request_sent": "✅ Talabyňyz iberildi.",
        "status_pending": "⏳ Talabyňyz (#{uid}) henüz barlanýar. Garaşyň.",
        "status_approved": "✅ Talabyňyz (#{uid}) tassyklandy! {gift_name} üçin {amount} ⭐ aýryldy.",
        "status_declined": "❌ Talabyňyz (#{uid}) ret edildi.\n\nSebäp: {reason}",
        "status_not_found": "🤷‍♀️ #{uid} nomerli talap tapylmady.",
    },
    'uz': {
        "start": "👋 <b>Salom, {user_name}!</b>\n\n"
                 "Turkmen Stars botiga xush kelibsiz! ✨\n\n"
                 "<blockquote>Bu yerda siz vazifalarni bajarib, doʻstlaringizni taklif qilib yulduzlar topishingiz mumkin. "
                 "Bu yulduzlarni sovgʻalarga yoki haqiqiy pulga almashtirishingiz mumkin. 🎁</blockquote>\n"
                 "🧸 Sizning balansingiz: <b>{balance}</b> ⭐",
        "profile": "👤 <b>Sizning profilingiz:</b>\n\n"
                   "🆔 <b>Sizning ID:</b> <code>{user_id}</code>\n"
                   "🧸 <b>Balans:</b> <b>{balance}</b> ⭐\n"
                   "👥 <b>Taklif qilingan doʻstlar:</b> <b>{referrals_count}</b>",
        "earn": "💸 <b>Qanday qilib yulduz ishlash mumkin?</b>\n\n"
                "<blockquote>⭐ ishlashning barcha usullari shu yerda toʻplangan. Oʻzingizga ma'qulini tanlang va ishlashni boshlang!</blockquote>",
        "invite": "🤝 <b>Doʻstlarni taklif qilish</b>\n\n"
                  "Doʻstlaringizni taklif qiling va sizning havolangiz orqali qoʻshilib, kanallarga obuna boʻlgan har bir kishi uchun <b>{ref_bonus}</b> ⭐ oling!\n\n"
                  "🔗 <i>Sizning taklif havolangiz quyidagi tugmada mavjud.</i>\n\n"
                  "🔗 Nusxalash uchun havolangiz:\n{ref_link}",
        "tasks_hub": "📝 <b>Vazifalarni bajarish</b>\n\n"
                     "<blockquote>Quyida taklif etilgan kanallara obuna boʻling va mukofotingizni oling. Agar vazifa sizni qiziqtirmasa, oʻtkazib yuboring.</blockquote>",
        "task_instruction": "<blockquote>Mukofotni olish uchun kanalga obuna boʻling, soʻngra botga qaytib, «Tasdiqlash» tugmasini bosing.</blockquote>\n\n",
        "task_reward": "💰 <b>Mukofot:</b> +{task_reward}⭐",
        "no_tasks": "🎉 <b>Barcha vazifalar bajarildi!</b>\n\nSiz barcha mavjud vazifalarni bajardingiz. Keyinroq yana tekshiring, yaqinda yangilari qoʻshiladi!",
        "withdraw_type_title": "🎁 <b>Mablagʻni yechib olish</b>\n\nIltimos, yechib olish turini tanlang:",
        "withdraw": "Yulduzlaringizni sovgʻalarga yoki pulga almashtiring! Quyidagi variantlardan birini tanlang.\n\n"
                    "<i>ℹ️ Pul yechib olish uchun kamida {min_refs} doʻst taklif qilishingiz kerak. Sizning takliflaringiz soni: {user_refs}</i>\n\n"
                    "Sizning balansingiz: <b>{balance}</b> ⭐",
        "bonus": "🎉 <b>Kundalik bonus</b>\n\n"
                 "<blockquote>Har 24 soatda siz tasodifiy bonus olishingiz mumkin! Omadni sinab koʻrish uchun tugmani bosing.</blockquote>",
        "bonus_claimed": "🎉 Tabriklaymiz! Siz {bonus_amount} ⭐ yutib oldingiz!",
        "bonus_wait": "😔 Keyingi bonus uchun {hours} soat {minutes} daqiqadan soʻng qayta urinib koʻring.",
        "promo": "🎟️ <b>Promokodni faollashtirish</b>\n\n"
                 "<blockquote>Agar sizda promokod boʻlsa, yoqimli bonus olish uchun uni kiritish maydoniga yozing!</blockquote>",
        "promo_success": "✅ Promokod faollashtirildi! Hisobingizga {reward} ⭐ qoʻshildi.",
        "promo_fail_used": "🚫 Siz bu promokodni allaqachon ishlatgansiz.",
        "promo_fail_general": "❌ Promokod mavjud emas yoki muddati tugagan.",
        "top": "🏆 <b>Eng Yaxshi Foydalanuvchilar</b>\n\n<blockquote>Bu yerda kim eng faol? Yulduzlar ve takliflar boʻyicha liderlarni bilib oling.</blockquote>",
        "top_balance_title": "🏆 <b>Yulduzlar boʻyicha eng yaxshilar:</b>\n\n",
        "top_referrals_title": "👥 <b>Takliflar boʻyicha eng yaxshilar:</b>\n\n",
        "top_no_users": "<i>Hech kim yoʻq.</i>",
        "enter_payment_details": "📋 <b>Toʻlov ma'lumotlaringizni kiriting</b>\n\n"
                                 "<blockquote>Toʻlovni olish uchun телефон raqamingizni yuboring.\n\n"
                                 "<i>Masalan:</i> <code>65123456</code></blockquote>\n"
                                 "Operatsiyani istalgan vaqtda bekor qilishingiz mumkin.",
        "request_submitted_for_review": "✅ Sizning <code>#{request_uid}</code> raqamli arizangiz koʻrib chiqish uchun yuborildi. Administrator tomonidan bir necha kun ichida tasdiqlanishini kuting.",
        "lang_select": "🌐 Iltimos, tilni tanlang:",
        "lang_changed": "✅ Til muvaffaqiyatli oʻzbek tiliga oʻzgartirildi.",
        # Buttons
        "btn_earn": "💸 Yulduz Ishlash", "btn_withdraw": "🎁 Yechib olish", "btn_profile": "👤 Profil",
        "btn_bonus": "🎉 Kundalik Bonus", "btn_promo": "🎟️ Promokod", "btn_top": "🏆 TOP",
        "btn_invite": "🤝 Doʻst taklif qilish", "btn_tasks": "📝 Vazifalar", "btn_back": "⬅️ Orqaga",
        "btn_back_to_menu": "⬅️ Menyuga qaytish", "btn_share": "📲 Ulashish",
        "btn_cancel": "❌ Bekor qilish",
        "btn_top_balance": "🏆 Yulduz TOP", "btn_top_referrals": "👥 Takliflar TOP",
        "btn_withdraw_rub": "TMT🇹🇲 Pul", "btn_withdraw_gift": "🎁 Sovgʻalar",
        "btn_change_lang": "🌐 Tilni oʻzgartirish",
        "btn_lang_ru": "Русский 🇷🇺", "btn_lang_tr": "Türkmençe 🇹🇲", "btn_lang_uz": "Oʻzbekcha 🇺🇿",
        "btn_task_perform": "➡️ Bajarish", "btn_task_confirm": "✅ Tasdiqlash", "btn_task_skip": "⏩ Oʻtkazib yuborish",
        "btn_check_status": "💸 Toʻlovlar kanali",
        # Subscription check
        "sub_check_fail": "❗️ <b>Botdan foydalanish uchun kanallarga obuna boʻlishingiz kerak:</b>",
        "sub_check_button": "✅ Men obuna boʻldim",
        "sub_check_success": "✅ Obuna boʻlganingiz uchun rahmat!",
        "sub_check_not_yet": "❗️ Siz hali barcha kanallarga obuna boʻlmadingiz.",
        "referral_notification": "🎉 Sizning havolangiz orqali yangi foydalanuvchi qoʻshildi: {new_user_display}!\nHisobingizga <b>{ref_bonus}</b> ⭐ qoʻshildi.",
        # Alerts
        "alert_action_canceled": "Amal bekor qilindi",
        "alert_task_skipped": "⏭️ Vazifa oʻtkazib yuborildi",
        "alert_task_already_done": "✅ Siz bu vazifani allaqachon bajargansiz!",
        "alert_task_not_found": "❌ Vazifa endi dolzarb emas.",
        "alert_not_subscribed": "❗️ Siz «{task_name}» kanaliga hali obuna boʻlmagansiz. Qayta urinib koʻring.",
        "alert_sub_check_failed": "❌ Obunani tekshirish muvaffaqiyatsiz tugadi.",
        "alert_need_more_refs": "❗️ Pul yechib olish uchun yana {diff} doʻst taklif qilishingiz kerak.",
        "alert_pending_withdrawal": "❗️ Sizda allaqachon koʻrib chiqilayotgan ariza mavjud.",
        "alert_insufficient_stars": "😔 Sizda yetarli yulduz yoʻq.",
        "alert_request_sent": "✅ Sizning soʻrovingiz yuborildi.",
        "status_pending": "⏳ Sizning (#{uid}) raqamli arizangiz hali ham koʻrib chiqilmoqda. Iltimos, kuting.",
        "status_approved": "✅ Sizning (#{uid}) raqamli arizangiz tasdiqlandi! «{gift_name}» uchun {amount} ⭐ yechib olindi.",
        "status_declined": "❌ Sizning (#{uid}) raqamli arizangiz rad etildi.\n\nSabab: {reason}",
        "status_not_found": "🤷‍♀️ #{uid} raqamli ariza topilmadi.",
    }
}

# --- FSM (Durum Makinesi) ---
class UserStates(StatesGroup):
    viewing_task = State()
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
    add_task_name = State()
    add_task_channel_entry = State()
    add_task_private_link = State()
    add_task_reward = State()
    add_admin_id = State()
    balance_change_user_id = State()
    balance_change_amount = State()
    set_ref_bonus = State()
    upload_db = State()
    set_start_banner = State()

# --- PIARFLOW API CLIENT ---
class PiarFlowAPI:
    @staticmethod
    async def get_sponsors(user_id: int, chat_id: int, max_sponsors: int = 5) -> list:
        url = f"{PIARFLOW_API_URL}/sponsors"
        headers = {"Authorization": f"Bearer {PIARFLOW_API_KEY}", "Content-Type": "application/json"}
        payload = {"user_id": int(user_id), "chat_id": int(chat_id), "max_sponsors": max_sponsors}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "ok":
                            return data.get("sponsors", [])
        except Exception as e:
            logging.error(f"PiarFlow get_sponsors error: {e}")
        return []

    @staticmethod
    async def check_sponsors(user_id: int, links: list) -> list:
        url = f"{PIARFLOW_API_URL}/sponsors/check"
        headers = {"Authorization": f"Bearer {PIARFLOW_API_KEY}", "Content-Type": "application/json"}
        payload = {"user_id": int(user_id), "links": links}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "ok":
                            return data.get("sponsors", [])
        except Exception as e:
            logging.error(f"PiarFlow check_sponsors error: {e}")
        return []

    @staticmethod
    async def register_bot(chat_id: int, bot_token: str) -> dict:
        url = f"{PIARFLOW_API_URL}/traffic_bot/add"
        headers = {"Content-Type": "application/json"}
        payload = {"chat_id": int(chat_id), "bot_token": bot_token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    return await resp.json()
        except Exception as e:
            logging.error(f"PiarFlow register_bot error: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    async def get_bot_data() -> dict:
        url = f"{PIARFLOW_API_URL}/traffic_bot"
        headers = {"Authorization": f"Bearer {PIARFLOW_API_KEY}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    return await resp.json()
        except Exception as e:
            logging.error(f"PiarFlow get_bot_data error: {e}")
            return {"status": "error"}

    @staticmethod
    async def get_bot_stats(date_str: str) -> dict:
        url = f"{PIARFLOW_API_URL}/traffic_bot/stats?date={date_str}"
        headers = {"Authorization": f"Bearer {PIARFLOW_API_KEY}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    return await resp.json()
        except Exception as e:
            logging.error(f"PiarFlow get_bot_stats error: {e}")
            return {"status": "error"}

# --- VERİTABANI (SQLite) ---
class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
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
                    referral_processed BOOLEAN DEFAULT 0,
                    language TEXT DEFAULT 'ru'
                )''')
            try:
                self.cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ru'")
            except sqlite3.OperationalError:
                pass
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS used_promocodes (user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code))''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS completed_tasks (user_id INTEGER, task_id INTEGER, PRIMARY KEY (user_id, task_id))''')
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
                    details TEXT
                )''')
            try: self.cursor.execute("ALTER TABLE withdrawal_requests ADD COLUMN decline_reason TEXT")
            except sqlite3.OperationalError: pass
            try: self.cursor.execute("ALTER TABLE withdrawal_requests ADD COLUMN details TEXT")
            except sqlite3.OperationalError: pass
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, reward REAL, activations_left INTEGER)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, channel_url TEXT, channel_id TEXT, reward REAL, is_active BOOLEAN DEFAULT 1)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS required_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_name TEXT NOT NULL, channel_id TEXT NOT NULL UNIQUE, channel_url TEXT NOT NULL)''')
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, is_chief BOOLEAN DEFAULT 0)''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS sponsor_rewards (
                    user_id INTEGER,
                    offer_link TEXT,
                    reward REAL,
                    source TEXT,
                    PRIMARY KEY (user_id, offer_link)
                )''')
            self.set_setting_if_not_exists('ref_bonus', '1.5')
            self.set_setting_if_not_exists('daily_bonus_min', '0.1')
            self.set_setting_if_not_exists('daily_bonus_max', '0.2')

            if CHIEF_ADMIN_ID:
                self.cursor.execute("UPDATE admins SET is_chief = 0")
                self.cursor.execute("INSERT OR REPLACE INTO admins (user_id, is_chief) VALUES (?, 1)", (CHIEF_ADMIN_ID,))

    def record_sponsor_reward(self, user_id: int, offer_link: str, reward: float, source: str):
        with self.connection:
            self.cursor.execute(
                "INSERT OR REPLACE INTO sponsor_rewards (user_id, offer_link, reward, source) VALUES (?, ?, ?, ?)",
                (user_id, offer_link, reward, source)
            )

    def get_and_remove_sponsor_reward(self, user_id: int, offer_link: str) -> float:
        self.cursor.execute("SELECT reward FROM sponsor_rewards WHERE user_id = ? AND offer_link = ?", (user_id, offer_link))
        row = self.cursor.fetchone()
        if row:
            with self.connection:
                self.cursor.execute("DELETE FROM sponsor_rewards WHERE user_id = ? AND offer_link = ?", (user_id, offer_link))
            return float(row[0])
        return 0.0

    def get_user_language(self, user_id: int) -> str:
        self.cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result and result[0] else 'ru'

    def set_user_language(self, user_id: int, language: str):
        with self.connection:
            self.cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))

    def add_user(self, user: User, referrer_id=None, lang='ru'):
        with self.connection:
            self.cursor.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, referrer_id, language) VALUES (?, ?, ?, ?, ?)",
                (user.id, user.username, user.first_name, referrer_id, lang)
            )

    def update_user_info(self, user_id: int, username: str, first_name: str):
        with self.connection:
            self.cursor.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (username, first_name, user_id)
            )

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
            self.cursor.execute("INSERT INTO withdrawal_requests (uid, user_id, username, amount, gift_name, details) VALUES (?, ?, ?, ?, ?, ?)", (request_uid, user_id, username, amount, gift_name, details))
            return self.cursor.lastrowid, request_uid

    def get_withdrawal_request(self, request_id):
        self.cursor.execute("SELECT uid, user_id, username, amount, gift_name, status, decline_reason, details FROM withdrawal_requests WHERE id = ?", (request_id,))
        return self.cursor.fetchone()
    
    def get_withdrawal_request_by_uid(self, request_uid):
        self.cursor.execute("SELECT uid, user_id, username, amount, gift_name, status, decline_reason FROM withdrawal_requests WHERE uid = ?", (request_uid,))
        return self.cursor.fetchone()

    def update_withdrawal_status(self, request_id, status, reason=None):
        with self.connection: self.cursor.execute("UPDATE withdrawal_requests SET status = ?, decline_reason = ? WHERE id = ?", (status, reason, request_id))

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

    def update_balance(self, user_id, amount):
        with self.connection: self.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))

    def get_referrals_count(self, user_id):
        self.cursor.execute("SELECT COUNT(user_id) FROM users WHERE referrer_id = ? AND referral_processed = 1", (user_id,))
        return self.cursor.fetchone()[0]

    def get_last_bonus_time(self, user_id):
        self.cursor.execute("SELECT last_bonus_time FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return datetime.fromisoformat(result[0]) if result and result[0] else None

    def update_last_bonus_time(self, user_id):
        with self.connection: self.cursor.execute("UPDATE users SET last_bonus_time = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))

    def get_top_by_balance(self, limit=10):
        self.cursor.execute("SELECT user_id, balance, username, first_name FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_top_by_referrals(self, limit=10):
        self.cursor.execute("""
            SELECT u.referrer_id, COUNT(u.user_id) as ref_count, ref.username, ref.first_name
            FROM users u
            JOIN users ref ON u.referrer_id = ref.user_id
            WHERE u.referrer_id IS NOT NULL AND u.referral_processed = 1
            GROUP BY u.referrer_id
            ORDER BY ref_count DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()

    def get_all_user_ids(self):
        self.cursor.execute("SELECT user_id FROM users"); return [row[0] for row in self.cursor.fetchall()]

    def get_stats(self):
        self.cursor.execute("SELECT COUNT(user_id) FROM users"); total_users = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(user_id) FROM users WHERE join_date >= date('now', '-24 hours')"); new_users_24h = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT SUM(balance) FROM users"); total_balance = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(id) FROM tasks WHERE is_active = 1"); active_tasks = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM completed_tasks"); completed_tasks = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT status, COUNT(*) FROM withdrawal_requests GROUP BY status")
        withdraw_counts = {s: c for s, c in self.cursor.fetchall()}
        self.cursor.execute("SELECT SUM(amount) FROM withdrawal_requests WHERE status = 'approved'")
        withdrawn_sum = self.cursor.fetchone()[0]
        return {"total_users": total_users, "new_users_24h": new_users_24h, "total_balance": round(total_balance or 0, 2), "active_tasks": active_tasks, "completed_tasks": completed_tasks, "withdraw_pending": withdraw_counts.get('pending', 0), "withdraw_approved": withdraw_counts.get('approved', 0), "withdraw_declined": withdraw_counts.get('declined', 0), "withdrawn_sum": round(withdrawn_sum or 0, 2)}

    def create_promocode(self, code, reward, activations):
        with self.connection: self.cursor.execute("INSERT OR REPLACE INTO promocodes (code, reward, activations_left) VALUES (?, ?, ?)", (code, reward, activations))

    def get_promocode(self, code):
        self.cursor.execute("SELECT reward, activations_left FROM promocodes WHERE code = ?", (code,)); return self.cursor.fetchone()

    def use_promocode(self, user_id, code):
        with self.connection:
            self.cursor.execute("UPDATE promocodes SET activations_left = activations_left - 1 WHERE code = ?", (code,))
            self.cursor.execute("INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)", (user_id, code))

    def has_user_used_promo(self, user_id, code):
        self.cursor.execute("SELECT 1 FROM used_promocodes WHERE user_id = ? AND code = ?", (user_id, code)); return self.cursor.fetchone() is not None

    def get_all_promocodes(self):
        self.cursor.execute("SELECT code, reward, activations_left FROM promocodes ORDER BY code")
        return self.cursor.fetchall()

    def delete_promocode(self, code):
        with self.connection: self.cursor.execute("DELETE FROM promocodes WHERE code = ?", (code,))

    def add_task(self, name, url, channel_id, reward):
        with self.connection:
            self.cursor.execute("INSERT INTO tasks (name, channel_url, channel_id, reward) VALUES (?, ?, ?, ?)", (name, url, channel_id, reward))
            return self.cursor.lastrowid

    def get_all_tasks(self):
        self.cursor.execute("SELECT id, name, reward, channel_id FROM tasks WHERE is_active = 1 ORDER BY id")
        return self.cursor.fetchall()

    def get_task(self, task_id):
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return self.cursor.fetchone()

    def delete_task(self, task_id):
         with self.connection: self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_next_available_task(self, user_id, skipped_ids=None):
        if skipped_ids is None: skipped_ids = []
        placeholders = ','.join('?' for _ in skipped_ids)
        query = f"SELECT id, channel_url, channel_id, reward FROM tasks WHERE is_active = 1 AND id NOT IN (SELECT task_id FROM completed_tasks WHERE user_id = ?) AND id NOT IN ({placeholders}) ORDER BY id LIMIT 1"
        params = [user_id] + skipped_ids
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def is_task_completed(self, user_id, task_id):
        self.cursor.execute("SELECT 1 FROM completed_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        return self.cursor.fetchone() is not None

    def complete_task(self, user_id, task_id):
        with self.connection: self.cursor.execute("INSERT OR IGNORE INTO completed_tasks (user_id, task_id) VALUES (?, ?)", (user_id, task_id))


db = Database(DB_FILE)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- YÖNETİCİ FİLTRELERİ ---
class IsAdmin(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        return db.is_admin(event.from_user.id)

class IsChiefAdmin(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        return db.is_chief_admin(event.from_user.id)

# --- DİL YARDIMCISI ---
def get_text(key: str, lang: str):
    return LANG_TEXTS.get(lang, LANG_TEXTS['ru']).get(key, f"_{key}_")

# --- ABONELİK KONTROLÜ (LOCAL + TGRASS + PIARFLOW) ---
async def run_full_subscription_check(user: User, bot: Bot) -> tuple[bool, list]:
    not_subscribed_channels = []
    is_fully_subscribed = True
    user_id = user.id

    # 1. Local Database Channels
    local_channels = db.get_required_channels()
    if local_channels:
        for _, name, channel_id, url in local_channels:
            try:
                member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status not in ["creator", "administrator", "member"]:
                    is_fully_subscribed = False
                    not_subscribed_channels.append({'name': name, 'url': url})
            except TelegramAPIError as e:
                logging.error(f"Error checking local sub for {channel_id} (user: {user_id}): {e}.")
                is_fully_subscribed = False
                not_subscribed_channels.append({'name': name, 'url': url})

    # 2. TGrass Offers
    try:
        url = "https://tgrass.space/offers"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Auth": TGRASS_API_KEY,
        }
        payload = {
            "tg_user_id": int(user.id),
            "tg_login": user.username or "",
            "lang": user.language_code or "en",
            "is_premium": user.is_premium or False,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    resp_json = await response.json()
                    if resp_json.get("status") == "not_ok":
                         is_fully_subscribed = False
                         for offer in resp_json.get("offers", []):
                             not_subscribed_channels.append({
                                 'name': f"{offer.get('title', 'Спонсор')}",
                                 'url': offer['link']
                             })
    except Exception as e:
        logging.error(f"TGrass check error: {e}")

    # 3. PiarFlow Sponsors
    try:
        piarflow_sponsors = await PiarFlowAPI.get_sponsors(user_id=user.id, chat_id=user.id, max_sponsors=5)
        for sp in piarflow_sponsors:
            if sp.get("status") == "unsubscribed":
                is_fully_subscribed = False
                not_subscribed_channels.append({
                    'name': "Спонсор",
                    'url': sp.get("link")
                })
    except Exception as e:
        logging.error(f"PiarFlow check error: {e}")

    return is_fully_subscribed, not_subscribed_channels

# --- ARA YAZILIMLAR (Dil ve Abonelik) ---
class MasterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get('event_from_user')
        if not user:
            return await handler(event, data)

        db.update_user_info(user.id, user.username, user.first_name)
        user_lang = db.get_user_language(user.id)
        data['user_lang'] = user_lang

        if db.is_admin(user.id):
            return await handler(event, data)

        if (isinstance(event, types.Message) and event.text and event.text.startswith('/start')) or \
           (isinstance(event, types.CallbackQuery) and event.data in ["check_subscription"]):
            return await handler(event, data)

        is_subscribed, not_subscribed_list = await run_full_subscription_check(user, data['bot'])
        
        if not is_subscribed:
            text = get_text('sub_check_fail', user_lang)
            builder = InlineKeyboardBuilder()
            for channel in not_subscribed_list:
                builder.button(text=f" {channel['name']}", url=channel['url'])
            builder.adjust(2)
            builder.row(InlineKeyboardButton(text=get_text('sub_check_button', user_lang), callback_data="check_subscription"))

            if isinstance(event, types.Message):
                await event.answer(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)
            elif isinstance(event, types.CallbackQuery):
                try:
                    await event.answer()
                except TelegramAPIError:
                    pass
                await event.message.answer(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)
            return

        return await handler(event, data)

# --- KLAVYELER ---
def get_main_menu_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_earn', lang), callback_data="earn")
    builder.button(text=get_text('btn_withdraw', lang), callback_data="withdraw")
    builder.button(text=get_text('btn_profile', lang), callback_data="profile")
    builder.button(text=get_text('btn_bonus', lang), callback_data="bonus")
    builder.button(text=get_text('btn_promo', lang), callback_data="promo")
    builder.button(text=get_text('btn_top', lang), callback_data="top")
    builder.adjust(1, 2, 2, 1)
    return builder.as_markup()

def get_profile_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_change_lang', lang), callback_data="change_lang")
    builder.button(text=get_text('btn_back_to_menu', lang), callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_lang_select_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_lang_ru', lang), callback_data="set_lang_ru")
    builder.button(text=get_text('btn_lang_tr', lang), callback_data="set_lang_tr")
    builder.button(text=get_text('btn_lang_uz', lang), callback_data="set_lang_uz")
    builder.button(text=get_text('btn_back', lang), callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()

def get_withdraw_type_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_withdraw_rub', lang), callback_data="withdraw_type_rub")
    builder.button(text=get_text('btn_withdraw_gift', lang), callback_data="withdraw_type_gift")
    builder.button(text=get_text('btn_back_to_menu', lang), callback_data="main_menu")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_withdraw_gift_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="🧸 (15⭐)", callback_data="withdraw_gift_15_🧸")
    builder.button(text="💝 (15⭐)", callback_data="withdraw_gift_15_💝")
    builder.button(text="🎁 (25⭐)", callback_data="withdraw_gift_25_🎁")
    builder.button(text="🌹 (25⭐)", callback_data="withdraw_gift_25_🌹")
    builder.button(text="🎂 (50⭐)", callback_data="withdraw_gift_50_🎂")
    builder.button(text="💐 (50⭐)", callback_data="withdraw_gift_50_💐")
    builder.button(text="🚀 (50⭐)", callback_data="withdraw_gift_50_🚀")
    builder.button(text="🍾 (50⭐)", callback_data="withdraw_gift_50_🍾")
    builder.button(text="🏆 (100⭐)", callback_data="withdraw_gift_100_🏆")
    builder.button(text="💍 (100⭐)", callback_data="withdraw_gift_100_💍")
    builder.button(text="💎 (100⭐)", callback_data="withdraw_gift_100_💎")
    builder.button(text=get_text('btn_back', lang), callback_data="main_menu")
    builder.adjust(2, 2, 2, 2, 3, 1)
    return builder.as_markup()

def get_earn_menu_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_invite', lang), callback_data="invite_friends")
    builder.button(text=get_text('btn_tasks', lang), callback_data="tasks")
    builder.button(text=get_text('btn_back', lang), callback_data="main_menu")
    builder.adjust(1); return builder.as_markup()

def get_invite_kb(lang: str, ref_link: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_share', lang), switch_inline_query=ref_link.replace("`", ""))
    builder.button(text=get_text('btn_back', lang), callback_data="earn")
    builder.adjust(1); return builder.as_markup()

def get_task_viewer_kb(lang: str, task_id: str, task_url: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_task_perform', lang), url=task_url)
    builder.button(text=get_text('btn_task_confirm', lang), callback_data=f"task_confirm_{task_id}")
    builder.button(text=get_text('btn_task_skip', lang), callback_data="task_skip")
    builder.button(text=get_text('btn_back', lang), callback_data="earn")
    builder.adjust(2, 1, 1); return builder.as_markup()

def get_back_kb(lang: str, callback_data="main_menu"):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_back', lang), callback_data=callback_data)
    return builder.as_markup()

def get_cancel_kb(lang: str, callback_data="cancel_action"):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_cancel', lang), callback_data=callback_data)
    return builder.as_markup()

def get_top_menu_kb(lang: str):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text('btn_top_balance', lang), callback_data="top_balance")
    builder.button(text=get_text('btn_top_referrals', lang), callback_data="top_referrals")
    builder.button(text=get_text('btn_back', lang), callback_data="main_menu")
    builder.adjust(2, 1); return builder.as_markup()

def get_withdraw_submitted_kb(lang: str):
    builder = InlineKeyboardBuilder()
    if PAYMENTS_CHANNEL_LINK and "YourPaymentsChannel" not in PAYMENTS_CHANNEL_LINK:
        builder.button(text=get_text('btn_check_status', lang), url=PAYMENTS_CHANNEL_LINK)
    builder.button(text=get_text('btn_back_to_menu', lang), callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_kb(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="⚙️ Настройки бонуса", callback_data="admin_bonus_settings")
    builder.button(text="📝 Задания", callback_data="admin_task_management")
    builder.button(text="🎟️ Промокоды", callback_data="admin_promo_menu")
    builder.button(text="🔗 Каналы подписки", callback_data="admin_req_subs")
    builder.button(text="💰 Изменить баланс", callback_data="admin_balance_change")
    builder.button(text="🤝 Реферальный бонус", callback_data="admin_ref_bonus")
    builder.button(text="🖼️ Баннер /start", callback_data="admin_start_banner")
    builder.button(text="📈 Статистика PiarFlow", callback_data="admin_piarflow_stats")
    builder.button(text="💾 Скачать БД", callback_data="admin_download_db")
    builder.button(text="📤 Установить БД", callback_data="admin_upload_db")
    if db.is_chief_admin(user_id):
        builder.button(text="👑 Админы", callback_data="admin_manage_admins")
    builder.adjust(2)
    return builder.as_markup()

def get_back_to_admin_panel_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в админ-панель", callback_data="admin_panel")
    return builder.as_markup()

def get_admin_withdraw_kb(request_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"withdraw_approve_{request_id}")
    builder.button(text="❌ Отклонить", callback_data=f"withdraw_decline_{request_id}")
    return builder.as_markup()

# --- YARDIMCI FONKSİYONLAR ---
async def edit_or_send_message(target, text, markup, **kwargs):
    try:
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=markup, **kwargs)
            return target.message
        else:
            return await target.answer(text, reply_markup=markup, **kwargs)
    except (TelegramBadRequest, TelegramAPIError) as e:
        if isinstance(target, CallbackQuery) and "message is not modified" in str(e):
             await target.answer()
             return target.message

        logging.warning(f"edit_or_send_message failed to edit: {e}. Trying to send new message.")
        try:
            chat_id = target.message.chat.id if isinstance(target, CallbackQuery) else target.chat.id
            if isinstance(target, CallbackQuery):
                try: await target.message.delete()
                except TelegramAPIError: pass
            return await bot.send_message(chat_id, text, reply_markup=markup, **kwargs)
        except Exception as e_send:
            logging.error(f"Failed to both edit and send message: {e_send}")
            return None

async def process_referral(new_user: User, bot: Bot):
    user_id = new_user.id
    ref_info = db.get_user_referral_info(user_id)
    if not ref_info: return
    referrer_id, referral_processed = ref_info
    if referrer_id and not referral_processed:
        referrer_lang = db.get_user_language(referrer_id)
        ref_bonus = float(db.get_setting('ref_bonus'))
        db.update_balance(referrer_id, ref_bonus)
        db.mark_referral_as_processed(user_id)
        new_user_display = db.get_user_display_name(user_id)
        notification_text = get_text('referral_notification', referrer_lang).format(new_user_display=new_user_display, ref_bonus=ref_bonus)
        try:
            await bot.send_message(referrer_id, notification_text)
        except TelegramAPIError as e:
            logging.warning(f"Could not send ref notification to {referrer_id}: {e}")

async def clean_prompt(state: FSMContext, chat_id: int, bot: Bot):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    if prompt_message_id:
        try: await bot.delete_message(chat_id, prompt_message_id)
        except TelegramAPIError: pass

# --- KULLANICI İŞLEYİCİLERİ ---
@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(call: CallbackQuery, bot: Bot, user_lang: str):
    user = call.from_user
    is_subscribed, _ = await run_full_subscription_check(user, bot)
    
    if is_subscribed:
        await call.answer(get_text('sub_check_success', user_lang), show_alert=True)
        try: await call.message.delete()
        except TelegramAPIError: pass
        await process_referral(user, bot)
        balance = db.get_user_balance(user.id)
        text = get_text('start', user_lang).format(user_name=html.bold(user.full_name), balance=round(balance, 2))
        
        banner = db.get_setting('start_banner')
        if banner:
            await call.message.answer_photo(photo=banner, caption=text, reply_markup=get_main_menu_kb(user_lang))
        else:
            await call.message.answer(text, reply_markup=get_main_menu_kb(user_lang))
    else:
        await call.answer(get_text('sub_check_not_yet', user_lang), show_alert=True)

@dp.message(CommandStart())
async def command_start(message: Message, bot: Bot, user_lang: str):
    user = message.from_user
    if not db.user_exists(user.id):
        referrer_id = None
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit() and int(args[1]) != user.id:
            referrer_id = int(args[1])
        db.add_user(user, referrer_id, user_lang)

    is_subscribed, not_subscribed_list = await run_full_subscription_check(user, bot)

    if is_subscribed:
        await process_referral(user, bot)
        balance = db.get_user_balance(user.id)
        text = get_text('start', user_lang).format(user_name=html.bold(user.full_name), balance=round(balance, 2))
        
        banner = db.get_setting('start_banner')
        if banner:
            await message.answer_photo(photo=banner, caption=text, reply_markup=get_main_menu_kb(user_lang))
        else:
            await message.answer(text, reply_markup=get_main_menu_kb(user_lang))
    else:
        builder = InlineKeyboardBuilder()
        text = get_text('sub_check_fail', user_lang)
        for channel in not_subscribed_list:
            builder.button(text=f" {channel['name']}", url=channel['url'])
        builder.adjust(2)
        builder.row(InlineKeyboardButton(text=get_text('sub_check_button', user_lang), callback_data="check_subscription"))
        await message.answer(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)

@dp.callback_query(F.data == "main_menu")
async def back_to_main_menu(call: CallbackQuery, state: FSMContext, user_lang: str):
    await state.clear()
    balance = db.get_user_balance(call.from_user.id)
    username = call.from_user.username or call.from_user.first_name
    text = get_text('start', user_lang).format(user_name=html.bold(username), balance=round(balance, 2))
    
    try: await call.message.delete()
    except TelegramAPIError: pass
    
    banner = db.get_setting('start_banner')
    if banner:
        await bot.send_photo(call.message.chat.id, photo=banner, caption=text, reply_markup=get_main_menu_kb(user_lang))
    else:
        await bot.send_message(call.message.chat.id, text, reply_markup=get_main_menu_kb(user_lang))
    await call.answer()

@dp.callback_query(F.data == "profile")
async def show_profile(call: CallbackQuery, user_lang: str):
    user_id = call.from_user.id
    balance = db.get_user_balance(user_id)
    referrals_count = db.get_referrals_count(user_id)
    text = get_text('profile', user_lang).format(user_id=user_id, balance=round(balance, 2), referrals_count=referrals_count)
    await edit_or_send_message(call, text, get_profile_kb(user_lang))
    await call.answer()

@dp.callback_query(F.data == "change_lang")
async def change_lang_menu(call: CallbackQuery, user_lang: str):
    await edit_or_send_message(call, get_text('lang_select', user_lang), get_lang_select_kb(user_lang))
    await call.answer()

@dp.callback_query(F.data.startswith("set_lang_"))
async def set_user_language_handler(call: CallbackQuery):
    new_lang = call.data.split('_')[-1]
    db.set_user_language(call.from_user.id, new_lang)
    await call.answer(get_text('lang_changed', new_lang), show_alert=True)
    await show_profile(call, new_lang)

@dp.callback_query(F.data == "earn")
async def show_earn_menu(call: CallbackQuery, state: FSMContext, user_lang: str):
    await state.clear()
    await edit_or_send_message(call, get_text('earn', user_lang), get_earn_menu_kb(user_lang))
    await call.answer()

@dp.callback_query(F.data == "invite_friends")
async def show_invite_menu(call: CallbackQuery, bot: Bot, user_lang: str):
    ref_bonus = float(db.get_setting('ref_bonus'))
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={call.from_user.id}"
    text = get_text('invite', user_lang).format(ref_bonus=ref_bonus, ref_link=ref_link)
    await edit_or_send_message(call, text, get_invite_kb(user_lang, ref_link))
    await call.answer()

@dp.callback_query(F.data == "tasks")
async def start_tasks(call: CallbackQuery, state: FSMContext, user_lang: str):
    await state.clear()
    await state.update_data(skipped_tasks=[], skipped_piarflow=[], skipped_tgrass=[])
    await show_next_task(call, state, user_lang)

# --- УНИВЕРСАЛЬНАЯ ПОДАЧА ЗАДАНИЙ (LOCAL -> PIARFLOW -> TGRASS) ---
async def show_next_task(call: CallbackQuery, state: FSMContext, user_lang: str):
    user_id = call.from_user.id
    state_data = await state.get_data()
    
    # 1. Сначала локальные задания SQLite
    skipped_ids = state_data.get('skipped_tasks', [])
    task = db.get_next_available_task(user_id, skipped_ids)
    if task:
        task_id, task_url, _, task_reward = task
        await state.set_state(UserStates.viewing_task)
        await state.update_data(current_task_type="local", current_task_id=str(task_id))
        text = get_text('task_instruction', user_lang) + get_text('task_reward', user_lang).format(task_reward=task_reward)
        await edit_or_send_message(call, text, get_task_viewer_kb(user_lang, f"local_{task_id}", task_url))
        await call.answer()
        return

    # 2. Задания от PiarFlow
    skipped_pf = state_data.get('skipped_piarflow', [])
    piarflow_sponsors = await PiarFlowAPI.get_sponsors(user_id=user_id, chat_id=user_id, max_sponsors=5)
    for idx, sp in enumerate(piarflow_sponsors):
        link = sp.get("link")
        if sp.get("status") == "unsubscribed" and link not in skipped_pf:
            reward = float(sp.get("price", 1.0))
            await state.set_state(UserStates.viewing_task)
            await state.update_data(current_task_type="piarflow", current_task_id=link, pf_reward=reward)
            text = get_text('task_instruction', user_lang) + get_text('task_reward', user_lang).format(task_reward=reward)
            await edit_or_send_message(call, text, get_task_viewer_kb(user_lang, f"pf_{idx}", link))
            await call.answer()
            return

    # 3. Задания от TGrass
    skipped_tg = state_data.get('skipped_tgrass', [])
    try:
        url = "https://tgrass.space/offers"
        headers = {"accept": "application/json", "Content-Type": "application/json", "Auth": TGRASS_API_KEY}
        payload = {"tg_user_id": int(user_id), "tg_login": call.from_user.username or "", "lang": call.from_user.language_code or "en", "is_premium": call.from_user.is_premium or False}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                if response.status == 200:
                    resp_json = await response.json()
                    if resp_json.get("status") == "not_ok":
                        for idx, offer in enumerate(resp_json.get("offers", [])):
                            link = offer.get("link")
                            if link not in skipped_tg:
                                reward = float(offer.get("price", 1.0))
                                await state.set_state(UserStates.viewing_task)
                                await state.update_data(current_task_type="tgrass", current_task_id=link, tg_reward=reward)
                                text = get_text('task_instruction', user_lang) + get_text('task_reward', user_lang).format(task_reward=reward)
                                await edit_or_send_message(call, text, get_task_viewer_kb(user_lang, f"tg_{idx}", link))
                                await call.answer()
                                return
    except Exception as e:
        logging.error(f"TGrass tasks check error: {e}")

    await state.clear()
    await edit_or_send_message(call, get_text('no_tasks', user_lang), get_back_kb(user_lang, "earn"))
    await call.answer()

@dp.callback_query(UserStates.viewing_task, F.data == "task_skip")
async def skip_task(call: CallbackQuery, state: FSMContext, user_lang: str):
    state_data = await state.get_data()
    task_type = state_data.get('current_task_type')
    current_id = state_data.get('current_task_id')
    if task_type == "local" and current_id:
        skipped = state_data.get('skipped_tasks', [])
        skipped.append(int(current_id))
        await state.update_data(skipped_tasks=skipped)
    elif task_type == "piarflow" and current_id:
        skipped = state_data.get('skipped_piarflow', [])
        skipped.append(current_id)
        await state.update_data(skipped_piarflow=skipped)
    elif task_type == "tgrass" and current_id:
        skipped = state_data.get('skipped_tgrass', [])
        skipped.append(current_id)
        await state.update_data(skipped_tgrass=skipped)
    await call.answer(get_text("alert_task_skipped", user_lang))
    await show_next_task(call, state, user_lang)

@dp.callback_query(UserStates.viewing_task, F.data.startswith("task_confirm_"))
async def confirm_task_subscription(call: CallbackQuery, bot: Bot, state: FSMContext, user_lang: str):
    user_id = call.from_user.id
    data_str = call.data.split("_", 2)
    t_type = data_str[1]
    
    if t_type == "local":
        task_id = int(data_str[2])
        if db.is_task_completed(user_id, task_id):
            await call.answer(get_text('alert_task_already_done', user_lang), show_alert=True)
            return
        task_data = db.get_task(task_id)
        if not task_data:
            await call.answer(get_text('alert_task_not_found', user_lang), show_alert=True)
            await show_next_task(call, state, user_lang)
            return
        _, task_name, _, channel_id_str, reward, _ = task_data
        try:
            chat_id_to_check = f"@{channel_id_str}" if not channel_id_str.lstrip('-').isdigit() else int(channel_id_str)
            member = await bot.get_chat_member(chat_id=chat_id_to_check, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                db.update_balance(user_id, reward)
                db.complete_task(user_id, task_id)
                await call.answer(f"🎉 +{reward} ⭐", show_alert=True)
                await show_next_task(call, state, user_lang)
            else:
                await call.answer(get_text('alert_not_subscribed', user_lang).format(task_name=task_name), show_alert=True)
        except TelegramAPIError as e:
            logging.error(f"Error checking subscription for channel {channel_id_str}: {e}")
            await call.answer(get_text('alert_sub_check_failed', user_lang), show_alert=True)

    elif t_type == "pf":
        state_data = await state.get_data()
        link = state_data.get("current_task_id")
        reward = state_data.get("pf_reward", 1.0)
        res = await PiarFlowAPI.check_sponsors(user_id=user_id, links=[link])
        subscribed = any(sp.get("status") == "subscribed" for sp in res)
        if subscribed:
            db.update_balance(user_id, reward)
            db.record_sponsor_reward(user_id, link, reward, "piarflow")
            await call.answer(f"🎉 +{reward} ⭐", show_alert=True)
            await show_next_task(call, state, user_lang)
        else:
            await call.answer("❗️ Вы еще не подписались на канал PiarFlow. Попробуйте снова.", show_alert=True)

    elif t_type == "tg":
        state_data = await state.get_data()
        link = state_data.get("current_task_id")
        reward = state_data.get("tg_reward", 1.0)
        db.update_balance(user_id, reward)
        db.record_sponsor_reward(user_id, link, reward, "tgrass")
        await call.answer(f"🎉 +{reward} ⭐", show_alert=True)
        await show_next_task(call, state, user_lang)

@dp.callback_query(F.data == "withdraw")
async def show_withdraw_menu(call: CallbackQuery, state: FSMContext, user_lang: str):
    await state.clear()
    user_id = call.from_user.id
    balance = db.get_user_balance(user_id)
    referrals = db.get_referrals_count(user_id)
    text = get_text('withdraw', user_lang).format(balance=round(balance, 2), min_refs=MIN_REFERRALS_FOR_WITHDRAWAL, user_refs=referrals)
    await edit_or_send_message(call, text, get_withdraw_gift_kb(user_lang))
    await call.answer()

@dp.callback_query(F.data.startswith("withdraw_gift_"))
async def request_withdraw(call: CallbackQuery, bot: Bot, state: FSMContext, user_lang: str):
    user_id = call.from_user.id
    referrals_count = db.get_referrals_count(user_id)
    if referrals_count < MIN_REFERRALS_FOR_WITHDRAWAL:
        diff = MIN_REFERRALS_FOR_WITHDRAWAL - referrals_count
        await call.answer(get_text('alert_need_more_refs', user_lang).format(diff=diff), show_alert=True)
        return
    if db.has_pending_withdrawal(user_id):
        await call.answer(get_text('alert_pending_withdrawal', user_lang), show_alert=True)
        return

    username = db.get_user_display_name(user_id)
    balance = db.get_user_balance(user_id)

    try:
        _, _, cost_str, gift_name = call.data.split("_", 3)
        cost = float(cost_str)
    except (ValueError, IndexError): 
        logging.error(f"Could not parse gift withdraw callback data: {call.data}")
        return
    
    if balance < cost: 
        await call.answer(get_text('alert_insufficient_stars', user_lang), show_alert=True)
        return

    request_id, request_uid = db.create_withdrawal_request(user_id, username, cost, gift_name)
    confirmation_text = get_text("request_submitted_for_review", user_lang).format(request_uid=request_uid)
    
    await edit_or_send_message(call, confirmation_text, get_withdraw_submitted_kb(user_lang))
    await call.answer()

    admin_text = (f"✨ Новая заявка (Подарок) #{request_uid} ✨\n\n"
                  f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                  f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Стоимость:</b> {cost} ⭐\n"
                  f"🕓 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try: 
        await bot.send_message(ADMIN_CHANNEL_ID, admin_text, reply_markup=get_admin_withdraw_kb(request_id))
    except TelegramAPIError as e: 
        logging.error(f"Could not send gift request to admin channel {ADMIN_CHANNEL_ID}: {e}")

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment_input(call: CallbackQuery, state: FSMContext, user_lang: str):
    await state.clear()
    await call.answer(get_text("alert_action_canceled", user_lang))
    await show_withdraw_menu(call, state, user_lang)

@dp.callback_query(F.data == "bonus")
async def claim_bonus(call: CallbackQuery, state: FSMContext, user_lang: str):
    user_id = call.from_user.id
    last_bonus_time = db.get_last_bonus_time(user_id)
    if last_bonus_time and datetime.now() - last_bonus_time < timedelta(hours=24):
        time_left = timedelta(hours=24) - (datetime.now() - last_bonus_time)
        hours, rem = divmod(time_left.seconds, 3600); minutes, _ = divmod(rem, 60)
        wait_text = get_text('bonus_wait', user_lang).format(hours=hours, minutes=minutes)
        await call.answer(wait_text, show_alert=True)
    else:
        min_b, max_b = float(db.get_setting('daily_bonus_min')), float(db.get_setting('daily_bonus_max'))
        bonus_amount = round(random.uniform(min_b, max_b), 1)
        db.update_balance(user_id, bonus_amount)
        db.update_last_bonus_time(user_id)
        claim_text = get_text('bonus_claimed', user_lang).format(bonus_amount=bonus_amount)
        await call.answer(claim_text, show_alert=True)
        await back_to_main_menu(call, state, user_lang)

@dp.callback_query(F.data == "promo")
async def show_promo_menu(call: CallbackQuery, state: FSMContext, user_lang: str):
    await state.set_state(UserStates.enter_promo_code)
    prompt_message = await edit_or_send_message(call, get_text('promo', user_lang), get_back_kb(user_lang, "main_menu"))
    if prompt_message: await state.update_data(prompt_message_id=prompt_message.message_id)
    await call.answer()

@dp.message(UserStates.enter_promo_code, F.text)
async def process_promo_code(message: Message, state: FSMContext, bot: Bot, user_lang: str):
    user_id, code = message.from_user.id, message.text.strip().upper()
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")
    await message.delete()
    if prompt_message_id:
        try: await bot.delete_message(message.chat.id, prompt_message_id)
        except TelegramAPIError: pass
    await state.clear()
    msg_text = ""
    if db.has_user_used_promo(user_id, code): msg_text = get_text('promo_fail_used', user_lang)
    else:
        promo_data = db.get_promocode(code)
        if promo_data and promo_data[1] > 0:
            reward, _ = promo_data
            db.update_balance(user_id, reward); db.use_promocode(user_id, code)
            msg_text = get_text('promo_success', user_lang).format(reward=reward)
        else: msg_text = get_text('promo_fail_general', user_lang)
    
    final_msg = await message.answer(msg_text)
    await asyncio.sleep(4)
    try: 
        await final_msg.delete()
    except TelegramAPIError: 
        pass
    
    balance, username = db.get_user_balance(user_id), message.from_user.username or message.from_user.first_name
    start_text = get_text('start', user_lang).format(user_name=html.bold(username), balance=round(balance,2))
    
    banner = db.get_setting('start_banner')
    if banner:
        await message.answer_photo(photo=banner, caption=start_text, reply_markup=get_main_menu_kb(user_lang))
    else:
        await message.answer(start_text, reply_markup=get_main_menu_kb(user_lang))

@dp.callback_query(F.data == "top")
async def show_top_menu(call: CallbackQuery, user_lang: str):
    await edit_or_send_message(call, get_text('top', user_lang), get_top_menu_kb(user_lang))
    await call.answer()

@dp.callback_query(F.data == "top_balance")
async def show_top_balance(call: CallbackQuery, user_lang: str):
    top_users = db.get_top_by_balance()
    text = get_text('top_balance_title', user_lang)
    if not top_users: text += get_text('top_no_users', user_lang)
    else:
        lines = []
        for i, (user_id, balance, username, first_name) in enumerate(top_users, 1):
            display_name = f"@{username}" if username else html.quote(first_name)
            lines.append(f"{i}. {display_name} — <b>{round(balance, 2)}</b> ⭐")
        text += "\n".join(lines)
    await edit_or_send_message(call, text, get_back_kb(user_lang, "top"))
    await call.answer()

@dp.callback_query(F.data == "top_referrals")
async def show_top_referrals(call: CallbackQuery, user_lang: str):
    top_referrers = db.get_top_by_referrals()
    text = get_text('top_referrals_title', user_lang)
    if not top_referrers: text += get_text('top_no_users', user_lang)
    else:
        lines = []
        for i, (user_id, ref_count, username, first_name) in enumerate(top_referrers, 1):
            display_name = f"@{username}" if username else html.quote(first_name)
            lines.append(f"{i}. {display_name} — <b>{ref_count}</b> 👥")
        text += "\n".join(lines)
    await edit_or_send_message(call, text, get_back_kb(user_lang, "top"))
    await call.answer()

# --- YÖNETİCİ PANELİ ---
@dp.message(Command("admin"), IsAdmin())
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 <b>Добро пожаловать в админ-панель!</b>", reply_markup=get_admin_kb(message.from_user.id))

@dp.callback_query(F.data == "admin_panel", IsAdmin())
async def admin_panel_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await edit_or_send_message(call, "👋 <b>Добро пожаловать в админ-панель!</b>", get_admin_kb(call.from_user.id))
    await call.answer()

@dp.callback_query(F.data == "admin_start_banner", IsAdmin())
async def admin_start_banner_menu(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.set_start_banner)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Удалить баннер", callback_data="admin_delete_banner")
    builder.button(text="⬅️ Назад в админ-панель", callback_data="admin_panel")
    builder.adjust(1)
    await edit_or_send_message(call, "🖼️ <b>Настройка баннера /start</b>\n\nОтправьте фото, которое будет отображаться в главном меню, или нажмите кнопку удаления.", builder.as_markup())
    await call.answer()

@dp.callback_query(F.data == "admin_delete_banner", IsAdmin())
async def admin_delete_banner(call: CallbackQuery, state: FSMContext):
    db.set_setting('start_banner', '')
    await call.answer("✅ Баннер удален!", show_alert=True)
    await admin_panel_callback(call, state)

@dp.message(AdminStates.set_start_banner, F.photo, IsAdmin())
async def admin_set_start_banner(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    db.set_setting('start_banner', file_id)
    await message.answer("✅ Баннер успешно установлен!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

@dp.callback_query(F.data.startswith("withdraw_approve_"), IsAdmin())
async def approve_withdraw(call: CallbackQuery, bot: Bot):
    request_id = int(call.data.split("_")[-1])
    admin_name = html.quote(call.from_user.username or call.from_user.first_name)
    request_data = db.get_withdrawal_request(request_id)
    if not request_data: await call.answer("❌ Запрос не найден.", show_alert=True); return
    uid, user_id, username, amount, gift_name, status, _, details = request_data
    if status != 'pending': await call.answer(f"⚠️ Этот запрос уже был обработан (статус: {status}).", show_alert=True); return
    db.update_balance(user_id, -amount)
    db.update_withdrawal_status(request_id, 'approved')
    details_text = f"\n<b>💳 Номер:</b> <code>{html.quote(details)}</code>" if details else ""
    admin_channel_text = (f"✅ <b>Запрос #{uid} одобрен</b> админом {admin_name}\n\n"
                          f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Списано:</b> {amount} ⭐{details_text}")
    await call.message.edit_text(admin_channel_text, reply_markup=None)
    user_lang = db.get_user_language(user_id)
    try:
        user_msg = get_text('status_approved', user_lang).format(uid=uid, gift_name=gift_name, amount=amount)
        await bot.send_message(user_id, user_msg)
    except TelegramAPIError as e: logging.warning(f"Failed to send approval notification to user {user_id}: {e}")
    if PAYMENTS_CHANNEL_ID != 0:
        public_message = (f"✅ <b>Успешный Вывод #{uid}</b>\n\n"
                          f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Выведено:</b> {amount} ⭐")
        try: await bot.send_message(PAYMENTS_CHANNEL_ID, public_message)
        except TelegramAPIError as e: logging.error(f"Could not send payment proof to channel {PAYMENTS_CHANNEL_ID}: {e}")
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
        text="➡️ Ввести причину",
        callback_data=f"decline_prompt_{request_id}_{channel_chat_id}_{channel_message_id}"
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
    if not all([request_id, channel_chat_id, channel_message_id]): await bot.send_message(message.from_user.id, "❌."); return
    admin_name = html.quote(message.from_user.username or message.from_user.first_name)
    request_data = db.get_withdrawal_request(request_id)
    if not request_data: await bot.send_message(message.from_user.id, f"❌ Запрос #{request_id} не найден."); return
    uid, user_id, username, amount, gift_name, status, _, details = request_data
    if status != 'pending': await bot.send_message(message.from_user.id, f"⚠️ Запрос #{uid} уже обработан (Статус: {status})."); return
    db.update_withdrawal_status(request_id, 'declined', reason)
    details_text = f"\n<b>💳 Номер:</b> <code>{html.quote(details)}</code>" if details else ""
    admin_channel_text = (f"❌ <b>Запрос #{uid} отклонён</b> Админом {admin_name}\n\n"
                          f"👤 <b>Пользователь:</b> {html.quote(username)} (ID: <code>{user_id}</code>)\n"
                          f"🎁 <b>Подарок:</b> {gift_name}\n💰 <b>Списано:</b> {amount} ⭐{details_text}\n\n"
                          f"📝 <b>Причина:</b> {html.quote(reason)}")
    try: await bot.edit_message_text(admin_channel_text, chat_id=channel_chat_id, message_id=channel_message_id, reply_markup=None)
    except TelegramAPIError as e: logging.error(f"Could not edit message in admin channel: {e}")
    user_lang = db.get_user_language(user_id)
    try:
        user_notification = get_text('status_declined', user_lang).format(uid=uid, reason=html.quote(reason))
        await bot.send_message(user_id, user_notification)
    except TelegramAPIError as e: logging.warning(f"Failed to send decline notification to user {user_id}: {e}")
    await bot.send_message(message.from_user.id, f"✅ Запрос #{uid} отклонён.", reply_markup=get_back_to_admin_panel_kb())

# --- REFERRAL BONUS AYARI ---
@dp.callback_query(F.data == "admin_ref_bonus", IsAdmin())
async def ref_bonus_settings(call: CallbackQuery, state: FSMContext):
    await state.clear()
    current_bonus = db.get_setting('ref_bonus')
    text = (f"🤝 <b>Реферальный бонус</b>\n\n"
            f"Текущий бонус: <b>{current_bonus}</b> ⭐\n\n"
            f"<blockquote>Количество звёзд, начисляемых за каждого приглашённого друга.\n"
            f"Введите новое значение (например: <code>1.5</code>)</blockquote>")
    
    prompt_message = await edit_or_send_message(call, text, get_back_to_admin_panel_kb())
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
            raise ValueError("Бонус должен быть положительным")
        
        db.set_setting('ref_bonus', str(new_bonus))
        await message.answer(f"✅ Реферальный бонус изменён: <b>{new_bonus}</b> ⭐", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except ValueError:
        await state.set_state(AdminStates.set_ref_bonus)
        prompt = await message.answer("❌ Неверный формат. Введите правильное число (например: <code>1.5</code>).")
        await state.update_data(prompt_message_id=prompt.message_id)

# --- АДМИН ПАНЕЛЬ: СКАЧАТЬ И УСТАНОВИТЬ БД ---
@dp.callback_query(F.data == "admin_download_db", IsAdmin())
async def admin_download_db_handler(call: CallbackQuery, bot: Bot):
    try:
        file = FSInputFile(DB_FILE, filename=DB_FILE)
        await bot.send_document(call.from_user.id, document=file, caption="💾 <b>Ваша актуальная база данных SQLite.</b>")
        await call.answer("✅ База данных отправлена.")
    except Exception as e:
        await call.answer(f"❌ Ошибка отправки БД: {e}", show_alert=True)

@dp.callback_query(F.data == "admin_upload_db", IsAdmin())
async def admin_upload_db_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.upload_db)
    await edit_or_send_message(
        call,
        "📤 <b>Установка базы данных</b>\n\nОтправьте файл формата <code>.db</code> в этот чат. Это полностью заменит текущую базу данных!",
        get_back_to_admin_panel_kb()
    )
    await call.answer()

@dp.message(AdminStates.upload_db, F.document, IsAdmin())
async def process_upload_db(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    if not doc.file_name.endswith(".db"):
        await message.answer("❌ Файл должен иметь расширение <code>.db</code>. Попробуйте снова или вернитесь в меню.", reply_markup=get_back_to_admin_panel_kb())
        return

    try:
        file_info = await bot.get_file(doc.file_id)
        await bot.download_file(file_info.file_path, destination=DB_FILE)
        global db
        db = Database(DB_FILE)
        await message.answer("✅ База данных успешно загружена и установлена!", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении БД: {e}", reply_markup=get_back_to_admin_panel_kb())

# --- АДМИН ПАНЕЛЬ: СТАТИСТИКА PIARFLOW ---
@dp.callback_query(F.data == "admin_piarflow_stats", IsAdmin())
async def admin_piarflow_stats_handler(call: CallbackQuery):
    data = await PiarFlowAPI.get_bot_data()
    if data.get("status") == "ok":
        bot_info = data.get("bot", {})
        text = (
            f"📈 <b>Статистика PiarFlow</b>\n\n"
            f"🤖 Бот: @{bot_info.get('username')}\n"
            f"📊 Продано подписок: <b>{bot_info.get('sold_subs', 0)}</b>\n"
            f"💰 Заработано: <b>{bot_info.get('earned', 0)}</b> RUB\n"
            f"📈 Не засчитано: {bot_info.get('not_counted', 0)}"
        )
    else:
        text = "❌ Не удалось получить статистику PiarFlow. Проверьте API ключ."
    await edit_or_send_message(call, text, get_back_to_admin_panel_kb())
    await call.answer()

@dp.callback_query(F.data == "admin_stats", IsAdmin())
async def admin_stats(call: CallbackQuery):
    stats = db.get_stats()
    text = (f"📊 <b>Статистика:</b>\n\n"
            f"<b>Пользователи:</b>\n"
            f"├ Всего: <b>{stats['total_users']}</b>\n"
            f"└ За 24 часа: <b>{stats['new_users_24h']}</b>\n\n"
            f"<b>Экономика:</b>\n"
            f"├ Всего звёзд: <b>{stats['total_balance']}</b> ⭐\n"
            f"└ Выведено: <b>{stats['withdrawn_sum']}</b> ⭐\n\n"
            f"<b>Активность:</b>\n"
            f"├ Задания: <b>{stats['active_tasks']}</b>\n"
            f"└ Выполненные задания: <b>{stats['completed_tasks']}</b>\n\n"
            f"<b>Заявки:</b>\n"
            f"├ Ожидают: <b>{stats['withdraw_pending']}</b>\n"
            f"├ Одобрены: <b>{stats['withdraw_approved']}</b>\n"
            f"└ Отклонены: <b>{stats['withdraw_declined']}</b>")
    await edit_or_send_message(call, text, get_back_to_admin_panel_kb())
    await call.answer()

@dp.callback_query(F.data == "admin_broadcast", IsAdmin())
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.broadcast_message)
    await edit_or_send_message(call, "Отправьте сообщение для рассылки всем пользователям:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.broadcast_message, IsAdmin())
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = db.get_all_user_ids()
    sent = 0
    await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")
    for uid in users:
        try:
            await message.copy_to(uid)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Рассылка завершена! Доставлено: {sent}/{len(users)}.", reply_markup=get_back_to_admin_panel_kb())

@dp.callback_query(F.data == "admin_bonus_settings", IsAdmin())
async def admin_bonus_settings(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.set_bonus_amount)
    min_b = db.get_setting('daily_bonus_min')
    max_b = db.get_setting('daily_bonus_max')
    await edit_or_send_message(call, f"🎁 Текущий бонус от {min_b} до {max_b} ⭐.\nВведите новые значения через пробел (например: <code>0.1 0.5</code>):", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.set_bonus_amount, IsAdmin())
async def set_bonus_values(message: Message, state: FSMContext):
    try:
        min_val, max_val = map(float, message.text.replace(',', '.').split())
        db.set_setting('daily_bonus_min', str(min_val))
        db.set_setting('daily_bonus_max', str(max_val))
        await message.answer("✅ Настройки бонуса обновлены!", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except Exception:
        await message.answer("❌ Неверный формат. Введите два числа через пробел:")

@dp.callback_query(F.data == "admin_task_management", IsAdmin())
async def admin_task_management(call: CallbackQuery):
    tasks = db.get_all_tasks()
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить задание", callback_data="admin_task_add")
    for tid, name, reward, cid in tasks:
        builder.button(text=f"❌ Удалить: {name} ({reward}⭐)", callback_data=f"admin_task_del_{tid}")
    builder.button(text="⬅️ Назад в админ-панель", callback_data="admin_panel")
    builder.adjust(1)
    await edit_or_send_message(call, "📝 <b>Управление заданиями</b>", builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_task_del_"), IsAdmin())
async def admin_task_del(call: CallbackQuery):
    tid = int(call.data.split("_")[-1])
    db.delete_task(tid)
    await admin_task_management(call)

@dp.callback_query(F.data == "admin_task_add", IsAdmin())
async def admin_task_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_task_name)
    await edit_or_send_message(call, "Введите название задания (например: <code>Наш канал</code>):", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.add_task_name, IsAdmin())
async def add_task_name_step(message: Message, state: FSMContext):
    await state.update_data(t_name=message.text)
    await state.set_state(AdminStates.add_task_channel_entry)
    await message.answer("Отправьте @username канала или его числовой ID (например <code>-10012345678</code>):", reply_markup=get_back_to_admin_panel_kb())

@dp.message(AdminStates.add_task_channel_entry, IsAdmin())
async def add_task_channel_entry_step(message: Message, state: FSMContext):
    await state.update_data(t_cid=message.text.strip().lstrip('@'))
    await state.set_state(AdminStates.add_task_private_link)
    await message.answer("Отправьте пригласительную ссылку для кнопки (например <code>https://t.me/...</code>):", reply_markup=get_back_to_admin_panel_kb())

@dp.message(AdminStates.add_task_private_link, IsAdmin())
async def add_task_link_step(message: Message, state: FSMContext):
    await state.update_data(t_link=message.text.strip())
    await state.set_state(AdminStates.add_task_reward)
    await message.answer("Введите размер награды за выполнение (число):", reply_markup=get_back_to_admin_panel_kb())

@dp.message(AdminStates.add_task_reward, IsAdmin())
async def add_task_reward_step(message: Message, state: FSMContext):
    try:
        reward = float(message.text.replace(',', '.'))
        data = await state.get_data()
        db.add_task(data['t_name'], data['t_link'], data['t_cid'], reward)
        await message.answer("✅ Задание успешно добавлено!", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except Exception:
        await message.answer("❌ Ошибка. Введите числовое значение награды:")

@dp.callback_query(F.data == "admin_promo_menu", IsAdmin())
async def admin_promo_menu(call: CallbackQuery):
    promos = db.get_all_promocodes()
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать промокод", callback_data="admin_promo_create")
    for code, reward, acts in promos:
        builder.button(text=f"❌ {code} ({reward}⭐ | {acts} шт.)", callback_data=f"admin_promo_del_{code}")
    builder.button(text="⬅️ Назад в админ-панель", callback_data="admin_panel")
    builder.adjust(1)
    await edit_or_send_message(call, "🎟️ <b>Управление промокодами</b>", builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_promo_del_"), IsAdmin())
async def admin_promo_del(call: CallbackQuery):
    code = call.data.split("_")[-1]
    db.delete_promocode(code)
    await admin_promo_menu(call)

@dp.callback_query(F.data == "admin_promo_create", IsAdmin())
async def admin_promo_create(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.create_promo_code)
    await edit_or_send_message(call, "Введите код промокода (только буквы и цифры):", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.create_promo_code, IsAdmin())
async def create_promo_code_step(message: Message, state: FSMContext):
    await state.update_data(p_code=message.text.strip().upper())
    await state.set_state(AdminStates.create_promo_reward)
    await message.answer("Введите награду в звёздах:", reply_markup=get_back_to_admin_panel_kb())

@dp.message(AdminStates.create_promo_reward, IsAdmin())
async def create_promo_reward_step(message: Message, state: FSMContext):
    try:
        reward = float(message.text.replace(',', '.'))
        await state.update_data(p_reward=reward)
        await state.set_state(AdminStates.create_promo_activations)
        await message.answer("Введите количество активаций:", reply_markup=get_back_to_admin_panel_kb())
    except Exception:
        await message.answer("❌ Введите число:")

@dp.message(AdminStates.create_promo_activations, IsAdmin())
async def create_promo_acts_step(message: Message, state: FSMContext):
    try:
        acts = int(message.text)
        data = await state.get_data()
        db.create_promocode(data['p_code'], data['p_reward'], acts)
        await message.answer("✅ Промокод успешно создан!", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except Exception:
        await message.answer("❌ Введите целое число активаций:")

@dp.callback_query(F.data == "admin_req_subs", IsAdmin())
async def admin_req_subs(call: CallbackQuery):
    channels = db.get_required_channels()
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить канал (ОП)", callback_data="admin_req_add")
    for cid_pk, name, cid_str, _ in channels:
        builder.button(text=f"❌ Удалить: {name}", callback_data=f"admin_req_del_{cid_pk}")
    builder.button(text="⬅️ Назад в админ-панель", callback_data="admin_panel")
    builder.adjust(1)
    await edit_or_send_message(call, "🔗 <b>Каналы обязательной подписки (ОП)</b>", builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_req_del_"), IsAdmin())
async def admin_req_del(call: CallbackQuery):
    cid_pk = int(call.data.split("_")[-1])
    db.delete_required_channel(cid_pk)
    await admin_req_subs(call)

@dp.callback_query(F.data == "admin_req_add", IsAdmin())
async def admin_req_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_req_channel_name)
    await edit_or_send_message(call, "Введите название канала для ОП:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.add_req_channel_name, IsAdmin())
async def req_name_step(message: Message, state: FSMContext):
    await state.update_data(r_name=message.text)
    await state.set_state(AdminStates.add_req_channel_entry)
    await message.answer("Отправьте @username или ID канала:", reply_markup=get_back_to_admin_panel_kb())

@dp.message(AdminStates.add_req_channel_entry, IsAdmin())
async def req_cid_step(message: Message, state: FSMContext):
    await state.update_data(r_cid=message.text.strip())
    await state.set_state(AdminStates.add_req_private_link)
    await message.answer("Отправьте публичную или пригласительную ссылку:", reply_markup=get_back_to_admin_panel_kb())

@dp.message(AdminStates.add_req_private_link, IsAdmin())
async def req_link_step(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_required_channel(data['r_name'], data['r_cid'], message.text.strip())
    await message.answer("✅ Канал для ОП успешно добавлен!", reply_markup=get_back_to_admin_panel_kb())
    await state.clear()

@dp.callback_query(F.data == "admin_balance_change", IsAdmin())
async def admin_balance_change_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.balance_change_user_id)
    await edit_or_send_message(call, "Введите ID пользователя для изменения баланса:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.balance_change_user_id, IsAdmin())
async def balance_change_uid(message: Message, state: FSMContext):
    try:
        uid = int(message.text.strip())
        if not db.user_exists(uid):
            await message.answer("❌ Пользователь не найден. Попробуйте другой ID:")
            return
        await state.update_data(bc_uid=uid)
        await state.set_state(AdminStates.balance_change_amount)
        await message.answer("Введите сумму изменения (например <code>10</code> или <code>-5</code>):", reply_markup=get_back_to_admin_panel_kb())
    except Exception:
        await message.answer("❌ Введите корректный числовой ID:")

@dp.message(AdminStates.balance_change_amount, IsAdmin())
async def balance_change_amount_step(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        db.update_balance(data['bc_uid'], amount)
        await message.answer(f"✅ Баланс пользователя <code>{data['bc_uid']}</code> изменен на <b>{amount}</b> ⭐!", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except Exception:
        await message.answer("❌ Введите числовое значение суммы:")

@dp.callback_query(F.data == "admin_manage_admins", IsChiefAdmin())
async def admin_manage_admins(call: CallbackQuery):
    admins = db.get_admins()
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить админа", callback_data="admin_add_admin_start")
    for aid, is_chief in admins:
        role = "👑" if is_chief else "❌ Удалить:"
        builder.button(text=f"{role} ID: {aid}", callback_data=f"admin_del_admin_{aid}")
    builder.button(text="⬅️ Назад в админ-панель", callback_data="admin_panel")
    builder.adjust(1)
    await edit_or_send_message(call, "👑 <b>Управление администраторами</b>", builder.as_markup())
    await call.answer()

@dp.callback_query(F.data.startswith("admin_del_admin_"), IsChiefAdmin())
async def admin_del_admin(call: CallbackQuery):
    aid = int(call.data.split("_")[-1])
    db.remove_admin(aid)
    await admin_manage_admins(call)

@dp.callback_query(F.data == "admin_add_admin_start", IsChiefAdmin())
async def admin_add_admin_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.add_admin_id)
    await edit_or_send_message(call, "Введите Telegram ID нового администратора:", get_back_to_admin_panel_kb())
    await call.answer()

@dp.message(AdminStates.add_admin_id, IsChiefAdmin())
async def admin_add_admin_step(message: Message, state: FSMContext):
    try:
        aid = int(message.text.strip())
        db.add_admin(aid)
        await message.answer("✅ Администратор добавлен!", reply_markup=get_back_to_admin_panel_kb())
        await state.clear()
    except Exception:
        await message.answer("❌ Введите корректный Telegram ID:")

# --- FLASK СЕРВЕР И ВЕБХУК ОТПИСОК (RENDER) ---
flask_app = Flask(__name__)

@flask_app.route('/', methods=['GET'])
def render_health_check():
    return "PiarFlow & TurkmenStars Bot is Running!", 200

@flask_app.route('/webhook/piarflow', methods=['POST'])
def piarflow_webhook_endpoint():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"ok": False}), 400

    if payload.get("test"):
        return jsonify({"ok": True}), 200

    if payload.get("status") == "unsubscribed":
        tg_user_id = payload.get("user_id")
        link = payload.get("link")
        if tg_user_id and link:
            reward = db.get_and_remove_sponsor_reward(int(tg_user_id), link)
            if reward > 0:
                db.update_balance(int(tg_user_id), -reward)
    return jsonify({"ok": True}), 200

async def main():
    def run_flask():
        flask_app.run(host="0.0.0.0", port=PORT)
    
    threading.Thread(target=run_flask, daemon=True).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    dp.message.middleware(MasterMiddleware())
    dp.callback_query.middleware(MasterMiddleware())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
