import os
import sys
from pathlib import Path

# Fake settings so config.py imports without real secrets.
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN_VALUE")
os.environ.setdefault("CHAT_ID", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
