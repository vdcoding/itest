import logging


def setup_log(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if numeric_level is None:
        raise ValueError("Invalid log level: %s" % loglevel)
    logger = logging.getLogger('itest')
    log_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(log_fmt)
    logger.addHandler(handler)
    logger.setLevel(loglevel)
    return logger

