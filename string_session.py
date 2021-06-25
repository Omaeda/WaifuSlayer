from telethon.sync import TelegramClient
from telethon.sessions import StringSession


def main():
    api_id = int(input("api_id: "))
    api_hash = input("api_hash: ")

    with TelegramClient(StringSession(), api_id=api_id, api_hash=api_hash) as client:
        string = client.session.save()
        client.send_message("me", string)
        print("Se envio el string session a los mensajes guardados")


if __name__ == "__main__":
    main()
