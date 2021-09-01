import os
from libgen_api import LibgenSearch
import requests
from urllib.parse import urlparse
from telethon import TelegramClient, events
import dotenv
dotenv.load()
api_id = dotenv.get('api_id')
api_hash = dotenv.get('api_hash')
bot_token = dotenv.get('bot_token')
s = LibgenSearch()
currentResults = dict()
result_limit = 10
lastestRequest = dict()
def getBooks(name, userID):
    global currentResults
    results = s.search_title(name)
    currentResults[userID] = list()
    for element in results[:10]:
        item_to_download = element
        download_links = s.resolve_download_links(item_to_download)
        if len(download_links) > 0:
            currentElement = dict()
            currentElement["Title"] = element['Title']
            currentElement["Link"] = download_links['GET']
            
            currentResults[userID].append(currentElement)
    return currentResults[userID]

def getResultsText(results):
    textRes = ""
    index = 1
    for element in results:
        textRes += str(index) + ") " + element["Title"] + "\n"
        index += 1
    return textRes

botClient = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

def is_integer(n):
    try:
        int(n)
        return True
    except ValueError:
        return False

async def fetchAndSendBooks(input, sender, chatID, messageToEditID):
    books = getBooks(input, sender)
    results = getResultsText(books)
    #await botClient.edit_message(event.chat_id, response,"Found")
    if len(books) == 0:
        await botClient.edit_message(chatID, messageToEditID,"No results found.")
    else:
        await botClient.edit_message(chatID, messageToEditID, results)

@botClient.on(events.MessageEdited(incoming=True))
async def onEdit(event):
    if lastestRequest[event.sender.id]["recievedMessage"] == event.message.id:
        editNotification = await botClient.send_message(event.chat_id, "Edit detected, hold on.")
        await fetchAndSendBooks(event.message.message, event.sender.id, event.chat_id, lastestRequest[event.sender.id]["sentMessageID"])
        await botClient.delete_messages(event.chat_id, editNotification)

@botClient.on(events.NewMessage(incoming=True))
async def onMessage(event):
    message = event.raw_text
    if is_integer(message) and int(message) > 0 and int(message) <= result_limit:
        url = currentResults[event.sender.id][int(message) - 1]["Link"]
        a = urlparse(url)
        file = requests.get(url)
        uploaded_file = await botClient.upload_file(file.content, file_name=os.path.basename(a.path))
        await botClient.send_file(event.chat_id, uploaded_file)
    else:
        #print(event)
        response = await event.reply("Searching...")
        print(message)
        lastestRequest[event.sender.id] = dict ({"recievedMessage" : event.id, "sentMessageID": response.id})
        await fetchAndSendBooks(message, event.sender.id, event.chat_id, response.id)
    
botClient.start()
botClient.run_until_disconnected()