from threading import Thread
import time
from typing import Tuple
from room import Room
from structsock import StructuredSocket, PeerDisconnect
from service import log, Signal
from result import Status, StatusCode
import elite, msgpack, queue

MINIMUM_BETWEEN = 1

class Session:
    'Represents a session to communicate with the client.'
    def __init__(self, client: StructuredSocket, server: 'Server'):
        'Initializes with a client and a server.'
        self._user = None
        self._scheme = elite.getscheme()
        self._client = client
        self._server = server
        self._room = None
        self._lastTimestamp = 0
    def lifecycle(self, multithread: bool=False) -> None:
        'Runs the lifecycle, either in this thread or in another.'
        if multithread:
            t = Thread(name='Session-{}:{}'.format(*self._client.getpeername()), target=self.lifecycle)
            t.start()
            return
        try:
            self._handshake()
            self._main()
        except PeerDisconnect: pass
        log("会话结束。")
        if self._room:
            self._room.userLeft(self._user)
            self._room.metaMessage('{} 离开了房间。'.format(self._user))
            self._room = None
        self._server.sessionExit(self)
    def _send(self, status: Status, encrypt: bool=True):
        'Sends the specific status.'
        data = status.pack()
        if encrypt:
            data = self._scheme.encrypt(data)
        self._client.send(data)
    def _handshake(self) -> None:
        'Handshakes with the client.'
        while True:
            key = self._client.recv()
            try:
                self._scheme.importBinaryKey(key)
                self._send(Status.ok(self._scheme.exportBinaryKey()), False)
                break
            except elite.secret.CurveKindMismatch:
                self._send(
                    Status(StatusCode.SC_KEY_INVALID), False
                )
        log("密钥协商完毕。共享密钥为 {}".format(self._scheme.secret().hex()))
    def _main(self) -> None:
        'The main loop of the session.'
        while True:
            data = self._client.recv()
            try:
                data = self._scheme.decrypt(data)
            except elite.cipher.AuthorizationCodeInvalid:
                self._send(
                    Status(StatusCode.SC_UNAUTHORIZED)
                )
                continue
            data = msgpack.unpackb(data)
            op = data['type']
            if op == 'login':
                self._user = data['user']
                self._send(Status.ok())
            elif op == 'join':
                if self._user is None:
                    self._send(Status(StatusCode.SC_NEEDS_LOGIN))
                else:
                    self._room = self._server.getRoom(data['room'])
                    if self._room.userJoined(self._user):
                        self._room.onMessage.register(self._message)
                        self._send(Status.ok())
                        self._room.metaMessage('{} 加入了房间。'.format(self._user))
                    else:
                        self._send(Status(StatusCode.SC_DUPLICATE_USER))
            elif op == 'send':
                if self._room is None:
                    self._send(Status(StatusCode.SC_WANDER_ROOM))
                elif time.time() - self._lastTimestamp <= MINIMUM_BETWEEN:
                    self._send(Status(StatusCode.SC_TOO_FREQUENT))
                else:
                    message = data['message']
                    signature = data['signature']
                    if not self._scheme.verify(message.encode(), signature):
                        self._send(Status(StatusCode.SC_UNAUTHORIZED))
                    else:
                        self._room.messageReceived(self._user, message)
                        self._lastTimestamp = time.time()
                        self._send(Status.ok())
            elif op == 'leave':
                if self._room is None:
                    self._send(Status(StatusCode.SC_WANDER_ROOM))
                else:
                    self._room.userLeft(self._user)
                    self._room.onMessage.deregister(self._message)
                    self._room.metaMessage('{} 离开了房间。'.format(self._user))
                    self._room = None
                    self._send(Status.ok())
            elif op == 'quit':
                if self._room is not None:
                    self._room.userLeft(self._user)
                    self._room.onMessage.deregister(self._message)
                    self._room.metaMessage('{} 离开了房间。'.format(self._user))
                    self._room = None
                self._client.close()
                break
            else:
                self._send(Status(StatusCode.SC_INVALID_CMD))
    def _message(self, user: str, message: str) -> None:
        'Called when a new message was sent.'
        self._send(Status.message((user, message)))

class Server:
    'Represents the server to manage the connections.'
    def __init__(self, port: int):
        'Initializes the server with specific port.'
        self._sock = StructuredSocket()
        self._sock.bind(('0.0.0.0', port))
        self._port = port
        self._sessions = set()
        self._rooms = {}
    def sessionExit(self, session: Session):
        'Called when a session exits.'
        self._sessions.remove(session)
    def serve(self, multithread: bool=False) -> None:
        'Launches the server.'
        if multithread:
            t = Thread(name='ServerDaemon', target=self.serve, daemon=True)
            t.start()
            return
        log('正在监听 0.0.0.0:{}'.format(self._port))
        self._sock.listen(5)
        while True:
            client, addr = self._sock.accept()
            log('客户端 {}:{} 已连接'.format(*addr))
            session = Session(client, self)
            self._sessions.add(session)
            session.lifecycle(True)
    def getRoom(self, name: str) -> Room:
        'Gets a room with specific name.'
        try:
            return self._rooms[name]
        except KeyError:
            room = Room(name)
            self._rooms[name] = room
            return room

class Client:
    'Represents a client.'
    def __init__(self, host: str, port: int):
        'Initializes with specific host and port.'
        self._address = (host, port)
        self._scheme = elite.getscheme()
        self._sock = StructuredSocket()
        self.onMessage = Signal()
        self.onFailure = Signal()
        self._queue = queue.Queue()
    @property
    def address(self) -> Tuple[str, int]:
        'Gets the address of the peer.'
        return self._address
    @property
    def scheme(self) -> elite.scheme.ECCScheme:
        'Gets the security scheme.'
        return self._scheme
    def connect(self) -> None:
        self._sock.connect(self._address)
        while True:
            self._sock.send(self._scheme.exportBinaryKey())
            stat = Status.unpack(self._sock.recv())
            if stat.success:
                self._scheme.importBinaryKey(stat.data)
                break
        self._sock.setblocking(False)
    def enqueue(self, operation: dict) -> None:
        'Pushes an operation to the message queue.'
        self._queue.put(operation)
    def enterRoom(self, room: str) -> None:
        'Enters a room with specific name.'
        self.enqueue({
            'type': 'join',
            'room': room
        })
    def leaveRoom(self) -> None:
        'Leaves the current room.'
        self.enqueue({
            'type': 'leave'
        })
    def login(self, user: str) -> None:
        'Logs in as specific user.'
        self.enqueue({
            'type': 'login',
            'user': user
        })
    def compose(self, message: str) -> None:
        'Composes a message and send it.'
        signature = self._scheme.sign(message.encode())
        self.enqueue({
            'type': 'send',
            'message': message,
            'signature': signature
        })
    def close(self) -> None:
        'Closes this client.'
        self.enqueue({
            'type': 'quit'
        })
    def mainLoop(self, multithread: bool=False) -> None:
        'Runs the main loop.'
        if multithread:
            t = Thread(name='ClientMainLoop', target=self.mainLoop, daemon=True)
            t.start()
            return
        try:
            while True:
                try:
                    stat = Status.unpack(
                        self._scheme.decrypt(self._sock.recv())
                    )
                    if stat.code == StatusCode.SC_NEW_MESSAGE:
                        self.onMessage(*stat.data)
                    elif not stat.success:
                        self.onFailure(stat.code)
                except BlockingIOError:
                    pass
                try:
                    operation = self._queue.get_nowait()
                    data = msgpack.packb(operation)
                    data = self._scheme.encrypt(data)
                    self._sock.send(data)
                except queue.Empty:
                    pass
        except PeerDisconnect:
            pass
        finally:
            self._sock.close()