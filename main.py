import asyncio
import sys
from random import randint

import requests
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from qasync import QEventLoop, asyncSlot

from vndb.VNDB import VNDB





class Main(QWidget):
    def __init__(self,parent):
        super(Main,self).__init__()
        self.parent = parent
        self.api = VNDB(prefer_languages=["zh"])
        self.setupUi(parent)
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1067, 600)
        self.setGeometry(QtCore.QRect(10, 0, 1051, 531))
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.main_title = QtWidgets.QLabel(parent=self)
        self.main_title.setTextFormat(QtCore.Qt.TextFormat.AutoText)
        self.main_title.setObjectName("main_title")
        self.gridLayout.addWidget(self.main_title, 0, 0, 1, 10)
        self.progressBar = QtWidgets.QProgressBar(parent=self)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 10)
        self.current_working = QtWidgets.QLabel(parent=self)
        self.current_working.setTextFormat(QtCore.Qt.TextFormat.AutoText)
        self.current_working.setObjectName("current_working")
        self.gridLayout.addWidget(self.current_working, 2, 0, 1, 10)
        self.searchbar = QtWidgets.QLineEdit(parent=self)
        self.searchbar.setObjectName("searchbar")
        self.gridLayout.addWidget(self.searchbar, 3, 0, 1, 7)
        self.searchbutton = QtWidgets.QPushButton(parent=self)
        self.searchbutton.setObjectName("searchbutton")
        self.gridLayout.addWidget(self.searchbutton, 3, 7, 1, 3)
        self.search_result = QtWidgets.QComboBox(parent=self)
        self.search_result.setObjectName("search_result")
        self.gridLayout.addWidget(self.search_result, 4, 0, 1, 10)
        self.result_title = QtWidgets.QLabel(parent=self)
        self.result_title.setObjectName("result_title")
        self.result_title.setWordWrap(True)
        self.gridLayout.addWidget(self.result_title, 5, 0, 1, 7)
        # self.result_image = QtWidgets.QGraphicsView(parent=self)
        self.result_image = QtWidgets.QLabel(parent=self)
        self.result_image.setObjectName("result_image")
        self.gridLayout.addWidget(self.result_image, 5, 7, 7, 3)
        self.result_description = QtWidgets.QLabel(parent=self)
        self.result_description.setObjectName("result_description")
        self.result_description.setWordWrap(True)
        self.gridLayout.addWidget(self.result_description, 6, 0, 6, 7)
        self.confirm_button = QtWidgets.QPushButton(parent=self)
        self.confirm_button.setObjectName("confirm_button")
        self.gridLayout.addWidget(self.confirm_button, 12, 7, 1, 3)
        MainWindow.setCentralWidget(self)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1067, 37))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        # self.gridLayout.setRowStretch(0, 1)
        # self.gridLayout.setRowStretch(6, 5)

        self.retranslateUi(MainWindow)
        # QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.searchbar.returnPressed.connect(self.do_search)
        self.searchbutton.clicked.connect(self.do_search)
        self.searchbar.textChanged.connect(self.search_trigger)
        self.searchbutton.setEnabled(False)
        self.confirm_button.setEnabled(False)
        self.search_result.currentIndexChanged.connect(self.update_show_info)



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.main_title.setText(_translate("MainWindow", "Scraper"))
        self.current_working.setText(_translate("MainWindow", "Currently Working on 1"))
        self.searchbutton.setText(_translate("MainWindow", "Search"))
        self.result_title.setText(_translate("MainWindow", "TextLabel"))
        self.result_description.setText(_translate("MainWindow", "TextLabel"))
        self.confirm_button.setText(_translate("MainWindow", "Confirm"))
        self.result_title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.result_description.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

    @asyncSlot()
    async def do_search(self):
        print(self.searchbar.text())
        self.search_result.clear()
        result = await self.api.query(self.searchbar.text())
        if result:
            titles = self.api.get_titles()
            for item in titles:
                self.search_result.addItem(item)
        self.searchbutton.setEnabled(False)

    def search_trigger(self):
        self.searchbutton.setEnabled(True)

    @asyncSlot()
    async def update_show_info(self):
        title = self.search_result.currentText()
        desc = self.api.get_description(title)
        self.result_title.setText(title)
        self.result_description.setText(desc)
        img = await self.api.get_cover_image(title)
        if img:
            self.result_image.setPixmap(self.pack_image_to_qpixmap(img))


    def pack_image_to_qpixmap(self,img_data):
        img = QImage()
        img.loadFromData(img_data)
        qpixmap = QPixmap()
        qpixmap = qpixmap.fromImage(img)
        return qpixmap


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main = Main(self)
        # self.setCentralWidget(self.main)

    # def resizeEvent(self,event):
    #     # super(MainWindow,self).resizeEvent(self,event)
    #     print(self.size().width())
    #     self.main.resize(self.size().width()-10,self.size().height()-10)



app = QApplication(sys.argv)

event_loop = QEventLoop(app)
asyncio.set_event_loop(event_loop)

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

w = MainWindow()
w.show()
with event_loop:
    event_loop.run_until_complete(app_close_event.wait())
