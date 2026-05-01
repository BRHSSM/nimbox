import os
import uuid
import asyncio
import re

def sanitize_filename(name):

    return re.sub(r'[^\w\.\-]', '_', name)

async def process_archive(file_path: str, comp_mode: str, password: str, updater):
    updater.action_text = "📦 Processing File"

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    raw_base = os.path.splitext(os.path.basename(file_path))[0]
    ext = os.path.splitext(file_path)[1]

    base_name = sanitize_filename(raw_base)
    unique_id = str(uuid.uuid4())[:8]
    new_base = f"{base_name}_{unique_id}"


    if comp_mode == "raw" and file_size_mb <= 95:
        final_path = os.path.join(os.path.dirname(file_path), f"{new_base}{ext}")
        os.rename(file_path, final_path)
        return [final_path]

    zip_path = os.path.join(os.path.dirname(file_path), f"{new_base}.zip")
    cmd = ["7z", "a", "-tzip", "-mx=9"]


    if file_size_mb > 95:
        cmd.append("-v95m")

    if password and password != "None":
        cmd.append(f"-p{password}")

    cmd.extend([zip_path, file_path])

    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.wait()

    if os.path.exists(file_path): os.remove(file_path)

    dir_name = os.path.dirname(file_path)
    generated_files =[os.path.join(dir_name, f) for f in os.listdir(dir_name) if f.startswith(new_base + ".zip")]
    return sorted(generated_files)