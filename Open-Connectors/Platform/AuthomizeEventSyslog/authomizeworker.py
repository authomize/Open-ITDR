# main script
import json
import requests
import configparser
import os
import logging
from datetime import datetime, timezone
import syslogworker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load settings
config = configparser.ConfigParser()
try:
    config.read('config.cfg')
    # ... settings ...
    URL = config.get('DEFAULT', 'authomizeURL')
    token = config.get('DEFAULT', 'authomizeToken')
    DateFileCFG = config.get('DEFAULT', 'DateFileCFG')
    syslog_host = config.get('DEFAULT', 'syslog_host') 
    syslog_port = config.getint('DEFAULT', 'syslog_port')

except configparser.Error as e:
    logging.error(f"Error reading or parsing config file: {e}")
    exit(1)

currentDate = ""

def GetJSONData(nextPage, TheCurrentDateTime, last_run_datetime=None):
    filter_criteria = {
        "createdAt": {
            "$lte": TheCurrentDateTime
        },
        "status": {
            "$in": ["Open"]
        }
    }

    if last_run_datetime:
        filter_criteria["createdAt"]["$gte"] = last_run_datetime

    return {
        "filter": filter_criteria,
        "expand": [
            "policy"
        ],
        "sort": [
            {
                "fieldName": "createdAt",
                "order": "ASC"
            }
        ],
        "pagination": {
            "limit": 10,
            "nextPage": nextPage
        }
    }


def DateInZulu(currentDate):
    currentDate = datetime.now(timezone.utc).isoformat()
    return currentDate


def CheckFileExists():
    try:
        # Checking if file exists
        return os.path.exists(DateFileCFG)
    except Exception as e:
        # Log or print the exception message
        logging.error(f"An error occurred while checking if the file exists: {e}")
        # Return False, assuming file does not exist in case of an error
        return False

def WriteFileContent(FileContent):
    try:
        # Opening file for writing
        with open(DateFileCFG, "w") as f:
            f.write(FileContent)
    except Exception as e:
        # Log or print the exception message
        logging.error(f"An error occurred while writing to the file: {e}")

def ReadFileContent():
    try:
        # Opening file for reading
        with open(DateFileCFG, "r") as f:
            return f.read()
    except Exception as e:
        # Log or print the exception message
        logging.error(f"An error occurred while reading from the file: {e}")
        # Return None in case of an error
        return None

def searchIncident():
    FileState = CheckFileExists()

    last_run_datetime = None
    if FileState:
        last_run_datetime = ReadFileContent()

    TheCurrentDateTime = DateInZulu(currentDate)

    theheaders = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    logging.info(f"Status: Started processing.")
    MyCounter = 0
    nextPage = ""
    while True:
        MyCounter += 1
        logging.info(f"INFO: --Processing-- [{MyCounter}]")
        JsonData = GetJSONData(nextPage, TheCurrentDateTime, last_run_datetime)
        theData = json.dumps(JsonData)

        try:
            response = requests.post(url=URL, data=theData, headers=theheaders, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Warning: An error occurred making the API request: {e}")
            break

        try:
            response_json = response.json()

            # Handling data element
            data_element = response_json.get('data', [])
            if data_element:
                try:
                    if syslog_host and syslog_port:
                        for event in data_element:
                            event_body = json.dumps(event)
                            syslogworker.send_to_syslog(event_body, syslog_host, syslog_port)
                    else:
                        logging.error("Syslog settings are not properly configured")
                except Exception as e:
                    logging.error(f"Error posting data: {e}")
            else:
                logging.info("No data to send, skipping process steps.")

            # Handling pagination
            pagination = response_json.get('pagination', {})
            if pagination.get('hasMore'):
                nextPage = pagination.get('nextPage', "")
            else:
                logging.info("Status: Stopped processing.")
                break
        except Exception as e:
            logging.error(f"Error processing response JSON: {e}")
            break

    # Update the timestamp file at the end of processing
    WriteFileContent(TheCurrentDateTime)

if __name__ == "__main__":
    searchIncident()