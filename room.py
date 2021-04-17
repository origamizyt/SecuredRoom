from message import MessageManager
from service import Signal

class Room(MessageManager):
    'Represents a chat room.'
    def __init__(self, name: str):
        'Initializes a new instance.'
        super().__init__(name)
        self._users = set()
        self.onMessage = Signal()
    def userJoined(self, user: str) -> bool:
        'Called when a new user joined the room.'
        if user in self._users: return False
        self._users.add(user)
        return True
    def userLeft(self, user: str) -> None:
        'Called when a user left the room.'
        try:
            self._users.remove(user)
        except ValueError: pass
    def messageReceived(self, user: str, message: str) -> None:
        'Called when a message was received.'
        super().messageReceived(user, message)
        self.onMessage(user, message)
    def metaMessage(self, message: str) -> None:
        'Called when a meta message was received.'
        super().metaMessage(message)
        self.onMessage(None, message)