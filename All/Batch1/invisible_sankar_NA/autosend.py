
import asyncio
from telethon import TelegramClient, errors
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'python-dotenv'])
    from dotenv import load_dotenv


env_path = Path(__file__).parent / '.env'
def prompt_and_save_env(phone, api_id, api_hash):
    # Only save if .env does not already have the values
    if env_path.exists():
        # Read existing .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        keys = {line.split('=')[0].strip() for line in lines if '=' in line}
        if all(k in keys for k in ['MOBILE', 'API_ID', 'API_HASH']):
            # Already present, do not overwrite
            return
    with open(env_path, 'w') as f:
        f.write(f"Mobile={phone}\nAPI_ID={api_id}\nAPI_HASH={api_hash}\n")

def get_env_value(var, prompt_text):
    val = os.getenv(var)
    if not val:
        val = input(prompt_text)
    return val

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    phone = os.getenv('Mobile')
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    missing = False
    if not phone:
        phone = input('Enter your phone number (with country code): ')
        missing = True
    if not api_id:
        api_id = input('Enter your API ID: ')
        missing = True
    if not api_hash:
        api_hash = input('Enter your API Hash: ')
        missing = True
    if missing:
        prompt_and_save_env(phone, api_id, api_hash)
    api_id = int(api_id)
else:
    phone = input('Enter your phone number (with country code): ')
    api_id = input('Enter your API ID: ')
    api_hash = input('Enter your API Hash: ')
    prompt_and_save_env(phone, api_id, api_hash)
    api_id = int(api_id)
session_name = 'session'


# --- FETCH FORMATS FROM SAVED MESSAGES ---
async def fetch_formats_from_saved_messages(client, num_formats=3):
    # 'me' is the special entity for Saved Messages
    entity = await client.get_entity('me')
    messages = []
    async for msg in client.iter_messages(entity, limit=num_formats):
        if msg.text and msg.text.strip():
            messages.append(msg.text.strip())
    # Return in chronological order (oldest first)
    return list(reversed(messages))


# --- GROUP LINKS: Will be dynamically fetched each run ---
async def fetch_group_links(client):
    print("[INFO] Fetching joined groups...")
    links = []
    async for dialog in client.iter_dialogs():
        # Only pure groups (not channels, contacts, private, or megagroups-as-channels)
        if getattr(dialog.entity, 'megagroup', False) and dialog.is_group and getattr(dialog.entity, 'username', None):
            link = f"https://t.me/{dialog.entity.username}"
            links.append(link)
    print(f"[INFO] Found {len(links)} groups.")
    return links

async def fetch_and_print_groups(client):
    print("[INFO] Fetching joined groups...")
    links = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group and getattr(dialog.entity, 'username', None):
            link = f"https://t.me/{dialog.entity.username}"
            links.append(link)
            print(link)
    print(f"[INFO] Found {len(links)} groups. Copy these into groupLinks for future runs.")
    return links


KEYWORDS = [
    "proxy support",
    "interview support",
    "interview",
    "interview help",
    "support available",
    "proxy",
    "assessment",
    "exam",
    "test",
    "8106368645",
]

async def send_messages(client, group_links, formats, interval=600):
    last_format = -1
    round_num = 1
    skip_numbers = ["78148_37019", "𝗗𝗠_𝗧𝗢_𝗞𝗡𝗢𝗪_𝗠𝗢𝗥𝗘","8271737924","82_717379_24", "9133817162", "9885074380", "7093493173", "919133817162", "919885074380", "917093493173", "9133_81_7162", "98850_74380", "7093_49_3173"]  # Add more numbers to skip if needed 
    while True:
        results = []
        for idx, group in enumerate(group_links, 1):
            # Skip sending to Saved Messages itself
            if group == 'https://t.me/SavedMessages' or group.lower() == 'me':
                continue
            last_format = (last_format + 1) % len(formats)
            message_to_send = formats[last_format]
            # Fetch last message in the group
            last_msg = None
            try:
                async for msg in client.iter_messages(group, limit=1):
                    last_msg = msg.text.strip() if msg.text else None
                    break
            except Exception as e:
                print(f"{idx}. {group}: ERROR fetching last message: {e}")
                continue
            if last_msg:
                has_keyword = any(keyword in last_msg.lower() for keyword in KEYWORDS)
                msg_length = len(last_msg)
            else:
                has_keyword = False
                msg_length = 0
            # Skip if last message contains any of the skip_numbers
            if last_msg and any(num in last_msg for num in skip_numbers):
                print(f"{idx}. SKIPPED  {group}")
                continue
            if last_msg and last_msg == message_to_send:
                print(f"{idx}. SKIPPED  {group}")
                continue
            if msg_length <= 250 and not has_keyword:
                print(f"{idx}. SKIPPED  {group}")
                continue
            try:
                await client.send_message(group, message_to_send)
                status = "_/"
            except errors.FloodWaitError as e:
                status = "X"
                await asyncio.sleep(e.seconds)
            except Exception as e:
                status = "X"
            results.append((group, status))
            print(f"{idx}. {status}       {group}")
            import random
            gap = random.randint(1, 5)  # Random gap after each message to mimic human behavior
            # print(f"[INFO] Waiting {gap} seconds before next message...")
            await asyncio.sleep(gap)  # Random delay between 1 and 5 seconds
        import random
        wait_time = random.randint(0, 1800) # Random delay between 0 and 30 minutes before next round
        print(f"[INFO] Waiting {wait_time} seconds before next round...\n")
        round_num += 1
        await asyncio.sleep(wait_time)


async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start(phone=phone)
    groupLinks = await fetch_group_links(client)
    # Deduplicate group links while preserving order
    seen = set()
    unique_groupLinks = []
    for link in groupLinks:
        if link not in seen:
            unique_groupLinks.append(link)
            seen.add(link)
    if not unique_groupLinks:
        print("[WARN] No groups found. Join some groups and try again.")
        return
    # Fetch formats from Saved Messages, fallback to default if none found
    formats = await fetch_formats_from_saved_messages(client, num_formats=3)
    if not formats:
        print("[WARN] No formats found in Saved Messages. Please add some messages there.")
        return
    await send_messages(client, unique_groupLinks, formats)

if __name__ == '__main__':
    asyncio.run(main())
