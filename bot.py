import logging

import requests
from bs4 import BeautifulSoup as bs
from decouple import config
from telethon import TelegramClient, events
from telethon.sessions import StringSession

logging.basicConfig(
    format='%(filename)s:%(lineno)s - %(levelname)s: %(message)s', level=logging.INFO)

print("Iniciando...")

try:
    api_id = config("API_ID", cast=int)
    api_hash = config("API_HASH")
    string_session = config("STRING_SESSION")
    capture_text = config("CAPTURE_TEXT")
    bot = TelegramClient(StringSession(string_session), api_id, api_hash)
except:
    print("Faltan las variables de entorno")
    exit()

data = {
    "chat_id": False,
    "bot_id": False,
    "message_text": False,
    "activated": False
}


@bot.on(events.NewMessage(pattern=r"^a ?(.*)?", outgoing=True))
async def _(event):
    args = event.pattern_match.group(1)
    if args:
        if args == "on":
            data["activated"] = True
        if args == "off":
            data["activated"] = False
    if event.is_reply:
        reply = await event.get_reply_message()
        data["chat_id"] = event.chat_id
        data["bot_id"] = reply.from_id.user_id
        data["message_text"] = reply.text
        data["activated"] = True
    print("Activo:", data["activated"], "\nChat ID:", data["chat_id"], "\nBot ID:", data["bot_id"])


@bot.on(events.NewMessage(incoming=True))
async def _(event):
    if not data["activated"]:
        return
    if not event.message.from_id.user_id == data["bot_id"]:
        return
    if not event.chat_id == data["chat_id"]:
        return
    if not event.media:
        return
    if not data["message_text"] == event.text:
        return
    dl = await bot.download_media(event.media, "resources/")
    file = {"encoded_image": (dl, open(dl, "rb"))}
    grs = requests.post(
        "https://www.google.com/searchbyimage/upload", files=file, allow_redirects=False
    )
    loc = grs.headers.get("Location")
    response = requests.get(
        loc,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0"
        },
    )
    xx = bs(response.text, "html.parser")
    div = xx.find_all("div", {"class": "r5a77d"})[0]
    alls = div.find("a")
    text = alls.text
    await bot.send_message(event.chat_id, f"/{capture_text} {text}")


with bot:
    print("Bot iniciado correctamente")
    bot.run_until_disconnected()
