# online/src/utils/log_helper.py
import logging

def setup_logger(name=None, level=logging.INFO):
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=level, format=fmt)
    return logging.getLogger(name)