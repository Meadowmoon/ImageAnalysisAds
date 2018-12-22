import logging
import sys
import os
import datetime

class Logger():
    # Initialize logs
    LOG_PATH = 'logs'
    LOG_FILE = '{}.txt'.format(datetime.date.today().isoformat())

    def config(self,name):
        logger = logging.getLogger(name)
        if os.path.exists(Logger.LOG_PATH):
            pass
        else:
            os.mkdir(self.LOG_PATH)
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
        file_handler = logging.FileHandler("%s/%s" % (Logger.LOG_PATH, Logger.LOG_FILE))
        file_handler.setFormatter(formatter) 
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = formatter 
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def get_logger(self,name):
        return self.config(name)
