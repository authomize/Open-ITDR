# import sys
import json
# import logging
# import configparser
import requests

# Temp Objects for Testing
myAuthomizeAPIkey = ""
myAuthomizeBaseURL = "https://api.authomize.com/v2/apps/"
myAauthomizeRestAPIid = ""
bodyJSON=[]

def GetJSONData():
  JsonData = {"data": [{"uniqueId": "683f316e-69c0-48e7-99d4-8d2cf0938933", "name": "Henrietta Mueller", "email": "HenriettaM@6xd4bs.onmicrosoft.com", "firstName": "Henrietta", "lastName": "Mueller", "description": "TEST: v1.1 | Risk Event: passwordSpray | IP Address: 142.44.170.136 | Detection Type: offline | Detected: 2022-11-04T09:52:23.952Z", "tags": ["atRisk_v1", "riskLevel-high"], "detectionTime": "2022-11-04T09:52:23.952Z"}]}
  JsonData2 = [{"email": "HenriettaM@6xd4bs.onmicrosoft.com"}]
  return JsonData

def postRiskyUser(authomizeBaseURL,authomizeAPIkey,authomizeRestAPIid,bodyJSON):
    getTestData = GetJSONData()
    theData = json.dumps(bodyJSON)
    print(theData)
    getJSONdump = []
    if theData != []:
      URL = authomizeBaseURL + authomizeRestAPIid + "/identities"
      print (URL)
      theheaders = {
          'Authorization': authomizeAPIkey,
          'Content-Type': 'application/json'
          }
      try:
        response = requests.post(url=URL,data=theData, headers=theheaders)
        theresponse = response
        if (response.status_code >= 200 and response.status_code <= 299):
            getJSONdump = json.dumps(theresponse.json(), indent=2)
            print("The Return Data is: ", getJSONdump)
        else:
          print("Response code: {}".format(response.status_code))

      except:
          print("Response code: {}".format(response.status_code))
    else:
      print("Empty Data String!!!")

# postRiskyUser(myAuthomizeBaseURL,myAuthomizeAPIkey,myAauthomizeRestAPIid,bodyJSON)
