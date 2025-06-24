import re

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, CallbackQuery

from account.models import CustomUser
from dispatcher import dp
from tg_bot.buttons.reply import *
from tg_bot.state.main import User
from ..buttons.inline import user_accept
from ..send_message import TelegramBot

bot=TelegramBot()

@dp.message(lambda msg: msg.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:

    user = CustomUser.objects.filter(chat_id=message.chat.id,role="Admin").first()
    if user is None:
        await state.set_state(User.phone)
        await message.answer(
            text="Assalomu alaykum, botdan foydalanish uchun avval telefon raqamingizni bosing !",
            reply_markup=phone_number_btn()
        )

    else:
        await  message.answer(
            text="Xush kelibsiz!"
        )


def format_phone_number(phone_number: str) -> str:

    phone_number = ''.join(c for c in phone_number if c.isdigit())

    # Prepend +998 if missing
    if phone_number.startswith('998'):
        phone_number = '+' + phone_number
    elif not phone_number.startswith('+998'):
        phone_number = '+998' + phone_number

    # Check final phone number length
    if len(phone_number) == 13:
        return phone_number
    else:
        raise ValueError("Invalid phone number length")

@dp.message(User.phone)
async def callback_start_handler(message: Message, state: FSMContext) -> None:
    if message.contact:
        phone_number = message.contact.phone_number
        phone_number = format_phone_number(phone_number)

        user = CustomUser.objects.filter(phone=phone_number , role="Admin").first()
        if user:

            user.chat_id = message.from_user.id
            user.save()

            await message.answer(
                f"{user.full_name} botga xush kelibsiz."
            )
        else:

            user=CustomUser.objects.create(
                chat_id=message.from_user.id,
                phone=phone_number,
                role="User"
            )

            admins = CustomUser.objects.filter(role="Admin").all()
            for admin in admins:
                bot.send_message(
                    chat_id=admin.chat_id,
                    text=f"{user.full_name} botga qushildi, botdan foydalanish uchun ruxsat berasizmi?",
                    reply_markup=user_accept(admin.chat_id)
                )

            await message.answer(
                f"{message.from_user.full_name} kechirasiz, sizda botdan foydalanish buyicha kerakli ruxsat mavjud emas ! "
            )


    elif message.text and re.match(r"^\+\d{9,13}$", message.text):
        phone_number = message.text
        phone_number = format_phone_number(phone_number)
        user = CustomUser.objects.filter(phone=phone_number , role__in = ["DIRECTOR", "MULTIPLE_FILIAL_MANAGER"]).first()
        if user:
            await message.answer(
                f"{user.full_name} botga xush kelibsiz, "
                f"ushbu bot orqali siz har kunlik xisobotlar bilan tanishib borishingiz mumkin!"
            )

            user.chat_id = message.from_user.id
            user.save()

        else:
            await message.answer(
                f"{message.from_user.full_name} kechirasiz, sizda botdan foydalanish buyicha kerakli ruxsat mavjud emas ! "
            )



@dp.callback_query(lambda call: call.data.startswith("ok_"))
async def handle_order_selection(callback_query: CallbackQuery, state: FSMContext):

    await callback_query.message.edit_reply_markup(reply_markup=None)
    user_id = callback_query.data.split("_")[1]

    user = CustomUser.objects.filter(id=user_id).first()
    if user and user.role == "User":
        user.role = "Admin"
        user.save()

        await bot.send_message(
            chat_id=user.chat_id,
            text=f"{user.full_name} sizga admin xuquqi berildi!",
        )

        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"{user.full_name} ga  Admin xuquqi berildi"
        )
    elif user and user.role == "Admin":
        await callback_query.message.answer(
            text=f"{user.full_name} role adminga uzgartirilgan!",
            show_alert=True
        )


@dp.callback_query(lambda call: call.data.startswith("no_"))
async def handle_order_selection(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    user_id = callback_query.data.split("_")[1]

    user = CustomUser.objects.filter(id=user_id).first()
    if user:
        user.is_blocked = True
        user.save()

        await bot.send_message(
            chat_id=user.chat_id,
            text=f"{user.full_name}  siz admin tomonidan boklandingiz malumot uchun admin bilan bog'laning!",
        )
        await callback_query.message.answer(
            text="User bloklandi!",
            show_alert=True
        )
    if user and user.is_blocked:
        await callback_query.message.answer(
            text="User allaqachon bloklangan!",
            show_alert=True
        )






