import sys  
from PyQt5.QtWidgets import QApplication  
from gui import IntroWindow, MainWindow

if __name__ == '__main__':  
    app = QApplication(sys.argv)  
    intro_window = IntroWindow()  
    intro_window.show()  
    # main_window = MainWindow("../tests/images/")
    # main_window.show()
    sys.exit(app.exec_())