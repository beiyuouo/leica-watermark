from pathlib import Path
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QFont, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QGridLayout, QListWidget, QListWidgetItem, QTextEdit, QListView
from PyQt5.QtCore import Qt, QSize
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
from loguru import logger
import piexif


class IntroWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LEICA WATERMARK - Intro")
        self.layout = QHBoxLayout()
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.layout.addWidget(self.open_folder_button)
        self.setLayout(self.layout)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            logger.info(f"selected folder: {folder_path}")
            self.hide()
            self.main_window = MainWindow(folder_path)
            self.main_window.show()


class MainWindow(QWidget):
    def __init__(self, folder_path):
        super().__init__()
        self.setWindowTitle("LEICA WATERMARK - Main")
        self.setFixedSize(1200, 800)
        self.folder_path = folder_path
        self.initUI()

    def initUI(self):
        self.grid = QGridLayout()
        self.thumbView = QListWidget()
        self.thumbView.setViewMode(QListView.IconMode)
        # self.thumbView.setResizeMode(QListView.Adjust)
        self.thumbView.setMovement(QListView.Static)
        self.thumbView.setFlow(QListView.LeftToRight)
        # self.thumbView.setFixedHeight(800)

        self.imgView = QLabel()
        self.imgView.setAlignment(Qt.AlignCenter)
        self.imgWMView = QLabel()
        self.imgWMView.setAlignment(Qt.AlignCenter)
        self.imgInfo = QTextEdit()
        self.controlPanel = QWidget()
        

        self.grid.addWidget(self.thumbView, 0, 0, 2, 1)
        self.grid.addWidget(self.imgView, 0, 1)
        self.grid.addWidget(self.imgInfo, 1, 1)
        self.grid.addWidget(self.imgWMView, 0, 2)
        self.grid.addWidget(self.controlPanel, 1, 2)

        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 4)
        self.grid.setColumnStretch(2, 4)
        self.grid.setRowStretch(0, 2)
        self.grid.setRowStretch(1, 1)


        self.setLayout(self.grid)

        for img in os.listdir(self.folder_path):
            if img.lower().endswith(('.png', '.jpg', '.jpeg')):
                pixmap = QPixmap(os.path.join(self.folder_path, img)).scaled(100, 100, Qt.KeepAspectRatio)
                item = QListWidgetItem(QIcon(pixmap), img)
                self.thumbView.addItem(item)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.thumbView)
        self.scroll.setWidgetResizable(True)
        self.grid.addWidget(self.scroll, 0, 0, 2, 1)

        self.thumbView.currentRowChanged.connect(self.show_image)
        self.show_image(0)

    def show_image(self, index):
        filename = self.thumbView.item(index).text()
        img_path = os.path.join(self.folder_path, filename)
        
        img = QImage(img_path)
        self.imgView.setPixmap(QPixmap.fromImage(img).scaled(500, 500, Qt.KeepAspectRatio))

        f = Image.open(img_path)
        info = ''
        piexif_dict = piexif.load(f.info['exif'])
        for ifd_name in piexif_dict:
            if ifd_name == '0th':
                for tag in piexif_dict[ifd_name]:
                    tag_name = TAGS.get(tag, tag)
                    tag_value = piexif_dict[ifd_name][tag]
                    info += f'{tag_name}: {tag_value}\n'
        
        logger.info(info)
        
        self.imgInfo.setText(info)
        
        # 添加水印
        watermarked = QImage(img)
        self.imgWMView.setPixmap(QPixmap.fromImage(watermarked).scaled(500, 500, Qt.KeepAspectRatio))