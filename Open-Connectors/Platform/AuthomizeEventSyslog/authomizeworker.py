import json
import sys
import requests
import time
import configparser
import os.path
import logging
import logging.handlers
import socket
from datetime import datetime, timezone

# Load settings
config = configparser.ConfigParser()
config.read('config.cfg')
# Assign Variables
URL = config.get('DEFAULT','authomizeURL')
token = config.get('DEFAULT','authomizeToken')
# customer_id = config.get('DEFAULT','customer_id')
# shared_key = config.get('DEFAULT','shared_key')
# log_type = config.get('DEFAULT','sentinelLog')
DateFileCFG = config.get('DEFAULT','DateFileCFG')
theSYSLOG_HOST = config.get('DEFAULT','syslog_host')
#theSYSLOG_PORT = config.get('DEFAULT','syslog_port')
theSYSLOG_PORT = 514


MyNextPage = ""
currentDate = ""

# Setup the Data for the Search query
# Currently innefficient - only pulling 1 at a time
# Revisit the processes and update when have time

def GetJSONData(BooleanValue,nextPage,TheCurrentDateTime):
  if BooleanValue == True:
    JsonData = {
                "filter": {
                  "createdAt": {
                    "$lt": TheCurrentDateTime
                  },
                  "updatedAt": {
                  },
                  "severity": {
                    "$in": [
                      ]
                  },
                  "status": {
                    "$in": [
                      "Open"
                      ]
                  },
                  "isResolved": {
                    "$eq": False
                  }
                },
                "pagination": {
                  "nextPage": nextPage,
                  "limit": 1
                },
                "expand": [
                  "policy"
                ],
                "sort": [
                  {
                    "fieldName": "createdAt",
                    "order": "DESC"
                  }
                ]
              }
  else:
    JsonData = {
              "filter": {
                "createdAt": {
                  "$gte": TheCurrentDateTime
                },
                "updatedAt": {
                },
                "severity": {
                  "$in": [
                    ]
                },
                "status": {
                  "$in": [
                    "Open"
                    ]
                },
                "isResolved": {
                  "$eq": False
                }
              },
              "pagination": {
                "nextPage": nextPage,
                "limit": 1
              },
              "expand": [
                "policy"
              ],
              "sort": [
                {
                  "fieldName": "createdAt",
                  "order": "DESC"
                }
              ]
            }

  return JsonData


def process_local_syslog(theNewMessage):
  logging_server = theSYSLOG_HOST
  syslog_logger = logging.getLogger('SYSLOG')
  syslog_formatter = logging.Formatter("%(asctime)s  AUTHOMIZE: %(message)s\n", "%b %d %H:%M:%S")
  syslog_logger.setLevel(logging.INFO)
  syslog_handler = logging.handlers.SysLogHandler(address = (logging_server, theSYSLOG_PORT))
  syslog_handler.setFormatter(syslog_formatter)
  syslog_handler.append_nul = False
  syslog_logger.addHandler(syslog_handler)
  #mymsg2 = "processing message..."
  #syslog_logger.info(mymsg2)
  syslog_logger.info(theNewMessage)
  # time.sleep(1)
  # print("Just Sent ----> ",theNewMessage)
  q = True
  return bool(q)

def DateInZulu(currentDate):
  currentDate = datetime.now(timezone.utc).isoformat()
  return(currentDate)


def CheckFileExists(FileExistStatus):
  if os.path.exists(DateFileCFG):
    FileExistStatus = False
  else:
    FileExistStatus = True
  return bool(FileExistStatus)

def WriteFileContent(FileContent):
  f = open(DateFileCFG, "w")
  f.write(FileContent)
  f.close()

def ReadFileContent():
  f = open(DateFileCFG, "r")
  line = f.read()
  return line


#### NOT USED #####
def CheckToRun(TheCurrentDate,CurrentFileDate):
  #SominfoGoes Here
  TheDate = TheCurrentDate
  TheFileDate = CurrentFileDate
  #get the difference - check against intervalwait time and determine if greater than what has been specified

def convert(date_time):
    format = '%Y-%m-%dT%H:%M:%S.%f'  # The format
    datetime_str = datetime.strptime(date_time, format)
    return datetime_str
#### NOT USED ####

def searchIncident():

    TheCurrentDateTime = DateInZulu(currentDate)
    FileState = CheckFileExists(True)

    if FileState:
      WriteFileContent(TheCurrentDateTime)
      JsonData = GetJSONData(FileState,'',TheCurrentDateTime)
      theData = json.dumps(JsonData)
    else:
      TheTime = ReadFileContent()
      TheCurrentDateTime = TheTime
      JsonData = GetJSONData(FileState,'',TheCurrentDateTime)
      theData = json.dumps(JsonData)

    theheaders = {
        'Authorization': token,
        'Content-Type': 'application/json'
        }

    # Enter while state
    hasMore = True
    # Setup for pulling data until hasMore is False
    while hasMore:
      response = requests.post(url=URL,data=theData, headers=theheaders)
      theresponse = response
      if (response.status_code >= 200 and response.status_code <= 299):
          getJSONdump = json.dumps(theresponse.json(), indent=2)

          #Inspect JSON for returned values
          jsonObj = json.loads(getJSONdump)
          # print("This is the first bit", jsonObj['data'])

          #access elements in the object
          limit = jsonObj['pagination']['limit']
          nextPage = jsonObj['pagination']['nextPage']
          hasMore = jsonObj['pagination']['hasMore']

          #get the data from the object to send to Sentinel
          myAzureData = jsonObj['data']

          print("---",limit,"|", nextPage,"|", hasMore, "---")
          thebody = "---->" + nextPage
          # print(thebody)
          if myAzureData != []:
            thebody = json.dumps(myAzureData)
            #body = json.loads(myAzureData)
            #print("Message to syslog ---> Check out syslog")
            # Add variable to syslog for message (don't forget to wait)
            # change the number of events to 1 only (this is only temp for this Q)
            # Revisit and add components for processing a dictionary
            #print("Woudl Have Sent:", jsonObj['data'])
            process_local_syslog(thebody)

            # post_data(customer_id, shared_key, body, log_type)
          else:
            print("Empty Data String!!!")

          # Setup the request with new JSON data
          JsonData = GetJSONData(FileState,nextPage,TheCurrentDateTime)
          theData = json.dumps(JsonData)

          if hasMore == False:
            TheCurrentDateTime = DateInZulu(currentDate)
            WriteFileContent(TheCurrentDateTime)
      else:
          print("Response code: {}".format(response.status_code))

searchIncident()
