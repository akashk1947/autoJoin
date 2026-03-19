import asyncio
import random
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest

# ========= TELEGRAM API =========
api_id = 36241411
api_hash = "a9881ac2cca3e9fc13f0948bb04e674c"
session_name = "session"

# ========= TIMING =========
BATCH_SIZE = 5
SHORT_WAIT = (300, 600)   # 5 between joins
LONG_WAIT = 500           # 5 minutes rest after batch

# ========= LOAD GROUPS =========
with open("groups.txt", "r", encoding="utf-8") as f:
    groups = [g.strip() for g in f if g.strip()]

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    join_count = 0
    batch_count = 0

    print(f"🚀 Join started (total groups: {len(groups)})")

    for idx, group in enumerate(groups, start=1):
        try:
            print(f"➡️ RajRajak_[{idx}/{len(groups)}] Joining: {group}")
            await client(JoinChannelRequest(group))

            join_count += 1
            batch_count += 1
            print(f"✅ Joined total: {join_count}")

            # Random 5–10 minute wait
            await asyncio.sleep(random.randint(*SHORT_WAIT))

            # Batch rest: fixed 10 minutes
            if batch_count >= BATCH_SIZE:
                print("😴 Batch complete. Resting 5 minutes")
                await asyncio.sleep(LONG_WAIT)
                batch_count = 0

        except FloodWaitError as e:
            print(f"⛔ JOIN FLOODWAIT: {e.seconds//60} minutes")
            print("🛑 Stopping immediately to protect account")
            break

        except Exception as e:
            print(f"⚠️ Error joining {group}: {e}")
            # brief pause, then continue to next group
            await asyncio.sleep(60)

    await client.disconnect()
    print("🏁 Script finished")

asyncio.run(main())
