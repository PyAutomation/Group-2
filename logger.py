import logging

class Logger(object):
    def __init__(self, level):
        self.logger = logging.getLogger()
        if not len(self.logger.handlers):
            self.logger.setLevel(level)
            self.fh = logging.FileHandler('trace.log')
            self.fh.setLevel(level)
            self.ch = logging.StreamHandler()
            self.ch.setLevel(level)
            self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.fh.setFormatter(self.formatter)
            self.ch.setFormatter(self.formatter)
            self.logger.addHandler(self.fh)
            self.logger.addHandler(self.ch)

log = Logger(logging.INFO)