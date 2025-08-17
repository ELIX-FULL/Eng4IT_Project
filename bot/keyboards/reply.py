from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

web_app_info=WebAppInfo(url="")
main_menu = ReplyKeyboardMarkup(
    keyboard=[
            [KeyboardButton(text="📲 Register Device")],
            [KeyboardButton(text="🌐 Our Website", web_app=web_app_info)],
            [KeyboardButton(text="💳 Subscription Plan"), KeyboardButton(text="📟 My Devices")],
            [KeyboardButton(text="🛍 Buy Device")],
            [KeyboardButton(text="🆔 My ID"), KeyboardButton(text="❓ Help")]
        ],
    resize_keyboard=True
)

help_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Subscription Plans")],
        [KeyboardButton(text="➕ Register Device")],
        [KeyboardButton(text="📩 @LaunchX_uz")],
        [KeyboardButton(text="🔙 Back")]
    ],
    resize_keyboard=True
)

share_contact = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Send Phone Number", request_contact=True)]
    ],
    resize_keyboard=True
)

share_location = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Send Location", request_location=True)]
    ],
    resize_keyboard=True
)