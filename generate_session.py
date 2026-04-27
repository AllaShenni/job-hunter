"""
Run this ONCE locally to get a Telethon string session.
It will ask for your phone number and Telegram code.
Copy the printed string and save it as GitHub Secret: TG_STRING_SESSION
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import TG_API_ID, TG_API_HASH


async def main() -> None:
    async with TelegramClient(StringSession(), TG_API_ID, TG_API_HASH) as client:
        await client.start()
        string = client.session.save()
        print("\n=== YOUR STRING SESSION (copy everything on the next line) ===")
        print(string)
        print("=== END ===\n")
        print("Save this as GitHub Secret named: TG_STRING_SESSION")


asyncio.run(main())
