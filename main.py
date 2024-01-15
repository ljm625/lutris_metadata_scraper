import asyncio
import sys
from random import randint
import sqlite3

import requests
import yaml
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget, QDialog, QDialogButtonBox, QRadioButton, QHBoxLayout, QGridLayout, QScrollArea,
)
from qasync import QEventLoop, asyncSlot

from adaptor.lutris import Lutris
from vndb.VNDB import VNDB

def load_config(name):
    with open(name) as file:
        config = yaml.load(file.read(), Loader=yaml.FullLoader)
        return config


class ScreenshotDialog(QDialog):
    def __init__(self,parent,title):
        super().__init__()
        self.parent = parent
        self.setWindowTitle(f"{title}  Choose image for banner")
        self.setGeometry(QtCore.QRect(10, 0, 1051, 531))
        self.checkboxs = [None]*6
        self.images = [None]*6
        self.start_range = 0
        self.title = title
        self.screenshot_count = 0
        self.chosen_img_index = 0
        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.prev = QPushButton("Prev Page")
        self.next = QPushButton("Next Page")
        self.prev.setEnabled(False)
        self.next.setEnabled(False)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QGridLayout()
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev)
        button_layout.addWidget(self.next)
        button_layout.addWidget(self.buttonBox)
        index = 0
        for i in range(0,2):
            for j in range(0,3):
                resp = self.generate_image_group(index)
                self.layout.addLayout(resp, i, j, 1, 1)
                index+=1
        self.layout.addLayout(button_layout,2,0,1,-1)
        self.setLayout(self.layout)
        self.do_get_screenshots()
        self.prev.clicked.connect(self.goto_prev_page)
        self.next.clicked.connect(self.goto_next_page)
        self.screenshot_count = self.parent.api.get_screenshot_count(title)
        if self.screenshot_count>6:
            self.next.setEnabled(True)


    def goto_prev_page(self):
        self.start_range = self.start_range - 6
        if self.start_range<0: self.start_range=0
        if self.start_range==0:
            self.prev.setEnabled(True)
        self.next.setEnabled(True)
        self.do_get_screenshots()


    def goto_next_page(self):
        self.start_range = self.start_range + 6
        if self.start_range+6<self.screenshot_count:
            # Still more images to go
            pass
        else:
            self.next.setEnabled(False)
        self.prev.setEnabled(True)
        self.do_get_screenshots()

    def generate_image_group(self,index):
        if index>len(self.checkboxs):
            return
        layout = QtWidgets.QVBoxLayout()
        img = QLabel(f"Image-{index}")
        img.setScaledContents(True)
        choice = QRadioButton("Select")
        layout.addWidget(img)
        layout.addWidget(choice)
        choice.setEnabled(False)
        self.checkboxs[index] = choice
        self.images[index] = img
        choice.toggled.connect(self.on_chosen_screenshot)
        return layout

    def on_chosen_screenshot(self):
        for i in range(0,6):
            if self.checkboxs[i].isChecked():
                self.chosen_img_index = i+self.start_range
                print("Choose Image {}".format(self.chosen_img_index))
                return

    def pack_image_to_qpixmap(self,img_data):
        img = QImage()
        img.loadFromData(img_data)
        qpixmap = QPixmap()
        qpixmap = qpixmap.fromImage(img)
        scaled_pixmap = qpixmap.scaled(int(self.images[0].size().width()),int(self.images[0].size().height()), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return scaled_pixmap

    def do_get_screenshots(self):
        for i in range(0,6):
            self.do_get_screenshot(i)

    @asyncSlot()
    async def do_get_screenshot(self,index):
        if index+self.start_range>=self.screenshot_count:
            # Running out of images
            self.checkboxs[index].setEnabled(False)
            self.images[index].clear()
            return
        image = await self.parent.api.get_screenshot(self.title,index+self.start_range)
        if image:
            pixmap = self.pack_image_to_qpixmap(image)
            self.images[index].setPixmap(pixmap)
            self.images[index].setScaledContents(True)
            self.checkboxs[index].setEnabled(True)





class Main(QWidget):
    def __init__(self,parent,api,adaptor):
        super(Main,self).__init__()
        self.parent = parent
        self.api = api
        self.adaptor = adaptor
        self.setupUi(parent)
        self.game_list = []
        self.current_game_index=0
        self.game_list = self.adaptor.get_title_list()
        self.current_game_info = {
            "title": None,
            "prefer_title": None,
            "cover_art": None,
            "banner_art": None,
        }
        self.parse_next_game()

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
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.result_description)
        self.result_description.resize(self.scroll_area.size())
        self.gridLayout.addWidget(self.scroll_area, 6, 0, 6, 7)
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
        self.confirm_button.clicked.connect(self.do_choose_banner)



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.main_title.setText(_translate("MainWindow", "Scraper"))
        self.current_working.setText(_translate("MainWindow", "Currently Working "))
        self.searchbutton.setText(_translate("MainWindow", "Search"))
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

    def do_choose_banner(self):
        dlg = ScreenshotDialog(self,self.result_title.text())

        if dlg.exec():
            print("Success!")
            print("Final Chosen Image {}".format(dlg.chosen_img_index))
            self.update_info_to_adaptor(dlg.chosen_img_index)
        else:
            print("Cancel!")

    @asyncSlot()
    async def update_info_to_adaptor(self,banner_index):
        self.current_game_info["title"] = self.result_title.text()
        self.current_game_info["prefer_title"] = self.api.get_prefer_title(self.result_title.text())
        self.current_game_info["banner_art"] = await self.api.get_screenshot(self.current_game_info["title"],
                                                                             banner_index)

        self.adaptor.update_game_entry(self.game_list[self.current_game_index]['id'], self.current_game_info["prefer_title"],
                                  self.current_game_info["cover_art"], self.current_game_info["banner_art"])
        self.current_game_index += 1
        self.parse_next_game()

    @asyncSlot()
    async def update_show_info(self):
        title = self.search_result.currentText()
        desc = self.api.get_description(title)
        self.result_title.setText(title)
        self.result_description.setText(desc)
        img = await self.api.get_cover_image(title)
        self.current_game_info["cover_art"] = img
        if img:
            self.result_image.setPixmap(self.pack_image_to_qpixmap(img,self.result_image))
        self.confirm_button.setEnabled(True)


    def pack_image_to_qpixmap(self,img_data,qlabel):
        img = QImage()
        img.loadFromData(img_data)
        qpixmap = QPixmap()
        qpixmap = qpixmap.fromImage(img)
        scaled_pixmap = qpixmap.scaled(qlabel.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return scaled_pixmap


    def parse_next_game(self):
        if self.current_game_index>=len(self.game_list):
            # ALL DONE
            self.progressBar.setProperty("value", 100)
            self.current_working.setText(f"All DONE! You can safely quit the application now")
            return
        self.current_game_info = {
            "title": None,
            "prefer_title": None,
            "cover_art": None,
            "banner_art": None,
        }
        print(f"Start parsing {self.game_list[self.current_game_index]['title']}")
        current_game = self.game_list[self.current_game_index]
        self.current_working.setText(f"Currently working on: {current_game['title']}")
        self.progressBar.setProperty("value",int(100*self.current_game_index/len(self.game_list)))
        self.searchbar.setText(current_game['title'])
        self.do_search()



class MainWindow(QMainWindow):
    def __init__(self,api,adaptor):
        super().__init__()
        self.main = Main(self,api,adaptor)
        # self.setCentralWidget(self.main)

    # def resizeEvent(self,event):
    #     # super(MainWindow,self).resizeEvent(self,event)
    #     print(self.size().width())
    #     self.main.resize(self.size().width()-10,self.size().height()-10)

config=load_config("config.yaml")
app = QApplication(sys.argv)

event_loop = QEventLoop(app)
asyncio.set_event_loop(event_loop)

app_close_event = asyncio.Event()
app.aboutToQuit.connect(app_close_event.set)

api = VNDB(config["prefer_title_language"])
adaptor = Lutris(config["update_title"])

w = MainWindow(api,adaptor)
w.show()
with event_loop:
    event_loop.run_until_complete(app_close_event.wait())
