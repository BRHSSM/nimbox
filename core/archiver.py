import os
import uuid
import asyncio

async def process_archive(file_path: str, comp_mode: str, password: str, updater):
    updater.action_text = "📦 Processing File"

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    unique_id = str(uuid.uuid4())[:8]
    new_base = f"{base_name}_{unique_id}"


    if comp_mode == "raw" and file_size_mb <= 95:
        final_path = os.path.join(os.path.dirname(file_path), f"{new_base}{os.path.splitext(file_path)[1]}")
        os.rename(file_path, final_path)
        return [final_path]


    zip_path = os.path.join(os.path.dirname(file_path), f"{new_base}.zip")
    cmd = ["7z", "a", "-tzip", "-mx=9"]

    if password and password != "None":
        cmd.append(f"-p{password}")

    cmd.extend([zip_path, file_path])

    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.wait()

    if os.path.exists(file_path): os.remove(file_path)
    return [zip_path]