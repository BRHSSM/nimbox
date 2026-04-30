import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.crud import get_user
from handlers.callbacks import prepare_download_task

router = Router()


@router.message(F.text.regexp(r'https?://[^\s]+'))
async def handle_url(message: Message, state: FSMContext):

    user = get_user(message.from_user.id)
    if not user or not user.github_token:
        await message.answer("⚠️ Please set your token via /set_token first.")
        return

    await state.update_data(target_url=message.text.strip(), quality="best")

    await ask_compression(message)


@router.message(F.document | F.video | F.photo | F.audio)
async def handle_file(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user.github_token:
        await message.answer("⚠️ Please set your token via /set_token first.")
        return


    file_id = message.document.file_id if message.document else \
              message.video.file_id if message.video else \
              message.audio.file_id if message.audio else message.photo[-1].file_id

    file_info = await message.bot.get_file(file_id)
    file_path = f"tmp_downloads/{message.document.file_name if message.document else 'file'}"


    await message.bot.download_file(file_info.file_path, file_path)


    await state.update_data(target_url=file_path, quality="raw", is_local_file=True)
    await ask_compression(message)


async def ask_compression(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Raw (No Zip)", callback_data="comp_raw")],
        [InlineKeyboardButton(text="📦 Zip (Max Compression)", callback_data="comp_zip")],
        [InlineKeyboardButton(text="🔐 Zip with Password", callback_data="comp_pass")]
    ])
    await message.answer("📥 **File received!**\nHow should I process it?", reply_markup=keyboard, parse_mode="Markdown")