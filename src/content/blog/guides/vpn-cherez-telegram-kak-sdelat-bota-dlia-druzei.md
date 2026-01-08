---
title: 'VPN через Telegram: Как сделать бота для друзей'
description: 'Пошаговое руководство по созданию собственного Telegram-бота для управления VPN-сервером: от выбора VPS до генерации QR-кодов и безопасности.'
pubDate: 2026-02-20
author: 'NetFreedom Admin'
image: '/images/vpn-cherez-telegram-kak-sdelat-bota-dlia-druzei.jpg'
tags: ['VPN', 'Security']
---

В эпоху глобальных блокировок и усиления цензуры в интернете, наличие собственного VPN-сервера перестает быть роскошью для системных администраторов и становится предметом первой необходимости для обычного пользователя. Однако делиться доступом с друзьями или семьей, постоянно генерируя конфиги вручную через терминал — занятие утомительное.

Решение лежит на поверхности: объединить мощь современных протоколов туннелирования и удобство интерфейса Telegram. В этой статье мы разберем, как создать своего Telegram-бота, который будет выдавать ключи доступа к вашему личному VPN нажатием одной кнопки.

## Почему именно Telegram?

Использование Telegram в качестве панели управления вашим VPN имеет несколько неоспоримых преимуществ:
1.  **Кроссплатформенность:** Бот доступен с телефона, планшета и компьютера.
2.  **Простота для конечного пользователя:** Вашим друзьям не нужно учить команды Linux, они просто нажимают «Подключиться».
3.  **Автоматизация:** Бот сам создаст конфигурационный файл, сгенерирует QR-код и отправит его пользователю.
4.  **Безопасность:** Вы можете ограничить круг лиц, имеющих доступ к боту, по их Telegram ID.

## Шаг 1: Подготовка инфраструктуры

Прежде всего, нам понадобится виртуальный сервер (VPS). Для личного использования и 5–10 друзей хватит минимальной конфигурации:
- **ОС:** Ubuntu 22.04 LTS (рекомендуется).
- **Процессор:** 1 ядро.
- **RAM:** 1 ГБ.
- **Локация:** Вне вашей страны (например, Нидерланды, Германия, Казахстан или США), чтобы иметь доступ к заблокированным ресурсам.

### Выбор протокола
Для нашего бота мы выберем **WireGuard**. Он современный, быстрый и имеет отличные библиотеки для управления через командную строку. Если вы находитесь в регионе с очень жесткой фильтрацией трафика, стоит рассмотреть **VLESS + Reality**, но для базового понимания логики бота WireGuard — идеальный кандидат.

## Шаг 2: Установка WireGuard

Зайдите на ваш сервер по SSH и установите WireGuard. Самый простой способ — использовать проверенный скрипт автоматической установки:

bash
wget https://raw.githubusercontent.com/angristan/wireguard-install/master/wireguard-install.sh
chmod +x wireguard-install.sh
./wireguard-install.sh


В процессе установки скрипт спросит адрес сервера и порт. Оставьте значения по умолчанию, если не уверены. После установки скрипт создаст ваш первый клиентский конфиг.

## Шаг 3: Регистрация бота

1. Найдите в Telegram **@BotFather**.
2. Отправьте команду `/newbot`.
3. Дайте боту имя и уникальный юзернейм.
4. Сохраните полученный **API Token**.

## Шаг 4: Пишем логику бота на Python

Мы будем использовать библиотеку `aiogram` для работы с Telegram API. Бот будет запускать системные команды для создания новых пользователей в WireGuard.

### Окружение
Установите необходимые пакеты на сервере:

bash
pip install aiogram qrcode[pil]


### Код бота (фрагмент)

Ниже приведен пример логики создания нового пользователя. Основная идея заключается в вызове скрипта установки с заранее заданными параметрами.

python
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
import qrcode
import os

API_TOKEN = 'ВАШ_ТОКЕН_ЗДЕСЬ'
ADMIN_ID = 12345678  # Ваш ID, чтобы ботом не пользовались чужие

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def generate_qr(config_text, filename):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(config_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)

@dp.message(lambda message: message.text == "/start")
async def send_welcome(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Доступ запрещен. Обратитесь к администратору.")
        return
    
    kb = [
        [types.KeyboardButton(text="Создать доступ для друга")],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Добро пожаловать в VPN-панель!", reply_markup=keyboard)

@dp.message(lambda message: message.text == "Создать доступ для друга")
async def create_vpn(message: types.Message):
    if message.from_user.id != ADMIN_ID: return

    client_name = f"user_{message.message_id}"
    
    # Автоматизируем ввод данных в скрипт angristan
    # В реальности здесь должен быть вызов скрипта через subprocess с передачей аргументов
    process = subprocess.Popen(['./wireguard-install.sh'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Имитируем выбор пунктов меню (добавить пользователя, имя пользователя, DNS)
    stdout, stderr = process.communicate(input=f"1\n{client_name}\n1\n")

    config_path = f"/root/{client_name}.conf"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = f.read()
        
        qr_path = f"{client_name}.png"
        generate_qr(config_data, qr_path)
        
        photo = FSInputFile(qr_path)
        await message.answer_photo(photo, caption=f"Ваш конфиг {client_name}. Просто сканируйте QR в приложении WireGuard!")
        
        # Очистка
        os.remove(qr_path)
    else:
        await message.answer("Ошибка при создании конфига.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


*Примечание: Прямое использование `subprocess` со скриптом `angristan` требует аккуратной обработки потоков ввода-вывода (stdin/stdout). В продакшн-решениях лучше использовать API существующих менеджеров WireGuard, таких как **wg-gen-web** или самописные обертки над `wg` CLI.*

## Шаг 5: Безопасность и масштабирование

Когда вы делаете инструмент для друзей, безопасность сервера становится критически важной.

1.  **Белый список (Whitelist):** В коде бота обязательно проверяйте `message.from_user.id`. Без этого любой, кто узнает юзернейм вашего бота, сможет «съесть» весь трафик вашего сервера.
2.  **Лимиты трафика:** WireGuard сам по себе не умеет ограничивать скорость или объем данных. Для этого используются надстройки вроде `iptables` или специализированные панели (например, Marzban).
3.  **Скрытие бота:** Отключите добавление бота в группы и уберите его из глобального поиска через @BotFather.
4.  **Автозагрузка:** Используйте `systemd`, чтобы ваш бот автоматически поднимался после перезагрузки сервера.

Создайте файл `/etc/systemd/system/vpnbot.service`:
ini
[Unit]
Description=Telegram VPN Bot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/bot.py
Restart=always

[Install]
WantedBy=multi-user.target


## Этическая и юридическая сторона

Создавая VPN-бота, вы берете на себя роль провайдера для своих друзей. Важно помнить:
- **Логирование:** По умолчанию WireGuard не ведет логов посещений. Это хорошо для приватности.
- **Ответственность:** Весь трафик ваших друзей будет выходить в интернет под IP-адресом вашего сервера. Если кто-то из них нарушит правила площадок или закон, претензии могут прийти к владельцу сервера. Используйте только с теми, кому доверяете.

## Заключение

Свой VPN через Telegram — это не только удобный инструмент, но и отличный проект для прокачки навыков системного администрирования и программирования на Python. Вместо того чтобы платить сомнительным сервисам, вы создаете прозрачную и контролируемую среду для себя и своих близких.

В следующей статье мы рассмотрим, как добавить в этот пайплайн протоколы обфускации (Shadowsocks/V2Ray), чтобы ваш VPN оставался невидимым для систем глубокого анализа трафика (DPI). Оставайтесь в безопасности!