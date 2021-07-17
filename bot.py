import asyncio
import logging
import os
import shutil
import time

import requests
from bs4 import BeautifulSoup as bs
from decouple import config
from saucenao_api import SauceNao
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import PeerUser

logging.basicConfig(
    format='%(filename)s:%(lineno)s - %(levelname)s: %(message)s', level=logging.INFO)

logging.info("Iniciando...")

try:
    api_id = config("API_ID", cast=int)
    api_hash = config("API_HASH")
    string_session = config("STRING_SESSION")
    sauce_api = config("SAUCENAO_API")
    bot = TelegramClient(StringSession(string_session), api_id, api_hash)
except:
    logging.error("Faltan las variables de entorno")
    exit()

sauce = SauceNao(sauce_api)

data = {
    "chat_id": False,
    "bot_id": False,
    "message_text": False,
    "activated": False,
    "method": "saucenao",
    "sleep": 5,
    "c_word": "guess"
}

added = False


@bot.on(events.NewMessage(pattern=r"^(?:cazar) ?(\w+)? ?(.*)?", outgoing=True))
async def _(event):
    args = event.pattern_match.group(1)
    args2 = event.pattern_match.group(2)
    if args:
        if args == "si":
            data["activated"] = True
        elif args == "no":
            data["activated"] = False
        elif args in ("google", "saucenao"):
            data["method"] = args
        elif args2:
            if args == "esperar":
                try:
                    data["sleep"] = int(args2)
                except:
                    pass
            elif args == "palabra":
                data["c_word"] = args2

    if event.is_reply:
        reply = await event.get_reply_message()
        data["chat_id"] = event.chat_id
        data["bot_id"] = reply.from_id.user_id
        data["message_text"] = reply.text
        data["activated"] = True
    logging.info(f'Activo: {data["activated"]}\nChat ID: {data["chat_id"]}\nBot ID: {data["bot_id"]}')


@bot.on(events.NewMessage(incoming=True))
async def _(event):
    global added

    if not data["activated"]:
        return
    if not event.chat_id == data["chat_id"]:
        return
    if not isinstance(event.message.from_id, PeerUser):
        return
    if not event.message.from_id.user_id == data["bot_id"]:
        return
    if "added" in event.text:
        added = True
    else:
        added = False


@bot.on(events.NewMessage(incoming=True))
async def _(event):
    start = time.perf_counter()
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

    global added
    name = []
    dl = await bot.download_media(event.media, "resources/")

    # hacer busqueda reversa
    if data["method"] == "google":
        text = await google(dl)
        name = text.split()
    else:
        text = await sauce_nao(dl)
        if text:
            text = text.split()[0]
            name.append(text)
    
    if name == []:
        logging.info("No se encontro el nombre")
        return
    
    # comprobar que no fue atrapada y atrapar
    if not added:
        end = time.perf_counter()
        sleep_time = await calc_sleep(start, end)
        await asyncio.sleep(sleep_time)

        msg = await bot.send_message(event.chat_id, f"/{data['c_word']} {name[0]}")
        if msg:
            for x in name[1:]:
                await asyncio.sleep(2)                           # TODO: controlar que no se sigan editando los
                await msg.edit(f"/{data['c_word']} {x}")         #  mensajes luego de enviar la respuesta correcta
    else:
        logging.info("Ya fue atrapada")

    try:
        shutil.rmtree(f"{os.getcwd()}/resources")
    except:
        logging.exception("Error al remover el archivo descargado")
        pass


async def google(dl):
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

    return alls.text


async def sauce_nao(dl):
    with open(dl, "rb") as file:
        resultados = sauce.from_file(file)
    if not resultados:
        return  # logging.info("No se encontraron resultados")
    # print(len(resultados))
    for xoxxo in resultados:
        name = xoxxo.raw.get("data").get("characters")
        if name:
            return name
        # return print(xoxxo.raw["data"]["characters"])


async def calc_sleep(start, end):
    t_spent = end - start
    if t_spent >= data["sleep"]:
        return 0
    return data["sleep"] - t_spent


if __name__ == '__main__':
    with bot:
        logging.info("Bot iniciado correctamente")
        bot.run_until_disconnected()


# TODO: añadir texto de ayuda
