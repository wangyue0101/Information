import logging


logging.basicConfig(level=logging.DEBUG, filename="./logs/log", filemode="a")

logging.debug("This is Debug")
logging.info("This is Info")
logging.warning("This is Warning")
logging.error("Ths is is rror")
logging.critical("This is critical")
