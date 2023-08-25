from pathlib import Path
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import piexif
import ezkfg as ez
from cairosvg import svg2png

FONTS_PATH = Path(__file__).parent / "asset" / "fonts"
ICONS_PATH = Path(__file__).parent / "asset" / "icons"
TEMP_PATH = Path(__file__).parent / "temp"
TEMP_PATH.mkdir(exist_ok=True)

CONFIG_TEMPLATE = {
    'folder_history': [],
    'max_folder_history': 10,
    'watermark': {
        'text': 'LEICA',
        'font': {
            'bold': str(FONTS_PATH / "SourceHanSansCN-Bold.otf"),
            'light': str(FONTS_PATH / "SourceHanSansCN-Light.otf"),
        },
        'font_size': "20%",
        'font_color': [0, 0, 0, 255],
        'border': {
            'size': "3%",
            "ratio": "4:3",
        },
        'bg_color': [255, 255, 255, 255],
        'text_area': {
            'height': "15%",
            'width': "100%",
        },
        'margin': '3%',
        'div_line_width': 10,
        'div_line_color': [156, 156, 156, 255],
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
        'gps': False,
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
            
        self.config['export_folder'] = os.path.join(folder_path, "export")
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
        self.imgInfo = QListWidget()
        self.controlPanel = QWidget()

        self.set_control_panel()

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

    def set_control_panel(self):
        self.imgInfo.setSelectionMode(QAbstractItemView.NoSelection)
        info_items = self.config['show_info']
        for name, checked in info_items.items():
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if checked:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.imgInfo.addItem(item)
        
        self.imgInfo.itemChanged.connect(self.update_info)

        self.controlPanelLayout = QVBoxLayout()
        self.regenerate_btn = QPushButton('Regenerate')
        self.regenerate_btn.clicked.connect(self.show_image)
        
        self.batch_btn = QPushButton('Batch Process')
        self.batch_btn.clicked.connect(self.batch_process)
        
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        
        self.controlPanelLayout.addWidget(self.regenerate_btn)
        self.controlPanelLayout.addWidget(self.batch_btn)
        self.controlPanelLayout.addWidget(self.progressBar)
        self.controlPanel.setLayout(self.controlPanelLayout)
    
    def update_info(self, item):
        info_items = self.config['show_info']
        info_items[item.text()] = True if item.checkState() == Qt.Checked else False
        self.config['show_info'] = info_items
        self.config.dump(Path(__file__).parent / "asset" / "config.yaml")
        self.show_image(self.current_index)

    def process_single(self, img_path):
        target_dict = self.get_image_info(img_path)
        watermarked = Image.open(img_path).convert('RGBA')
        watermarked = self.add_watermark(watermarked, target_dict)
        watermarked = watermarked.convert('RGB')
        watermarked.save(os.path.join(self.config['export_folder'], os.path.basename(img_path)))

    def show_image(self, index = -1):
        if index == -1:
            index = self.thumbView.currentRow()
        self.current_index = index
        filename = self.thumbView.item(index).text()
        img_path = os.path.join(self.folder_path, filename)
        
        img = QImage(img_path)
        self.imgView.setPixmap(QPixmap.fromImage(img).scaled(500, 500, Qt.KeepAspectRatio))

        target_dict = self.get_image_info(img_path)        
        logger.info(target_dict)
        
        # add watermark
        watermarked = Image.open(img_path).convert('RGBA')
        watermarked = self.add_watermark(watermarked, target_dict)
        watermarked = QImage(watermarked.tobytes(), watermarked.size[0], watermarked.size[1], QImage.Format_RGBA8888)
        self.imgWMView.setPixmap(QPixmap.fromImage(watermarked).scaled(500, 500, Qt.KeepAspectRatio))
    
    def get_image_info(self, img_path):
        f = Image.open(img_path)
        # info = ''
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

        return target_dict

    def batch_process(self):
        # 显示progressBar
        self.progressBar.setVisible(True)
        
        if not os.path.exists(self.config['export_folder']):
            os.mkdir(self.config['export_folder'])
        
        # get all images
        images = []
        for img in os.listdir(self.folder_path):
            if img.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(img)
        
        # set progressBar
        self.progressBar.setMaximum(len(images))
        self.progressBar.setValue(0)

        # process

        for img in images:
            self.process_single(os.path.join(self.folder_path, img))
            self.progressBar.setValue(self.progressBar.value() + 1)
        
        # hide progressBar
        self.progressBar.setVisible(False)
        QMessageBox.information(self, "Done", "Batch process done")

    @staticmethod
    def get_shutter_speed(value):
        if value < 1:
            return f"1/{int(1/value)}s"
        else:
            return f"{int(value)}s"
    
    def add_watermark(self, img, info_dict):
        wm_config = self.config['watermark']
        img_size = img.size

        self.img_size = img_size
        logger.info(f"img size: {img_size}")

        # border
        border_size = wm_config['border']['size']
        border_size = self.deal_height_weight_type(border_size, img_size)
        
        self.border_size = border_size
        logger.info(f"border size: {border_size}")

        if ":" in wm_config['border']['ratio']:
            border_ratio = wm_config['border']['ratio'].split(':')
            if int(border_ratio[0]) < int(border_ratio[1]):
                border_ratio = int(border_ratio[1]) / int(border_ratio[0])
            else:
                border_ratio = int(border_ratio[0]) / int(border_ratio[1])
        else:
            border_ratio = None

        self.border_ratio = border_ratio
        logger.info(f"border ratio: {border_ratio}")

        # text area size
        text_area_size = wm_config['text_area']['width'], wm_config['text_area']['height']
        text_area_size = self.deal_height_weight_type(text_area_size, img_size)
        
        self.text_area_size = text_area_size
        logger.info(f"text area size: {text_area_size}")

        # new image size
        # always bottom
        nheight = img_size[1] + text_area_size[1] + border_size[1]
        nwidth = nheight * border_ratio if border_ratio else img_size[0] + border_size[0] * 2

        nheight = int(nheight)
        nwidth = int(nwidth)

        self.nheight = nheight
        self.nwidth = nwidth
        logger.info(f"new image size: {nwidth}x{nheight}")

        nimg = Image.new('RGBA', (nwidth, nheight), tuple(wm_config['bg_color']))
        nimg.paste(img, (int((nwidth-img_size[0])/2), border_size[1]))

        # font
        font_size = wm_config['font_size']
        if type(font_size) == str and '%' in font_size:
            font_size = self.get_percent(font_size, text_area_size[1])
        
        self.font_size = font_size
        logger.info(f"font size: {font_size}")

        bold_font = ImageFont.truetype(wm_config['font']['bold'], font_size)
        light_font = ImageFont.truetype(wm_config['font']['light'], int(font_size * 0.8))
        font = {
            'bold': bold_font,
            'light': light_font
        }

        # camera text
        self.draw_camera_text(nimg, info_dict, font)
        logger.info(f"draw camera text done")

        # detail text
        self.draw_detail_text(nimg, info_dict, font)
        logger.info(f"draw detail text done")

        # icon
        icon_path = self.get_icon_path(info_dict['camera_maker'])
        if icon_path and self.config['show_info']['camera_maker']:
            svg2png(url=icon_path ,write_to=str(TEMP_PATH / "icon.png"), parent_height=font_size * 2)
            # to PIL
            icon = Image.open(str(TEMP_PATH / "icon.png"))
            logger.info(f"icon size: {icon.size}")
            self.draw_icon(nimg, icon)
        
        # nimg.save(str(TEMP_PATH / "watermarked.png"))
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
        return self.config['icons']['leica']

    def draw_icon(self, img, icon):
        self.margin = self.get_percent(self.config['watermark']['margin'], self.text_area_size[0]) if '%' in str(self.config['watermark']['margin']) else self.config['watermark']['margin']
        self.div_line_width = self.get_percent(self.config['watermark']['div_line_width'], self.text_area_size[0]) if '%' in str(self.config['watermark']['div_line_width']) else int(self.config['watermark']['div_line_width'])
        icon_pos = (int(self.start_pos_width - icon.size[0] - self.margin * 2 - self.div_line_width), int(self.nheight-self.text_area_size[1] + (self.text_area_size[1]-icon.size[1])/2))
        img.paste(icon, icon_pos, icon)
        
        # draw div line
        draw = ImageDraw.Draw(img)
        draw.line((self.start_pos_width - self.margin - self.div_line_width, icon_pos[1], self.start_pos_width - self.margin - self.div_line_width, icon_pos[1] + icon.size[1]), fill=tuple(self.config['watermark']['div_line_color']), width=int(self.div_line_width))

        return img

    def draw_camera_text(self, img, info, font):
        draw = ImageDraw.Draw(img)
        if self.config['show_info']['camera']:
            text = info['camera']
            text_size = draw.textsize(text, font['bold'])
            logger.info(f"camera text size: {text_size}")
            text_pos = (int(self.border_size[0]), self.nheight-self.text_area_size[1] + int((self.text_area_size[1]-2*text_size[1])/5*2))
            draw.text(text_pos, text, tuple(self.config['watermark']['font_color']), font=font['bold'])

        if self.config['show_info']['lens']:
            text = info['lens']
            text_size = draw.textsize(text, font['light'])
            logger.info(f"lens text size: {text_size}")
            text_pos = (int(self.border_size[0]), self.nheight-self.text_area_size[1] + int(text_size[1] / 0.8) + int((self.text_area_size[1]-2*text_size[1])/5*3))
            draw.text(text_pos, text, tuple(self.config['watermark']['font_color']), font=font['light'])
        return img

    def draw_detail_text(self, img, info, font):
        draw = ImageDraw.Draw(img)
        text = ""
        if self.config['show_info']['focal_length']:
            text += info['focal_length']
        if self.config['show_info']['aperture']:
            text += ' ' + info['aperture']
        if self.config['show_info']['shutter_speed']:
            text += ' ' + info['shutter_speed']
        if self.config['show_info']['iso']:
            text += ' ' + info['iso']
        text_size = draw.textsize(text, font['bold'])
        logger.info(f"detail text size: {text_size}")
        text_pos = (int(self.nwidth - self.border_size[0] - text_size[0]), self.nheight-self.text_area_size[1] + int((self.text_area_size[1]-2*text_size[1])/5*2))
        draw.text(text_pos, text, tuple(self.config['watermark']['font_color']), font=font['bold'])

        self.start_pos_width = text_pos[0]

        text = ""
        if self.config['show_info']['date']:
            text += info['date']
        if self.config['show_info']['time']:
            text += ' ' + info['time']
        text_size = draw.textsize(text, font['light'])
        logger.info(f"date text size: {text_size}")
        text_pos = (int(self.nwidth - self.border_size[0] - text_size[0]), self.nheight-self.text_area_size[1] + int(text_size[1] / 0.8) + int((self.text_area_size[1]-2*text_size[1])/5*3))
        draw.text(text_pos, text, tuple(self.config['watermark']['font_color']), font=font['light'])

        self.start_pos_width = min(self.start_pos_width, text_pos[0])

        return img