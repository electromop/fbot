import telebot
import time
# import pytesseract
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboa import Keyboa
API_TOKEN = '5873525905:AAGkEpG4gQDN-H3LExJ0iqXuMkAlMNdPerQ'

with open('config.json') as f:
    config = json.load(f)

kb_list = ['Оформить заказ', 'Отмена']
currency = config["currency"]
root_pass = config["pass"]
keyboard = Keyboa(items=kb_list)
bot = telebot.TeleBot(API_TOKEN)

def list_to_str(mass):
    str_mass = ''
    for i in mass:
        str_mass += i
    return str_mass

def get_hello():
    local_time = time.strftime("%H", time.localtime())
    local_time = int(local_time)
    cond = 'Здравствуйте'
    if 11 < local_time <= 16:
        cond = 'Добрый день'
    elif 16 < local_time <= 22:
        cond = 'Добрый вечер'
    elif 22 < local_time <= 23 or 0 <= local_time <= 5:
        cond = 'Доброй ночи'
    elif 5 < local_time <= 11:
        cond = 'Доброе утро'
    return cond

def price(items_amount, yuan_amount, city):
    shipping_price = 1200 * items_amount
    price_cost = yuan_amount * config["currency"] + shipping_price
    if price_cost <= 10000:
        prcnt_cost = price_cost * 1.2
    elif price_cost > 10000 and price_cost < 20000:
        prcnt_cost = price_cost * 1.15
    elif price_cost >= 20000:
        prcnt_cost = price_cost * 1.1
    price_response = f'Стоимость заказа будет составлять: {round(prcnt_cost)} рублей\n'
    if city == None:
        return price_response
    if city.lower() != 'москва':
        price_response += f'Доставка до города {city} оплачивается отдельно по прибытию товара в Москву.'
    return price_response

bot.set_my_commands([
    telebot.types.BotCommand("/start", "Запуск бота"),
    telebot.types.BotCommand("/help", "Помощь"),
    telebot.types.BotCommand("/price", "Узнать цену заказа в рублях"),
    telebot.types.BotCommand("/order", "Оформить заказ")
])


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "Оформить заказ":
        bot.answer_callback_query(call.id, "Заявка отправлена!")
        bot.send_message(call.message.chat.id, "Ваша заявка оформлена, в ближайшее время администратор напишет вам для окончательного оформления и подтверждения заказа. Напишите /start для дальнейших действий")
        bot.register_next_step_handler()
    elif call.data == "Отмена":
        bot.answer_callback_query(call.id, "Отмена")
        bot.send_message(call.message.chat.id, "Заявка на оформление отменена. Напишите /start для дальнейших действий")

################################## START ####################################
@bot.message_handler(commands=['start'])
def send_welcome(message):
    hello_time = get_hello()

    bot.send_message(message.chat.id, hello_time + """\
, {0.first_name}! Тут вы можете проверить цену товара или отправить заявку на оформление заказа. Для того, чтобы проверить цену в рублях или оформить заявку на заказ используйте соответствующие кнопки в меню. \n Или напишите /help.
""".format(message.from_user))


################################## HELP ####################################
@bot.message_handler(commands=['help'])
def send_info(message):
    bot.send_message(message.chat.id, '/price - узнать цену в рублях \n/order - отправить заявку для оформления заказа \n')


################################## PRICE ####################################
@bot.message_handler(commands=['price'])
def get_amount(message):
    bot.send_message(message.chat.id, 'Напишите количество вещей в заказе.\nНапример:\n5')
    bot.register_next_step_handler(message, get_price)
def get_price(message):
    try:
        mess_amount = int(message.text)
        price_list = [mess_amount]
        bot.send_message(message.chat.id, "Напишите цену заказа в юанях.\nНапример:\n1100")
        bot.register_next_step_handler(message, get_city, price_list)
    except ValueError:
        bot.send_message(message.chat.id, "Количество должно быть числом, введите /price заново")
        print(price_list)
def get_city(message, price_list):
    try:
        mess_price = int(message.text)
        price_list.append(mess_price)
        bot.send_message(message.chat.id, "Напишите город получения заказа.\nНапример:\nМосква")
        bot.register_next_step_handler(message, send_price_info, price_list)
    except ValueError:
        bot.send_message(message.chat.id, "Цена должна быть числом, введите /price заново")
def send_price_info(message, price_list):
    price_list.append(message.text)
    resp_price = price(price_list[0], price_list[1], price_list[2])
    bot.send_message(message.chat.id, resp_price)

################################## ORDER/ROOT ####################################
@bot.message_handler(commands=['order'])
def get_order_arts(message):
    bot.send_message(message.chat.id, 'Для оформления заказа напишите артикулы товаров и размеры товара в соответствующем формате: \nNN987352 44.5, NN562782 XL, ... \nЕсли товар один, то просто отправьте артикул без других знаков .\nДля того, чтобы узнать где взять артикул напишите /help.')
    bot.register_next_step_handler(message, get_order_price)
def get_order_price(message):
    if str(message.text) != root_pass:
        try:
            order_dict = {}
            order_dict['order_arts'] = str(message.text).split(",")
            bot.send_message(message.chat.id, 'Напишите сумму заказа в юанях.')
            bot.register_next_step_handler(message, send_order_response, order_dict)
        except ValueError:
            bot.send_message(message.chat.id, "Неверно введен артикул")
    else:
        bot.send_message(message.chat.id, "Зашел папа!")
        bot.send_message(message.chat.id, "1 - поменять курс, 2 - залить новые фотки")
        bot.register_next_step_handler(message, check_root_op)
def send_order_response(message, order_dict):
    try:
        order_dict['order_price'] = str(message.text)
        order_resp = '\n'.join(order_dict['order_arts']) + '\n' + order_dict['order_price'] + ' юаней'
        bot.send_message(message.chat.id, 'Информация по вашему заказу: ' + '\n' + order_resp + '\n' + price(len(order_dict['order_arts']), int(order_dict['order_price']), None))
        bot.send_message(
            chat_id=message.chat.id, reply_markup=keyboard(),
            text="Вы подтверждаете заказ?")
    except ValueError:
        bot.send_message(message.chat.id, "Цена должна быть числом, введите /price заново")
def check_root_op(message):
    try:
        int_op = int(message.text)
        if int_op == 1:
            bot.send_message(message.chat.id, f'курс сейчас: {config["currency"]}')
            bot.send_message(message.chat.id, 'отправь новый курс числом')
            bot.register_next_step_handler(message, update_currency)
        elif int_op == 2:
            bot.send_message(message.chat.id, 'отправляй картинки паком, по паре. То есть одно сообщение - несколько фото ОДНОЙ пары')
            bot.register_next_step_handler(message, add_photos)
        else:
            bot.send_message(message.chat.id, 'ошибся в номере как так можно, придется перезапустить...')
    except ValueError:
        bot.send_message(message.chat.id, "либо 1 либо 2 че тупишь, придется перезапустить...")
def update_currency(message):
    try:
        new_price = float(message.text)
        config["currency"] = new_price

        with open('config.json', 'w') as f:
            f.write(json.dumps(config))

        bot.send_message(message.chat.id, f'Цена изменена на {config["currency"]}')
    except ValueError:
        bot.send_message(message.chat.id, "как в цене могут быть буквы епта, перезапускай!")
def add_photos(message):
    try:
        new_price = float(message.text)
        bot.send_message(message.chat.id, f'Цена изменена на {new_price}')
    except ValueError:
        bot.send_message(message.chat.id, "как в цене могут быть буквы епта, перезапускай!")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, 'Не понимаю, что вы пишите, используйте /help')

bot.infinity_polling(timeout=10, long_polling_timeout = 5)
