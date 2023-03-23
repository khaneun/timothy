from kiwoom.kiwoom import *
import sys
from PyQt5.QtWidgets import *

class UIClass():
    def __init__(self):
        print("UI_Class 입니다.")

        ### UI를 실행하기 위해 변수를 초기화하는 Function
        self.app = QApplication(sys.argv)
        ###########################################

        self.kiwoom = Kiwoom()

        ### Eventloop를 지속적으로 실행하기 위한 Command
        self.app.exec_()
