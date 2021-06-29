import logging
import shutil
import os
import json
import requests
from bs4 import BeautifulSoup as bs
from decouple import config
from saucenao_api import SauceNao
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import PeerUser

logging.basicConfig(
    format='%(filename)s:%(lineno)s - %(levelname)s: %(message)s', level=logging.INFO)

print("Iniciando...")

try:
    api_id = config("API_ID", cast=int)
    api_hash = config("API_HASH")
    string_session = config("STRING_SESSION")
    capture_text = config("CAPTURE_TEXT")
    sauce_api = config("SAUCENAO_API")
    bot = TelegramClient(StringSession(string_session), api_id, api_hash)
except:
    print("Faltan las variables de entorno")
    exit()

sauce = SauceNao(sauce_api)

data = {
    "chat_id": False,
    "bot_id": False,
    "message_text": False,
    "activated": False
}


@bot.on(events.NewMessage(pattern=r"^cazar ?(.*)?", outgoing=True))
async def _(event):
    args = event.pattern_match.group(1)
    if args:
        if args == "si":
            data["activated"] = True
        if args == "no":
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
    if not event.media:
        return
    if not data["message_text"] == event.text:
        return
    if not event.chat_id == data["chat_id"]:
        return
    if not isinstance(event.message.from_id, PeerUser):
        return
    if not event.message.from_id.user_id == data["bot_id"]:
        return
    dl = await bot.download_media(event.media, "resources/")
    with open(dl, "rb") as file:
        resultados = sauce.from_file(file)
    if not resultados:
        return logging.info("No se encontraron resultados")
    # print(len(resultados))
    for xoxxo in resultados:
        name = xoxxo.raw.get("data").get("characters")
        if name:
            return await bot.send_message(event.chat_id, f"/{capture_text} {name}")
        # return print(xoxxo.raw["data"]["characters"])
        # if "characters" in xoxxo.raw.keys():
        #     return print(xoxxo.raw["characters"])
    # file = {"encoded_image": (dl, open(dl, "rb"))}
    # grs = requests.post(
    #     "https://www.google.com/searchbyimage/upload", files=file, allow_redirects=False
    # )
    # loc = grs.headers.get("Location")
    # response = requests.get(
    #     loc,
    #     headers={
    #         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0"
    #     },
    # )
    # xx = bs(response.text, "html.parser")
    # div = xx.find_all("div", {"class": "r5a77d"})[0]
    # alls = div.find("a")
    # text = alls.text
    # for name in text.split():
    #     await bot.send_message(event.chat_id, f"/{capture_text} {name}")
    try:
        shutil.rmtree(f"{os.getcwd()}/resources")
    except:
        logging.exception("Error al remover el archivo descargado")
        pass


with bot:
    print("Bot iniciado correctamente")
    bot.run_until_disconnected()
