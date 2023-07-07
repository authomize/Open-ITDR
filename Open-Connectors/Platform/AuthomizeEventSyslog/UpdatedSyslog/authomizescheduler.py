import schedule
import time
import logging
import configparser
from authomizeworker import searchIncident

# Configuring logging
logging.basicConfig(filename='scheduler.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def heart_beat(number_of_minutes):
    logging.info(f"Scheduler is alive and running - Will make contact with your Authomize tenant every {number_of_minutes} minutes. A heart beat is issued every 2 minutes see you then...")

def setup_timer(number_of_minutes):
    if number_of_minutes < 5:
        logging.error("Number of minutes should be at least 5")
        return False
    
    # Task scheduling
    schedule.every(2).minutes.do(heart_beat, number_of_minutes)
    schedule.every(number_of_minutes).minutes.do(searchIncident)

    # Informing about the scheduler
    logging.info(f"The scheduler is set to pull data from your Authomize tenant every {number_of_minutes} minutes.")
    return True

# Read configuration from config.cfg
config = configparser.ConfigParser()

try:
    config.read_file(open('config.cfg'))
    # Reading number_of_minutes from the DEFAULT section
    number_of_minutes = config.getint('DEFAULT', 'number_of_minutes')
except FileNotFoundError:
    logging.error("Configuration file not found")
    exit()
except configparser.Error as e:
    logging.error(f"Error reading configuration file: {str(e)}")
    exit()
except Exception as e:
    logging.error(f"An unexpected error occurred: {str(e)}")
    exit()

# Setup timer with number_of_minutes from configuration file
if not setup_timer(number_of_minutes):
    exit()

try:
    # Call the searchIncident function once before entering the scheduling loop
    # This forces the immediate processing of Authomize incidents
    logging.info("The scheduler is starting to try and pull data from Authomize NOW.")
    searchIncident()
    while True:
        # Running scheduled tasks
        schedule.run_pending()
        time.sleep(120)

# Handling Keyboard Interrupt
except KeyboardInterrupt:
    logging.info("Scheduler stopped by user")
except Exception as e:
    logging.error("An error occurred: %s", str(e))
