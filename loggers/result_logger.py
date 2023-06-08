from datetime import datetime
import logging

def initialize():
    with open('errors.log', 'a') as f:
        f.write(f'\n------ {datetime.now().isoformat()} ------\n')
        
    logging.basicConfig(filename='result.log', level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log(msg):
    logging.info(msg)