from service import hexdump
from typing import Optional
from result import StatusCode
from PyQt5 import QtCore, QtGui, QtWidgets
from channel import Client

code_map = {
    StatusCode.SC_OK: '命令成功完成。',
    StatusCode.SC_NEW_MESSAGE: '有新消息。',
    StatusCode.SC_KEY_INVALID: '提供的密钥无效。',
    StatusCode.SC_INVALID_CMD: '无效的客户端命令。',
    StatusCode.SC_NEEDS_LOGIN: '需要登录才能执行此命令。',
    StatusCode.SC_WANDER_ROOM: '您还未进入任何一个房间。',
    StatusCode.SC_DUPLICATE_USER: '您的用户名在当前房间已被占用，导致无法进入此房间。',
    StatusCode.SC_UNAUTHORIZED: '提供的数字签名或加密数据无效。',
    StatusCode.SC_TOO_FREQUENT: '发送的频率太高，请稍后再发送。',
    StatusCode.SC_MSG_TOO_LONG: '消息过长，服务器拒绝接收。'
}

class Ui_MainWindow(object):
    def __init__(self):
        self._client = None
        self._user = None
        self.mainLoopThread = None
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setWindowIcon(QtGui.QIcon('assets\\icon.png'))
        self.mainWindow = MainWindow
        font = QtGui.QFont()
        font.setFamily("Microsoft YaHei UI")
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setEnabled(False)
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(9, 10, 781, 521))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.messages = QtWidgets.QTextBrowser(self.verticalLayoutWidget)
        self.messages.setObjectName("messages")
        messagesFont = QtGui.QFont()
        messagesFont.setFamily("Courier New")
        messagesFont.setPointSize(10)
        self.messages.setFont(messagesFont)
        self.verticalLayout.addWidget(self.messages)
        self.lineCompose = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        self.lineCompose.setObjectName("lineCompose")
        self.lineCompose.setPlaceholderText("在此处输入消息...")
        self.verticalLayout.addWidget(self.lineCompose)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 800, 26))
        self.menuBar.setObjectName("menuBar")
        self.menuConnect = QtWidgets.QMenu(self.menuBar)
        self.menuConnect.setObjectName("menuConnect")
        MainWindow.setMenuBar(self.menuBar)
        self.actionConnectTo = QtWidgets.QAction(MainWindow)
        self.actionConnectTo.setObjectName("actionConnectTo")
        self.menuConnect.addAction(self.actionConnectTo)
        self.actionEnterRoom = QtWidgets.QAction(MainWindow)
        self.actionEnterRoom.setObjectName("actionEnterRoom")
        self.actionEnterRoom.setEnabled(False)
        self.menuConnect.addAction(self.actionEnterRoom)
        self.menuConnect.addSeparator()
        self.actionConnectionInfo = QtWidgets.QAction(MainWindow)
        self.actionConnectionInfo.setObjectName("actionConnectionInfo")
        self.actionConnectionInfo.setEnabled(False)
        self.menuConnect.addAction(self.actionConnectionInfo)
        self.menuBar.addAction(self.menuConnect.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.actionConnectTo.triggered.connect(self.connect)
        self.actionEnterRoom.triggered.connect(self.joinRoom)
        self.actionConnectionInfo.triggered.connect(self.showConnectionInfo)
        self.lineCompose.returnPressed.connect(self.sendMessage)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "聊天窗口"))
        self.label.setText(_translate("MainWindow", "聊天内容："))
        self.menuConnect.setTitle(_translate("MainWindow", "连接 (&C)"))
        self.actionConnectTo.setText(_translate("MainWindow", "连接至... (&T)"))
        self.actionEnterRoom.setText(_translate("MainWindow", "加入聊天室... (&J)"))
        self.actionConnectionInfo.setText(_translate("MainWindow", "连接信息... (&I)"))
    def showConnectionInfo(self):
        message = '连接信息:\n'
        message += '服务器 IP 地址: {}\n服务器端口: {}\n'.format(*self._client.address)
        message += 'ECC 共享密钥:\n{}\nECC 私钥指纹:\n{}\nECC 公钥指纹:\n{}'.format(
            hexdump(self._client.scheme.secret().hex()),
            self._client.scheme.privateKey.export().fingerprint,
            self._client.scheme.publicKey.export().fingerprint
        )
        QtWidgets.QMessageBox.information(self.mainWindow, "连接信息", message)
    def connect(self):
        host, ret = QtWidgets.QInputDialog.getText(self.mainWindow, '连接至服务器', '请输入服务器地址:')
        if not ret: return
        self._client = client = Client(host, 5000)
        try:
            client.connect()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.mainWindow, '连接至 {} 失败。\n{!s}'.format(host, e))
            return
        self.mainLoopThread = MainLoopThread(client)
        self.mainLoopThread.failure.connect(self.displayFailureMessage)
        self.mainLoopThread.message.connect(self.newMessage)
        self.mainLoopThread.start()
        self.actionEnterRoom.setEnabled(True)
        self.actionConnectionInfo.setEnabled(True)
        self.displayMessage('已连接至 {}。您的连接是加密的。'.format(host))
    def joinRoom(self):
        if self._user:
            self._client.leaveRoom()
        user, ret = QtWidgets.QInputDialog.getText(self.mainWindow, '登录服务器', '请输入您的昵称:')
        if not ret:
            return
        room, ret = QtWidgets.QInputDialog.getText(self.mainWindow, '登录服务器', '请输入房间名:')
        if not ret:
            return
        self._user = user
        self._client.login(user)
        self._client.enterRoom(room)
        self.centralwidget.setEnabled(True)
        self.messages.clear()
    def displayFailureMessage(self, code: StatusCode):
        self.statusbar.showMessage('错误: {}'.format(code_map[code]), 2000)
    def displayMessage(self, text: str):
        self.statusbar.showMessage(text, 2000)
    def newMessage(self, user: Optional[str], message: str):
        if user:
            self.messages.append('{}: {}'.format(user, message))
        else:
            self.messages.append(message)
    def sendMessage(self):
        message = self.lineCompose.text().strip()
        if not message: return
        self._client.compose(message)
    def stopClient(self):
        if self._client:
            self._client.close()
        if self.mainLoopThread:
            self.mainLoopThread.wait()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        a0.accept()
        w = a0.size().width() - 20
        h = a0.size().height() - 70
        self.ui.verticalLayoutWidget.resize(w, h)
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        a0.accept()
        self.ui.stopClient()

class MainLoopThread(QtCore.QThread):
    failure = QtCore.pyqtSignal(StatusCode)
    message = QtCore.pyqtSignal(str, str)
    def __init__(self, client: Client):
        super().__init__()
        self._client = client
        self._client.onMessage.register(self.message.emit)
        self._client.onFailure.register(self.failure.emit)
    def run(self) -> None:
        self._client.mainLoop()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    app.exec()