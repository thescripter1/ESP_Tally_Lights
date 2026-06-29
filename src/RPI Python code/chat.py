import json
from pathlib import Path

# Ordner- und Dateipfad
BASE_DIR = Path(__file__).resolve().parent
CHAT_FILE = BASE_DIR / "chats" / "chat.jsonl"

def save_message(dictionary):
    # Nachricht anhängen
    CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHAT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dictionary, ensure_ascii=False) + "\n")

    print(f'Nachricht "{dictionary["text"]}" gespeichert')



def get_latest_message():
    if not CHAT_FILE.exists():
        return None

    with CHAT_FILE.open("r", encoding="utf-8") as f:
        messages = convert_to_json(f)

    return messages[-1] if messages else None

def convert_to_json(json1):
    final_dict = []
    for line in json1:
        final_dict.append(line)
    
    return final_dict
