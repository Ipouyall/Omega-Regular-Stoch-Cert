from logging import getLogger, FileHandler, Formatter, DEBUG


logger = getLogger(__name__)
file_handler = FileHandler(filename='system.log', mode='a')
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(DEBUG)
