import asyncio
import random
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest

# ========= TELEGRAM API =========
Mobile = "+919052212885"
api_id = 34325371
api_hash = "d2ebefde9777256d081f54cb79cdc05d"

session_name = "session"

# ========= TIMING =========
BATCH_SIZE = 4
SHORT_WAIT = (150, 300)   # 2.5-5 minutes between joins
LONG_WAIT = 300           # 5 minutes rest after batch

# ========= LOAD GROUPS =========
with open("groups.txt", "r", encoding="utf-8") as f:
    groups = [g.strip() for g in f if g.strip()]

async def main():
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start()

    joined = set()
    while True:
        join_count = 0
        batch_count = 0
        print(f"🚀 Join started (total groups: {len(groups)})")

        for idx, group in enumerate(groups, start=1):
            if group in joined:
                continue
            try:
                print(f"➡️ RajRajak_[{idx}/{len(groups)}] Joining: {group}")
                await client(JoinChannelRequest(group))

                join_count += 1
                batch_count += 1
                joined.add(group)
                print(f"✅ Joined total: {join_count}")

                # Random 2.5–5 minute wait
                await asyncio.sleep(random.randint(*SHORT_WAIT))

                # Batch rest: fixed 5 minutes
                if batch_count >= BATCH_SIZE:
                    print("😴 Batch complete. Resting 5 minutes")
                    await asyncio.sleep(LONG_WAIT)
                    batch_count = 0

            except FloodWaitError as e:
                wait_seconds = e.seconds % 60
                wait_minutes = e.seconds // 60
                wait_hours = wait_minutes // 60
                wait_minutes = wait_minutes % 60
                print(f"⛔ JOIN FLOODWAIT: {wait_hours} : {wait_minutes} : {wait_seconds}")
                await asyncio.sleep(e.seconds + 5)  # add a buffer
                print("🔄 Resuming join process after flood wait.")
                break  # break inner for-loop, restart outer while-loop


            except Exception as e:
                print(f"⚠️ Error joining {group}: {e}")
                # brief pause, then continue to next group
                await asyncio.sleep(60)

        if len(joined) == len(groups):
            print("🏁 All groups joined. Sleeping 1 hour before checking again.")
            await asyncio.sleep(300)
            # Optionally, reload groups.txt here if you want to pick up new groups
        else:
            print("🔄 Not all groups joined, restarting join loop.")

    await client.disconnect()
    print("🏁 Script finished")

asyncio.run(main())
