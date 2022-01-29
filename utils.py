import adafruit_logging as logging

def str_to_log_val(val):
    if val == "NONE":
        return logging.NOTSET
    if val == "DEBUG":
        return logging.DEBUG
    if val == "INFO":
        return logging.INFO
    if val == "WARNING":
        return logging.WARNING
    if val == "ERROR":
        return logging.ERROR
    if val == "CRITICAL":
        return logging.CRITICAL

