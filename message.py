from typing import Optional
from xml.dom import minidom as dom
import time

class Message:
    'Represents a fragment of message.'
    def __init__(self, user: Optional[str], message: str, timestamp: float):
        'Initializes a new instance.'
        self._user = user
        self._message = message
        self._timestamp = timestamp
    @property
    def user(self) -> Optional[str]:
        'The user who sent this message.'
        return self._user
    @property
    def message(self) -> str:
        'The message text.'
        return self._message
    @property
    def timestamp(self) -> float:
        'The timestamp of this message.'
        return self._timestamp

class MessageManager:
    'Represents a collection of messages.'
    def __init__(self, room_name: str):
        'Initializes with a room name.'
        self._messages = []
        self._roomName = room_name
    def messageReceived(self, user: str, message: str) -> None:
        'Called when a new message occurred.'
        timestamp = time.time()
        self._messages.append(Message(user, message, timestamp))
    def metaMessage(self, message: str) -> None:
        'Called when a meta message was received.'
        timestamp = time.time()
        self._messages.append(Message(None, message, timestamp))
    def exportMessages(self) -> str:
        'Exports the messages as xml.'
        doc = dom.getDOMImplementation().createDocument(None, 'messages', dom.DocumentType('messages'))
        doc.documentElement.setAttribute("room", self._roomName)
        for message in self._messages:
            elem = doc.createElement("message")
            elem.setAttribute("user", message.user)
            elem.setAttribute("timestamp", str(message.timestamp))
            elem.appendChild(
                doc.createTextNode(message.message)
            )
            doc.documentElement.appendChild(elem)
        return doc.toprettyxml(indent='  ')