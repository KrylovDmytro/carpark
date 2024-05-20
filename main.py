import telebot 
from telebot import types
from datetime import datetime
from database_client import DatabaseClient

# Токен від BotFather
TOKEN = '7022170542:AAFsW-pgaVw70jiaiRx9qDk2ecngUCEosGU'
bot = telebot.TeleBot(TOKEN)

# Екземпляр з'єднання з базою даних
db = DatabaseClient()

# Зберігання даних клієнтів для управління сесіями
client_data = {}
admin_sessions = {}


###################################################### Основна програма ######################################################


# Визначення команд для бота
commands = [
    telebot.types.BotCommand("/start", "Запустити бота"),
    telebot.types.BotCommand("/admin", "Вхід адміністратора")
]

# Встановлення команд бота
try:
    bot.set_my_commands(commands)
except telebot.apihelper.ApiTelegramException as e:
    print(f"Помилка встановлення команд бота: {e}")

# Обробник команди '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Ласкаво просимо до бота управління паркінгом!")
    show_main_menu(message.chat.id)


###################################################### Меню ######################################################


# Показати головне меню
def show_main_menu(chat_id, text="Ви повернулись до головного меню. Оберіть дію:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_auth = types.KeyboardButton('Авторизація')
    btn_reg = types.KeyboardButton('Реєстрація')
    markup.add(btn_auth, btn_reg)
    bot.send_message(chat_id, text, reply_markup=markup)

# Показати меню послуг
def show_service_menu(chat_id, text="Ви повернулись до меню користувача. Оберіть дію:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_services = types.KeyboardButton('Послуги')
    btn_backmain = types.KeyboardButton('Головне меню')
    markup.add(btn_services)
    markup.add(btn_backmain)
    bot.send_message(chat_id, text, reply_markup=markup)


###################################################### Кнопки ######################################################


# Обробник кнопки "Реєстрація"
@bot.message_handler(func=lambda message: message.text == "Реєстрація")
def handle_registration(message):
    msg = bot.send_message(message.chat.id, "Введіть ваше повне ім'я:")
    bot.register_next_step_handler(msg, process_name_step)

# Обробник введення імені під час реєстрації
def process_name_step(message):
    chat_id = message.chat.id
    name = message.text
    msg = bot.send_message(chat_id, "Введіть номер вашого транспорту:")
    bot.register_next_step_handler(msg, lambda msg: process_numbercar_step(msg, name))

# Обробник введення номера транспорту під час реєстрації
def process_numbercar_step(message, name):
    chat_id = message.chat.id
    numbercar = message.text
    msg = bot.send_message(chat_id, "Введіть марку вашого транспорту:")
    bot.register_next_step_handler(msg, lambda msg: process_brand_step(msg, name, numbercar))

# Обробник введення марки транспорту під час реєстрації
def process_brand_step(message, name, numbercar):
    chat_id = message.chat.id
    brand = message.text
    msg = bot.send_message(chat_id, "Введіть номер вашої платіжної картки:")
    bot.register_next_step_handler(msg, lambda msg: process_payment_card_step(msg, name, numbercar, brand))

# Обробник введення платіжної картки під час реєстрації
def process_payment_card_step(message, name, numbercar, brand):
    chat_id = message.chat.id
    payment_card = message.text
    id_client, response = db.add_client(name, numbercar, brand, payment_card, chat_id)
    if id_client:
        client_data[chat_id] = {'id_client': id_client, 'name': name, 'payment_card': payment_card, 'numbercar': numbercar}  # Зберігання даних клієнта
    bot.send_message(chat_id, response)
    show_main_menu(chat_id)

# Обробник кнопки "Авторизація"
@bot.message_handler(func=lambda message: message.text == "Авторизація")
def ask_for_numbercar(message):
    msg = bot.send_message(message.chat.id, "Введіть номер вашого транспорту для авторизації:")
    bot.register_next_step_handler(msg, perform_authentication)


###################################################### Авторизація ######################################################


# Обробник авторизації
def perform_authentication(message):
    numbercar = message.text.strip()
    client_info = db.authenticate_by_numbercar(numbercar)
    if client_info:
        entry_datetime = datetime.strptime(client_info[5], '%Y-%m-%d %H:%M:%S')
        exit_datetime = datetime.strptime(client_info[6], '%Y-%m-%d %H:%M:%S')

        formatted_entry_date = entry_datetime.strftime('%Y-%m-%d %H:%M:%S')
        formatted_exit_date = exit_datetime.strftime('%Y-%m-%d %H:%M:%S')


        client_data[message.chat.id] = {'id_client': client_info[0], 'name': client_info[1], 'payment_card': client_info[4], 'numbercar': client_info[2]}  # Зберігання даних клієнта
        balance = db.get_balance(client_info[4])

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_services = types.KeyboardButton('Послуги')
        btn_backmain = types.KeyboardButton('Головне меню')
        markup.add(btn_services)
        markup.add(btn_backmain)

        bot.send_message(message.chat.id,
            f"""🙍‍♂️ Вітаємо, {client_info[1]}!\n<b>✅ Ви успішно авторизувались.</b>\n
        --------------------------------
📒 1. Номер вашого транспорту: {client_info[2]}
🚘 2. Ваш транспорт: {client_info[3]}
🕛 3. Час заїзду: {formatted_entry_date}
🕛 4. Час виїзду: {formatted_exit_date}
💳 5. Ваш баланс: {balance} UAH
🅿️ 6. Місце для паркування: {client_info[7]}
🏢 7. Поверх: {client_info[8]}
        --------------------------------""",
            parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Цей номер транспорту не зареєстровано на парковці. Спробуйте ще раз або зареєструйтесь.")
        show_main_menu(message.chat.id)


###################################################### Послуги ######################################################


# Обробник кнопки "Послуги"
@bot.message_handler(func=lambda message: message.text == "Послуги")
def handle_services(message):
    services = db.fetch_active_services()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    
    if services:
        for service_id, name, description, price in services:
            button_text = f"{name} - {price} UAH"
            markup.add(types.KeyboardButton(button_text))
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(message.chat.id, "Оберіть послугу для деталей та оплати:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda msg: process_service_selection(msg, services))
    else:
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(message.chat.id, "Наразі немає доступних послуг.", reply_markup=markup)

# Обробник вибору послуги
def process_service_selection(message, services):
    selection = message.text
    if selection == 'Назад':
        show_service_menu(message.chat.id)
        return
    
    selected_service = next((s for s in services if f"{s[1]} - {s[3]} UAH" == selection), None)
    if selected_service:
        service_id, name, description, price = selected_service
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("Оплатити"), types.KeyboardButton('Назад')) 
        response_text = f"{name}\nОпис: {description}\nЦіна: {price} UAH\nНатисніть 'Оплатити' для продовження або 'Назад' для повернення."
        bot.send_message(message.chat.id, response_text, reply_markup=markup)
        bot.register_next_step_handler(message, lambda msg: process_payment(msg, service_id, price, name))

# Обробник оплати послуги
def process_payment(message, service_id, price, service_name):
    if message.text == "Оплатити":
        client = client_data.get(message.chat.id)
        if client:
            payment_card = client['payment_card']
            id_client = client['id_client']
            success, new_balance = db.deduct_money(payment_card, price)
            if not success:
                bot.send_message(message.chat.id, f"""
<b>🤖 У вас недостатньо коштів.</b>
<b>💳 Поточний баланс:</b> {new_balance} UAH""", parse_mode='HTML')
                show_service_menu(message.chat.id)
                return

            order_id = db.create_order(id_client, service_id)
            if isinstance(order_id, int):
                db.update_order_status(order_id, 'paid')

                if service_name == "Добове паркування":
                    db.extend_parking(client['numbercar'])
                elif service_name == "Змінити місце паркування":
                    msg = bot.send_message(message.chat.id, "Введіть новий номер місця для паркування:")
                    bot.register_next_step_handler(msg, lambda msg: process_new_parking_place(msg, id_client))
                    return
                
                bot.send_message(message.chat.id, f"""
<b>🤖 Ваш платіж на суму {price} UAH прийнято.
       Замовлення №{order_id} створено.</b>\n
<b>💳 Поточний баланс:</b> {new_balance} UAH""", parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, f"Помилка: {order_id}")
        else:
            bot.send_message(message.chat.id, "Помилка: Не вдалося знайти дані клієнта.")
        show_service_menu(message.chat.id)
    elif message.text == 'Назад':
        handle_services(message)

# Обробник введення нового місця паркування
def process_new_parking_place(message, id_client):
    new_place_number = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введіть новий поверх:")
    bot.register_next_step_handler(msg, lambda msg: finalize_new_parking_place(msg, id_client, new_place_number))

# Завершення обробки зміни місця паркування
def finalize_new_parking_place(message, id_client, new_place_number):
    new_floor = message.text.strip()
    response = db.change_parking_space(id_client, new_place_number, new_floor)
    bot.send_message(message.chat.id, response)
    show_service_menu(message.chat.id)
    
    
    
###################################################### Головне меню ######################################################
    
# Обробник кнопки "Головне меню"
@bot.message_handler(func=lambda message: message.text == "Головне меню")
def handle_back_to_main(message):
    show_main_menu(message.chat.id, "Ви повернулись до головного меню. Оберіть дію:")


###################################################### Адмін панель ######################################################

# Обробник команди '/admin'
@bot.message_handler(commands=['admin'])
def admin_login(message):
    msg = bot.send_message(message.chat.id, "Введіть пароль адміністратора:")
    bot.register_next_step_handler(msg, process_admin_login)

# Обробник введення пароля адміністратора
def process_admin_login(message):
    if message.text == "admin":
        admin_sessions[message.chat.id] = True
        bot.send_message(message.chat.id, "Вітаємо, Адміністратор! Ви маєте доступ до меню адміністратора.")
        show_admin_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Невірний пароль. Доступ заборонено.")
        show_main_menu(message.chat.id)

# Показати меню адміністратора
def show_admin_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_delete_user = types.KeyboardButton('Видалити користувача')
    btn_edit_parking = types.KeyboardButton('Редагувати паркування')
    btn_view_orders = types.KeyboardButton('Переглянути замовлення')
    btn_service_edit = types.KeyboardButton('Редагування сервісів')
    btn_backmain = types.KeyboardButton('Головне меню')
    markup.add(btn_delete_user, btn_edit_parking, btn_view_orders, btn_service_edit)
    markup.add(btn_backmain)
    bot.send_message(chat_id, "Меню адміністратора. Оберіть дію:", reply_markup=markup)

# Обробник кнопки "Видалити користувача"
@bot.message_handler(func=lambda message: message.text == "Видалити користувача")
def ask_for_delete_user(message):
    if admin_sessions.get(message.chat.id):
        msg = bot.send_message(message.chat.id, "Введіть номер транспорту для видалення:")
        bot.register_next_step_handler(msg, delete_user)
    else:
        bot.send_message(message.chat.id, "Доступ заборонено. Лише для адміністратора.")

# Обробник зупинки бота
def stop_bot(message):
    if message.chat.id in admin_sessions:
        bot.send_message(message.chat.id, "Адміністратор не може зупинити бота.")
    else:
        bot.send_message(message.chat.id, "Бот зупиняється. До побачення!")
        db.close()
        bot.stop_polling()

# Обробник видалення користувача
def delete_user(message):
    numbercar = message.text.strip()
    chat_id, response = db.delete_user_by_numbercar(numbercar)
    if chat_id:
        bot.send_message(chat_id, f"""🔴 Ваш транспорт з номером <b>{numbercar}</b> евакуйовано з місця паркування.""", parse_mode='HTML')
    bot.send_message(message.chat.id, response)
    show_admin_menu(message.chat.id)

# Обробник кнопки "Редагувати паркування"
@bot.message_handler(func=lambda message: message.text == "Змінити місце паркування")
def ask_for_parking_details(message):
    if admin_sessions.get(message.chat.id):
        msg = bot.send_message(message.chat.id, "Введіть номер транспорту користувача для зміни місця паркування:")
        bot.register_next_step_handler(msg, process_parking_change)
    else:
        bot.send_message(message.chat.id, "Доступ заборонено. Лише для адміністратора.")

# Обробник процесу зміни паркування
def process_parking_change(message):
    numbercar = message.text.strip()
    client = db.authenticate_by_numbercar(numbercar)
    if client:
        client_id = client[0]
        client_name = client[1]
        msg = bot.send_message(message.chat.id, "Введіть новий номер місця для паркування:")
        bot.register_next_step_handler(msg, lambda msg: get_new_floor(msg, client_id, client_name, numbercar))
    else:
        bot.send_message(message.chat.id, "Номер транспорту не знайдено.")
        show_admin_menu(message.chat.id)

# Обробник введення нового поверху для паркування
def get_new_floor(message, client_id, client_name, numbercar):
    new_place_number = message.text.strip()
    msg = bot.send_message(message.chat.id, "Введіть новий поверх:")
    bot.register_next_step_handler(msg, lambda msg: finalize_parking_change(msg, client_id, client_name, new_place_number, numbercar))

# Завершення обробки зміни паркування
def finalize_parking_change(message, client_id, client_name, new_place_number, numbercar):
    new_floor = message.text.strip()
    response = db.change_parking_space(client_id, new_place_number, new_floor)
    bot.send_message(message.chat.id, response)
    show_admin_menu(message.chat.id)

# Обробник кнопки "Переглянути замовлення"
@bot.message_handler(func=lambda message: message.text == "Переглянути замовлення")
def ask_for_vehicle_number(message):
    if admin_sessions.get(message.chat.id):
        msg = bot.send_message(message.chat.id, "Введіть номер транспорту для перегляду замовлень:")
        bot.register_next_step_handler(msg, view_orders)
    else:
        bot.send_message(message.chat.id, "Доступ заборонено. Лише для адміністратора.")

# Обробник перегляду замовлень
def view_orders(message):
    numbercar = message.text.strip()
    orders = db.get_order_history_by_numbercar(numbercar)
    if orders:
        response = "\n".join([f"Замовлення ID: {order[0]}, Послуга: {order[1]}, Статус: {order[2]}, Ціна: {order[3]}" for order in orders])
    else:
        response = "Жодного замовлення не знайдено."
    bot.send_message(message.chat.id, response)
    show_admin_menu(message.chat.id)

# Обробник кнопки "Редагування сервісів"
@bot.message_handler(func=lambda message: message.text == "Редагування сервісів")
def handle_edit_services(message):
    services = db.fetch_all_services()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    
    if services:
        for service_id, name in services:
            button_text = f"{name} - ID: {service_id}"
            markup.add(types.KeyboardButton(button_text))
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(message.chat.id, "Оберіть сервіс для редагування:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda msg: process_service_edit_selection(msg, services))
    else:
        markup.add(types.KeyboardButton('Назад'))
        bot.send_message(message.chat.id, "Наразі немає доступних сервісів.", reply_markup=markup)

# Обробник вибору сервісу для редагування
def process_service_edit_selection(message, services):
    selection = message.text
    if selection == 'Назад':
        show_admin_menu(message.chat.id)
        return
    
    selected_service = next((s for s in services if f"{s[1]} - ID: {s[0]}" == selection), None)
    if selected_service:
        service_id, name = selected_service
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn_edit = types.KeyboardButton('Редагувати')
        btn_cancel = types.KeyboardButton('Скасувати')
        markup.add(btn_edit, btn_cancel)
        msg = bot.send_message(message.chat.id, f"Ви обрали сервіс: {name}\nБажаєте його редагувати?", reply_markup=markup)
        bot.register_next_step_handler(msg, lambda msg: process_service_edit_choice(msg, service_id, name))

# Обробник вибору редагувати або скасувати сервіс
def process_service_edit_choice(message, service_id, name):
    if message.text == 'Редагувати':
        msg = bot.send_message(message.chat.id, f"Редагування сервісу: {name}\nВведіть нову назву:")
        bot.register_next_step_handler(msg, lambda msg: process_service_name_edit(msg, service_id))
    elif message.text == 'Скасувати':
        bot.send_message(message.chat.id, "Редагування скасовано.")
        show_admin_menu(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Невідома команда. Будь ласка, оберіть 'Редагувати' або 'Скасувати'.")
        process_service_edit_selection(message, services)

# Обробник введення нової назви сервісу
def process_service_name_edit(message, service_id):
    new_name = message.text
    msg = bot.send_message(message.chat.id, "Введіть новий опис сервісу:")
    bot.register_next_step_handler(msg, lambda msg: process_service_description_edit(msg, service_id, new_name))

# Обробник введення нового опису сервісу
def process_service_description_edit(message, service_id, new_name):
    new_description = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_activate = types.KeyboardButton('Активувати')
    btn_deactivate = types.KeyboardButton('Деактивувати')
    markup.add(btn_activate, btn_deactivate)
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: finalize_service_edit(msg, service_id, new_name, new_description))

# Завершення обробки редагування сервісу
def finalize_service_edit(message, service_id, new_name, new_description):
    action = message.text
    active = action == 'Активувати'
    db.update_service(service_id, new_name, new_description, active)
    bot.send_message(message.chat.id, f"Сервіс {new_name} успішно оновлено.")
    show_admin_menu(message.chat.id)

# Почати опитування
bot.polling(none_stop=True)
