import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from mcrcon import MCRcon

# ==========================================
# НАСТРОЙКИ
# ==========================================
BOT_TOKEN = "ТВОЙ_НОВЫЙ_ТОКЕН_ЗДЕСЬ"  # Вставь НОВЫЙ токен от BotFather
RCON_HOST = "127.0.0.1"                # IP сервера (если бот на том же ПК - оставь 127.0.0.1)
RCON_PORT = 25575
RCON_PASS = "eladeselasobi123"         # Твой пароль RCON

# Цены в Telegram Stars (1 Star ~ 2-3 рубля, цены ставь по своему усмотрению)
SHOP_ITEMS = {
    "vip": {"name": "VIP", "price": 50, "group": "vip"},
    "legend": {"name": "LEGEND", "price": 100, "group": "legend"},
    "admin": {"name": "ADMIN", "price": 210, "group": "admin"}
}

# ==========================================
# ЛОГИКА RCON
# ==========================================
def give_privilege(player_name: str, group: str) -> bool:
    try:
        with MCRcon(RCON_HOST, RCON_PASS, port=RCON_PORT) as mcr:
            command = f"lp user {player_name} parent set {group}"
            resp = mcr.command(command)
            logging.info(f"[RCON] Выдано право {group} игроку {player_name}. Ответ: {resp}")
            return True
    except Exception as e:
        logging.error(f"[RCON] Ошибка: {e}")
        return False

# ==========================================
# НАСТРОЙКА БОТА
# ==========================================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояние для ввода ника
class ShopState(StatesGroup):
    waiting_for_nickname = State()
    item_to_buy = State()

# ==========================================
# ХЕНДЛЕРЫ
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    for item_id, item in SHOP_ITEMS.items():
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"{item['name']} - {item['price']} ⭐",
                callback_data=f"buy_{item_id}"
            )
        ])
    await message.answer("🛒 Добро пожаловать в магазин NovaMC!\nВыбери привилегию:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery, state: FSMContext):
    item_id = callback.data.split("_")[1]
    item = SHOP_ITEMS.get(item_id)
    
    if not item:
        await callback.answer("Ошибка: товар не найден.")
        return

    await state.update_data(item_id=item_id)
    await state.set_state(ShopState.waiting_for_nickname)
    
    await callback.message.answer(f"Вы выбрали **{item['name']}**.\nВведите ваш **ник в Minecraft** (с точностью до регистра):", parse_mode="Markdown")
    await callback.answer()

@dp.message(ShopState.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    nickname = message.text.strip()
    if len(nickname) < 3:
        await message.answer("Ник слишком короткий. Попробуйте снова.")
        return
    
    data = await state.get_data()
    item_id = data['item_id']
    item = SHOP_ITEMS[item_id]
    
    await state.update_data(nickname=nickname)
    
    # Отправляем счет на оплату в Stars
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=f"Привилегия {item['name']}",
        description=f"Выдача привилегии {item['name']} игроку {nickname} на сервере NovaMC",
        payload=f"{item_id}_{nickname}",
        provider_token="", # Пустая строка для цифровых товаров
        currency="XTR",    # Telegram Stars
        prices=[LabeledPrice(label=item['name'], amount=item['price'])],
        start_parameter="create_invoice"
    )
    await state.clear()

@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    item_id, nickname = payload.split("_", 1)
    item = SHOP_ITEMS.get(item_id)
    
    if not item:
        await message.answer("Ошибка: товар не найден.")
        return
    
    await message.answer(f"✅ Оплата получена! Выдаем **{item['name']}** игроку **{nickname}**...")
    
    # Выдаем через RCON
    success = give_privilege(nickname, item['group'])
    
    if success:
        await message.answer(f"🎉 Привилегия успешно выдана! Зайдите на сервер (может потребоваться перезайти).")
    else:
        await message.answer(f"⚠️ Произошла ошибка при выдаче. Свяжитесь с администрацией и покажите этот чек.")

# ==========================================
# ЗАПУСК
# ==========================================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.info("Бот запущен...")
    asyncio.run(main())