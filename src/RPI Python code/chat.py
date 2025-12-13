import json
import os

# Ordner- und Dateipfad
file_path = "tally/newLaxoutV1/chats/chat.jsonl"

def save_message(dictionary):
    # Nachricht anhängen
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(dictionary, ensure_ascii=False) + "\n")

    print(f'Nachricht "{dictionary["text"]}" gespeichert')



def get_latest_message():
    json = convert_to_json(open(file_path))
    return json[-1]

def convert_to_json(json1):
    final_dict = []
    for line in json1:
        final_dict.append(line)
    
    return final_dict