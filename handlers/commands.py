import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.crud import create_or_update_user, get_user

router = Router()

class CookieState(StatesGroup):
    waiting_for_file = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    create_or_update_user(message.from_user.id)
    welcome_text = (
        "👋 **Welcome to RGit uploader!**\n\n"
        "I'm here to bypass restrictions and upload files directly to your GitHub repository.\n\n"
        "⚙️ **Setup Instructions:**\n"
        "1️⃣ `/set_token <YOUR_GITHUB_PAT>` - Set your PAT.\n"
        "2️⃣ `/set_repo <username/repo>` - Set your target repository.\n"
        "3️⃣ `/set_cookies` - Upload YouTube Cookies (Optional).\n\n"
        "💡 *Just send me any direct link, file, or media URL to start!*"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@router.message(Command("set_token"))
async def set_token(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ **Usage:** `/set_token <PAT>`", parse_mode="Markdown")
        return
    create_or_update_user(message.from_user.id, github_token=args[1].strip())
    await message.answer("✅ **GitHub Token saved!**", parse_mode="Markdown")

@router.message(Command("set_repo"))
async def set_repo(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ **Usage:** `/set_repo <user/repo>`", parse_mode="Markdown")
        return
    create_or_update_user(message.from_user.id, github_repo=args[1].strip())
    await message.answer(f"✅ **Repo set to:** `{args[1].strip()}`", parse_mode="Markdown")

@router.message(Command("set_cookies"))
async def cmd_set_cookies(message: Message, state: FSMContext):
    await message.answer("🍪 **Please send me your `cookies.txt` file.**\n(Export it from YouTube using a browser extension)", parse_mode="Markdown")
    await state.set_state(CookieState.waiting_for_file)

@router.message(CookieState.waiting_for_file, F.document)
async def process_cookies(message: Message, state: FSMContext):
    if not message.document.file_name.endswith(".txt"):
        await message.answer("⚠️ Please send a valid `.txt` file.")
        return

    file_info = await message.bot.get_file(message.document.file_id)
    file_path = f"tmp_downloads/cookies_{message.from_user.id}.txt"
    os.makedirs("tmp_downloads", exist_ok=True)
    await message.bot.download_file(file_info.file_path, file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        cookies_text = f.read()

    create_or_update_user(message.from_user.id, youtube_cookies=cookies_text)
    os.remove(file_path)
    await state.clear()
    await message.answer("✅ **YouTube Cookies saved successfully!**", parse_mode="Markdown")

@router.message(Command("status"))
async def cmd_status(message: Message):
    user = get_user(message.from_user.id)
    if not user: return
    t_st = "✅" if user.github_token else "❌"
    r_st = f"✅ `{user.github_repo}`" if user.github_repo else "❌"
    c_st = "✅" if user.youtube_cookies else "❌ `Not set`"

    text = f"📊 **Status:**\n\n🔑 **Token:** {t_st}\n📁 **Repo:** {r_st}\n🍪 **Cookies:** {c_st}"
    await message.answer(text, parse_mode="Markdown")