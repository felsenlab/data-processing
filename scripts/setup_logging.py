import logging
import os
import datetime
import colorlog

import logging
logger = logging.getLogger(__name__)

def configure_logging(log_dir):
	log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
	current_time = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')

	log_file = os.path.join(log_dir, f'{current_time}.log')

	file_handler = logging.FileHandler(log_file)
	file_handler.setFormatter(logging.Formatter(log_format))

	console_handler = colorlog.StreamHandler()
	console_handler.setFormatter(colorlog.ColoredFormatter(
		"%(log_color)s" + log_format,
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'white,bg_red'
        }
    ))

    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])
    logger.info('Logging to %s' % log_file)