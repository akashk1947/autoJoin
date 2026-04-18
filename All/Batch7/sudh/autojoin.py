import asyncio
import random
import os
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest

# ========= TELEGRAM API =========
Mobile = "+6283175615708"
api_id = 35001004
api_hash = "65f4e46a5842cdb7892da507bce98426"
session_name = Mobile.lstrip('+')

# ========= TIMING =========
BATCH_SIZE = 5
SHORT_WAIT = (60, 300)   # 1-5 minutes
LONG_WAIT = 1200         # 20 minutes rest

# ========= FILES =========
GROUPS_FILE = "groups.txt"
JOINED_FILE = "joined.txt"
FAILED_FILE = "FailedToJoin.txt"

def get_history(file_path, is_comma=True):
    """Generic loader for history files to prevent duplicates."""
    if not os.path.exists(file_path):
        return set()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        if is_comma:
            return {item.strip().lower() for item in content.split(',') if item.strip()}
        else:
            # For FailedToJoin.txt, we extract just the URL part
            links = set()
            for line in content.splitlines():
                if ". " in line:
                    links.add(line.split(". ")[1].split(" |")[0].strip().lower())
            return links

def log_failed(link, reason):
    """Logs failed attempts with numbering if not already there."""
    current_fails = get_history(FAILED_FILE, is_comma=False)
    if link.lower() in current_fails:
        return
    
    count = 0
    if os.path.exists(FAILED_FILE):
        with open(FAILED_FILE, "r") as f:
            count = sum(1 for line in f if line.strip())
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{count + 1}. {link} | Error: {reason}\n")

def log_joined(link):
    """Appends successful join to joined.txt if not already there."""
    current_joined = get_history(JOINED_FILE)
    if link.lower() in current_joined:
        return
    with open(JOINED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{link},\n")

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start(Mobile)
    
    # --- 1. INITIALIZE SKIP LISTS ---
    joined_list = get_history(JOINED_FILE)
    failed_list = get_history(FAILED_FILE, is_comma=False)
    print(f"📄 History: {len(joined_list)} joined, {len(failed_list)} failed.")

    print("🔄 Syncing live account data...")
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                entity = dialog.entity
                if hasattr(entity, 'username') and entity.username:
                    joined_list.add(entity.username.lower())
    except Exception as e:
        print(f"⚠️ Sync Note: {e}")
    
    # --- 2. LOAD TARGET GROUPS ---
    if not os.path.exists(GROUPS_FILE):
        print(f"❌ {GROUPS_FILE} not found!")
        return
    
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        all_groups = [g.strip() for g in f if g.strip()]

    join_count = 0
    batch_count = 0

    print(f"🚀 Processing {len(all_groups)} links...")

    for idx, group_link in enumerate(all_groups, start=1):
        clean_name = group_link.split('/')[-1].lower() if '/' in group_link else group_link.lower()

        # --- SMART SKIP (Joined, Previously Failed, or Duplicate in same run) ---
        if group_link.lower() in joined_list or clean_name in joined_list:
            continue
        if group_link.lower() in failed_list:
            print(f"⏩ Skipping {group_link} (Previously marked as Failed)")
            continue

        try:
            print(f"➡️ [{idx}/{len(all_groups)}] Joining: {group_link}")
            await client(JoinChannelRequest(group_link))
            
            # Normal Success
            log_joined(group_link)
            joined_list.add(clean_name)
            join_count += 1
            batch_count += 1
            print(f"✅ Joined! Total: {join_count}")
            await asyncio.sleep(random.randint(*SHORT_WAIT))

        except Exception as e:
            err = str(e)
            # Handle Join Requests / Already In / Flood
            if "USER_ALREADY_PARTICIPANT" in err:
                log_joined(group_link)
                joined_list.add(clean_name)
                print(f"ℹ️ Already in {group_link}.")
            elif "successfully requested to join" in err:
                log_joined(group_link)
                joined_list.add(clean_name)
                print(f"📩 Join Request Sent for {group_link}.")
                await asyncio.sleep(random.randint(*SHORT_WAIT))
            elif isinstance(e, FloodWaitError):
                print(f"⛔ FLOODWAIT: {e.seconds}s.")
                await asyncio.sleep(e.seconds + 5)
            else:
                print(f"⚠️ Failed: {group_link}")
                log_failed(group_link, err)
                failed_list.add(group_link.lower()) # Add to local skip for this session
                await asyncio.sleep(10)

        if batch_count >= BATCH_SIZE:
            print(f"😴 Batch done. Resting 20 mins...")
            await asyncio.sleep(LONG_WAIT)
            batch_count = 0

    await client.disconnect()
    print("🏁 Finished.")

if __name__ == "__main__":
    asyncio.run(main())