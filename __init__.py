from ui.ui import *
from config.logger import *

class Main():
    def __init__(self):

        self.logger = timothyLogger("Main  ")
        self.logger.info("Main Class Load.")

        # Load UI Class
        UIClass()

if __name__=="__main__":
    Main()




