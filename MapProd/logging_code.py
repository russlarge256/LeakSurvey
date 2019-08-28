import logging

def log_your_stuff(log_name):

    log_format = "%(asctime)s %(filename)s:%(lineno)-3d %(levelname)s %(message)s"

    # create a 'formatter' using format string
    formatter = logging.Formatter(log_format)

    # create a log message handler that sends output to the file
    file_handler = logging.FileHandler(log_name)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)

    # set console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # get the 'root' logger.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # add multiple handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # add our file_handler to the 'root' logger's handlers
    logger.addHandler(file_handler)

    return logger
