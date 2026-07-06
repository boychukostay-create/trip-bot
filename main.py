import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Токен берется из настроек Render (Environment Variables)
API_TOKEN = os.getenv('API_TOKEN')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class TripCalc(StatesGroup):
    waiting_for_route = State()
    waiting_for_fuel_price = State()
    waiting_for_car = State()
    waiting_for_passengers = State()

ROUTES = {"Пори": 350, "Коккола": 220}
CARS = {"1.4 Бензин": 6.5, "1.6 Автомат": 8.0, "1.8 Дизель": 5.5, "2.0 Бензин": 9.0}

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for r in ROUTES.keys(): markup.add(KeyboardButton(r))
    await message.answer("Привет! Выбери маршрут:", reply_markup=markup)
    await TripCalc.waiting_for_route.set()

@dp.message_handler(state=TripCalc.waiting_for_route)
async def choose_route(message: types.Message, state: FSMContext):
    await state.update_data(route=message.text, dist=ROUTES[message.text])
    await message.answer("Введите текущую цену топлива за литр (например, 1.95):")
    await TripCalc.waiting_for_fuel_price.set()

@dp.message_handler(state=TripCalc.waiting_for_fuel_price)
async def get_price(message: types.Message, state: FSMContext):
    await state.update_data(price=float(message.text.replace(',', '.')))
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for c in CARS.keys(): markup.add(KeyboardButton(c))
    await message.answer("Выберите автомобиль:", reply_markup=markup)
    await TripCalc.waiting_for_car.set()

@dp.message_handler(state=TripCalc.waiting_for_car)
async def choose_car(message: types.Message, state: FSMContext):
    await state.update_data(car=message.text, consumption=CARS[message.text])
    await message.answer("Сколько всего человек участвует в поездке?")
    await TripCalc.waiting_for_passengers.set()

@dp.message_handler(state=TripCalc.waiting_for_passengers)
async def final_calc(message: types.Message, state: FSMContext):
    try:
        people = int(message.text)
        data = await state.get_data()
        total_fuel = (data['dist'] / 100) * data['consumption']
        total_price = total_fuel * data['price']
        await message.answer(f"📊 **Итого по поездке:**\nМаршрут: {data['route']}\nАвто: {data['car']}\nВсего цена: {total_price:.2f} €\nНа каждого ({people}): {total_price/people:.2f} €", parse_mode="Markdown")
    except:
        await message.answer("Введи просто число (например: 2).")
    finally:
        await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
