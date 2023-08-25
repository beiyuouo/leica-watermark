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
import ezkfg as ez
import svgwrite

ICONS_PATH = Path(__file__).parent / "asset" / "icons"

CONFIG_TEMPLATE = {
    'folder_history': [],
    'max_folder_history': 10,
    'watermark': {
        'text': 'LEICA',
        'font': 'arial.ttf',
        'font_size': 20,
        'font_color': [255, 255, 255, 255],
        'border': {
            'size': "3%",
            "ratio": "16:9",
        },
        'bg_color': [0, 0, 0, 0],
        'text_area': {
            'height': "15%",
            'width': "100%",
        }
    },
    'show_info': {
        'camera': True,
        'camera_maker': True,
        'lens': True,
        'focal_length': True,
        'aperture': True,
        'shutter_speed': True,
        'iso': True,
        'date': True,
        'time': True,
        'gps': True
    },
    'icons': {
        'canon': str(ICONS_PATH / "canon.svg"),
        'leica': str(ICONS_PATH / "leica.svg"),
        'nikon': str(ICONS_PATH / "nikon.svg"),
        'sony': str(ICONS_PATH / "sony.svg"),
        'olympus': str(ICONS_PATH / "olympus.svg"),
        'panasonic': str(ICONS_PATH / "panasonic.svg"),
        'fujifilm': str(ICONS_PATH / "fujifilm.svg"),
        'apple': str(ICONS_PATH / "apple.svg"),
        'xiaomi': str(ICONS_PATH / "xiaomi.svg"),
        'huawei': str(ICONS_PATH / "huawei.svg"),
    }
}

class IntroWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LEICA WATERMARK - Intro")
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.open_last_folder_button = QPushButton("Open Last Folder")
        self.open_new_folder_button = QPushButton("Open New Folder")
        self.open_new_folder_button.clicked.connect(self.open_folder)
        self.open_last_folder_button.clicked.connect(self.open_last_folder)

        self.layout.addWidget(self.open_last_folder_button)
        self.layout.addWidget(self.open_new_folder_button)
        self.setLayout(self.layout)

        self.config_path = Path(__file__).parent / "asset" / "config.yaml"
        
        try:
            self.config = ez.load(self.config_path)
        except:
            self.config = ez.Config()
            self.config.dump(self.config_path)


        self.check_config()
        logger.info(self.config)
    
    def check_config(self):        
        self.config_ = ez.Config(CONFIG_TEMPLATE)
        self.config_.update(self.config)
        self.config = self.config_
        
        self.config.dump(self.config_path)
    
    def open_last_folder(self):
        if self.config['max_folder_history'] > 0 and self.config['folder_history'] != None and len(self.config['folder_history']) > 0:
            folder_path = self.config['folder_history'][-1]
            self.open_main_window(folder_path)
        else:
            QMessageBox.warning(self, "Warning", "No folder history found, please open a new folder")
            self.open_folder()

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            logger.info(f"selected folder: {folder_path}")
            self.open_main_window(folder_path)

    def open_main_window(self, folder_path):
        if self.config['folder_history'] == None:
            self.config['folder_history'] = []
        
        if folder_path not in self.config['folder_history']:
            self.config['folder_history'].append(folder_path)
            if len(self.config['folder_history']) > self.config['max_folder_history']:
                self.config['folder_history'] = self.config['folder_history'][-self.config['max_folder_history']:]
            self.config.dump(self.config_path)
        
        self.hide()
        self.main_window = MainWindow(folder_path)
        self.main_window.show()

class MainWindow(QWidget):
    def __init__(self, folder_path):
        super().__init__()
        self.setWindowTitle("LEICA WATERMARK - Main")
        self.setFixedSize(1200, 800)
        self.folder_path = folder_path
        self.config = ez.load(Path(__file__).parent / "asset" / "config.yaml")
        logger.info(self.config)
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
        target_dict = {
            'camera': piexif_dict['0th'][272].decode('utf-8'),
            'camera_maker': piexif_dict['0th'][271].decode('utf-8'),
            'lens': piexif_dict['Exif'][42036].decode('utf-8'),
            'focal_length': piexif_dict['Exif'][37386][0]/piexif_dict['Exif'][37386][1],
            'aperture': piexif_dict['Exif'][33437][0]/piexif_dict['Exif'][33437][1],
            'shutter_speed': piexif_dict['Exif'][33434][0]/piexif_dict['Exif'][33434][1],
            'iso': piexif_dict['Exif'][34855],
            'date': piexif_dict['Exif'][36867].decode('utf-8'),
            'time': piexif_dict['Exif'][36868].decode('utf-8'),
            'gps': piexif_dict['GPS']
        }

        target_dict['focal_length'] = f"{target_dict['focal_length']}mm"
        target_dict['aperture'] = f"f/{target_dict['aperture']}"
        target_dict['shutter_speed'] = self.get_shutter_speed(target_dict['shutter_speed'])
        target_dict['iso'] = f"ISO {target_dict['iso']}"
        target_dict['date'] = target_dict['date'].split(' ')[0].replace(':', '-')
        target_dict['time'] = target_dict['time'].split(' ')[1]

        info += f"Camera: {target_dict['camera']}\n"
        info += f"Camera Maker: {target_dict['camera_maker']}\n"
        info += f"Lens: {target_dict['lens']}\n"
        info += f"Focal Length: {target_dict['focal_length']}\n"
        info += f"Aperture: {target_dict['aperture']}\n"
        info += f"Shutter Speed: {target_dict['shutter_speed']}\n"
        info += f"ISO: {target_dict['iso']}\n"
        info += f"Date: {target_dict['date']}\n"
        info += f"Time: {target_dict['time']}\n"
        info += f"GPS: {target_dict['gps']}\n"
        
        logger.info(target_dict)
        
        self.imgInfo.setText(info)
        
        # 添加水印
        watermarked = Image.open(img_path).convert('RGBA')
        watermarked = self.add_watermark(watermarked, target_dict)
        watermarked = QImage(watermarked.tobytes(), watermarked.size[0], watermarked.size[1], QImage.Format_RGBA8888)
        self.imgWMView.setPixmap(QPixmap.fromImage(watermarked).scaled(500, 500, Qt.KeepAspectRatio))

    @staticmethod
    def get_shutter_speed(value):
        if value < 1:
            return f"1/{int(1/value)}s"
        else:
            return f"{int(value)}s"
    
    def add_watermark(self, img, info_dict):
        wm_config = self.config['watermark']
        img_size = img.size

        logger.info(f"img size: {img_size}")

        # border
        border_size = wm_config['border']['size']
        border_size = self.deal_height_weight_type(border_size, img_size)
        
        logger.info(f"border size: {border_size}")

        if ":" in wm_config['border']['ratio']:
            border_ratio = wm_config['border']['ratio'].split(':')
            if int(border_ratio[0]) < int(border_ratio[1]):
                border_ratio = int(border_ratio[1]) / int(border_ratio[0])
            else:
                border_ratio = int(border_ratio[0]) / int(border_ratio[1])
        else:
            border_ratio = None

        logger.info(f"border ratio: {border_ratio}")

        # text area size
        text_area_size = wm_config['text_area']['width'], wm_config['text_area']['height']
        text_area_size = self.deal_height_weight_type(text_area_size, img_size)

        logger.info(f"text area size: {text_area_size}")

        # new image size
        # awalys bottom
        nheight = img_size[1] + text_area_size[1] + border_size[1]
        nwidth = nheight * border_ratio if border_ratio else img_size[0] + border_size[0] * 2

        nheight = int(nheight)
        nwidth = int(nwidth)

        logger.info(f"new image size: {nwidth}x{nheight}")

        nimg = Image.new('RGBA', (nwidth, nheight), tuple(wm_config['bg_color']))
        nimg.paste(img, (int((nwidth-img_size[0])/2), border_size[1]))

        # font
        font = ImageFont.truetype(wm_config['font'], wm_config['font_size'])
        font_color = wm_config['font_color']

        # icon
        icon_path = self.get_icon_path(info_dict['camera_maker'])
        if icon_path:
            icon = svgwrite.image.Image(icon_path, size=(int(img_size[0]*0.1), int(img_size[0]*0.1)))
            self.draw_icon(nimg, icon)



        return nimg

    @staticmethod
    def get_percent(value, total):
        value = int(value.split('%')[0])
        return int(1.0*value*total/100)
    
    def deal_height_weight_type(self, value, img_size):
        if type(value) == int:
            return (value, value)
        elif (type(value) == list or type(value) == tuple) and len(value) == 2:
            value = list(value)
            if '%' in value[0]:
                value[0] = self.get_percent(value[0], img_size[0])
            if '%' in value[1]:
                value[1] = self.get_percent(value[1], img_size[1])
            return (value[0], value[1])
        elif type(value) == str and '%' in value:
            value = value.split('%')[0]
            return (self.get_percent(value, img_size[0]), self.get_percent(value, img_size[1]))

    def get_icon_path(self, camera_maker):
        for key, value in self.config['icons'].items():
            if key.lower() in camera_maker.lower():
                return value
        return None

    def draw_icon(self, img, icon):
        return img

    def draw_camera_text(self, img, text):
        return img

    def draw_detail_text(self, img, text):
        return img

    def draw_date_text(self, img, text):
        return img