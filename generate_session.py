"""
Run this ONCE locally to get a Telethon string session.
It will ask for your phone number and Telegram code.
The session string will be saved to session_string.txt — open that file and copy from there.
Save it as GitHub Secret: TG_STRING_SESSION
"""
import asyncio
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import TG_API_ID, TG_API_HASH


async def main() -> None:
    async with TelegramClient(StringSession(), TG_API_ID, TG_API_HASH) as client:
        await client.start()
        string = client.session.save()

        out = Path("session_string.txt")
        out.write_text(string, encoding="utf-8")

        print("\n✅ Session saved to session_string.txt")
        print("Open that file in Notepad and copy the string from there.")
        print("Paste it into GitHub Secret: TG_STRING_SESSION")
        print(f"\nLength: {len(string)} characters")


asyncio.run(main())
