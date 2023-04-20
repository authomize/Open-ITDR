import os
import time
import json
import logging
# import configparser
from collections import OrderedDict
from datetime import datetime, timezone
from updateauthomize import postRiskyUser
import requests
import msal

#get JSON file
def JSONConfig():
    with open('parameters.json') as f:
        d = json.load(f)
    return d

myJSONconfig = JSONConfig()

# Put all the security details together

# Optional logging
# logging.basicConfig(level=logging.DEBUG)

mysecret = myJSONconfig["secret"]
myscope = myJSONconfig["scope"]
myendpoint = myJSONconfig["endpoint"]
myauthority = myJSONconfig["authority"]
myclientid = myJSONconfig["client_id"]
myAuthomizeAPIkey = myJSONconfig["authomizeAPIkey"]
myAuthBaseURL = myJSONconfig["authomizeBaseURL"]
myauthomizeRestAPIid = myJSONconfig["authomizeRestAPIid"]

fieldNames = ["uniqueId","name", "email","firstName", "lastName", "description", "tags"]
values = []
body = []
anotherTest = []


# May use this??
def revBubbleSort( theSeq ):

    n = len( theSeq )
    
    for i in range( n - 1 ) :
        flag = 0

        for j in range(n - 1) :
            
            if theSeq[j]['timestamp'] < theSeq[j + 1]['timestamp'] : 
                tmp = theSeq[j]
                theSeq[j] = theSeq[j + 1]
                theSeq[j + 1] = tmp
                flag = 1

        if flag == 0:
            break
    
    
    return theSeq

def DateInZulu(currentDate):
  currentDate = datetime.now(timezone.utc).isoformat()
  return(currentDate)

#Convert date to perform calulations 
def convert(date_time):
    date_time = date_time.strip('Z')
    format = '%Y-%m-%dT%H:%M:%S.%f'  # The format
    datetime_str = datetime.strptime(date_time, format)
    return datetime_str

# look through the list of elements and ensure we just grab the Latest
# As the list is sorted in reverse from the bubble process, the latest event
# will be first. We just want to grab all the details of the one line and return it
def removeItems( objToWorkOn, itemToFind ):
    buildObj = objToWorkOn
    
    notFinished = True
    x = 0
    while notFinished == True:
        counter = 1
        y = 0
        itemSearch = True
        while itemSearch == True:
            #count number of items in itemToFind
            if objToWorkOn[y]['uniqueId'] == itemToFind:
                counter += 1
                y += 1
            else:
                y += 1
            
        try:
            canWeDoIt = objToWorkOn[y]["userId"]
        except:
            itemSearch = False
             
        if itemToFind == objToWorkOn[x]['uniqueId']:
            
            MyTestJson = {'itemNum': objToWorkOn[x]['itemNum'], 'uniqueId': objToWorkOn[x]['uniqueId'], 'date': objToWorkOn[x]['date'], 'timestamp': objToWorkOn[x]['timestamp']}
        
        buildObj.append(MyTestJson)
    
    if itemToFind == []:
        return objToWorkOn
    
    #Find Object
    if objToWorkOn[x]['uniqueId'] == itemToFind:
        print("Found Somethning")
    
    #Return a list of new 
    return(buildObj)

# Just retirn only one uniqueId from the events - ie remove the multiple events
def returnTheOne( theDupObj ):
    buildObj = theDupObj
    tmpObj = theDupObj
    x=0
    notFinished = True
    while notFinished == True:
        #Grab the first item - its sorted so it will be the right one
        theObjItem = tmpObj[x]['uniqueId']
        tmpObj = removeItems(tmpObj,theObjItem) #remove the rest of the items if any exist as we know this one we want as it was sorted
        
        try:
            x+=1
            canWeDoIt = tmpObj[x]["userId"]
        except:
            notFinished = False
        
        
        if theDupObj[x+1]['uniqueId'] == theObjItem:
            # we have what we need - remove the rest of these
            theDupObj = removeItems(theDupObj,theObjItem)
            x+=1
        else:
            x+=1
            
    
    return(buildObj)
    

def remObjectsInDict(origObj, dictDeleteList):
    a = origObj
    b = dictDeleteList
    a, b = [i for i in a if i not in b], [j for j in b if j not in a]
    origObj = a    
    return origObj

# process list items and return only those we want to work with
def retConsolidatedDict(objToProcess):
    buildObj = [] 
    # Lets sort the list
    # First create int time stamp to make sorting easier
    t=0
    while t < len(objToProcess):
        timestamp = int(round(objToProcess[t]['date'].timestamp()))
        MyJson = {'itemNum': t, 'uniqueId': objToProcess[t]['uniqueId'], 'date': objToProcess[t]['date'], 'timestamp': timestamp}
        buildObj.append(MyJson)
        t += 1
    # Sort the dict (generally should already be sorted from API but we don't know that yet)
    theReturnedObj = revBubbleSort(buildObj)
    
    counter = 0
    n = len(theReturnedObj)
    myGlobalObj = []
    # myGlobalObj.append(theReturnedObj[x])
    
    for l in range(n):
        for i in range(n):
            getElement = theReturnedObj[l]['uniqueId']
            getElementTime = theReturnedObj[l]['timestamp']
            if theReturnedObj[i]['uniqueId'] == getElement: counter += 1
            if (((theReturnedObj[i]['uniqueId'] == getElement) and (theReturnedObj[i]['timestamp'] == getElementTime)) and (counter == 1)): 
                myGlobalObj.append(theReturnedObj[l])
            if i == (n-1): counter = 0
    
    
    # newDictObj = remObjectsInDict(theReturnedObj, myGlobalObj)
   
    
    return(myGlobalObj)

def getRiskyUser():
    
    # Create a preferably long-lived app instance which maintains a token cache.
    app = msal.ConfidentialClientApplication(
        myclientid, authority=myauthority,
        client_credential=mysecret,

        )

    result = None

    result = app.acquire_token_silent(scopes=myscope, account=None)
   
    if not result:
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=myscope)

    if "access_token" in result:
        # Calling graph using the access token
        graph_data = requests.get( 
            myendpoint,
            headers={'Authorization': 'Bearer ' + result['access_token']}, ).json()
        
        grabData = json.loads(json.dumps(graph_data))
        myJSONdata = grabData["value"]

        newdict =[]
        y = 0
        while y < len(myJSONdata): 
            getDateTimeStr = myJSONdata[y]["detectedDateTime"]
            if len(getDateTimeStr) > 24:
                getDateTimeStr = getDateTimeStr[:-2]
            mkDateObj = convert(getDateTimeStr)
            newdict.append({'uniqueId': myJSONdata[y]["userId"],'date': mkDateObj})
            y += 1
        # Sort all elements and then de-duplicate

        selectedElements = retConsolidatedDict(newdict)

        slength = len(selectedElements)
        myJSONdataLength = len(myJSONdata)
        riskyUserObj = []
        # Looping through 
        for i in range(slength):
            for a in range(myJSONdataLength):
                getmyDateTimeStr = myJSONdata[a]["detectedDateTime"]
                if len(getmyDateTimeStr) > 24:
                    getmyDateTimeStr = getmyDateTimeStr[:-2]
                myRealDT = convert(getmyDateTimeStr)
                mytimestamp = int(round(myRealDT.timestamp()))
                if (myJSONdata[a]['userId'] == selectedElements[i]['uniqueId']) and (mytimestamp == selectedElements[i]['timestamp']):
                    # PUT THE WHILE LOOP HERE
                    riskyUserObj.append(myJSONdata[a])
                    
        
        myJSONdata = []
        notFinished = True
        x = 0
        while notFinished:
            theUniqueId = riskyUserObj[x]["userId"] #This is the true Azure AD Object of the User
            
            if riskyUserObj[x]["userDisplayName"] is not None:
                theName = riskyUserObj[x]["userDisplayName"]
                theNameSplit = theName.split(' ') #We have assumed the first and last name and No middle name
            else:
                theName = "Not Set"
            
            if riskyUserObj[x]["userPrincipalName"] is not None:
                theEmail = riskyUserObj[x]["userPrincipalName"]
            else:
                theEmail = "Not Set"
                    
            if riskyUserObj[x]["riskState"] is not None:
                theTagRiskState = riskyUserObj[x]["riskState"]
            else:
                theTagRiskState = "Not Set"

            if riskyUserObj[x]["riskLevel"] is not None:
                theTagRiskLevel = riskyUserObj[x]["riskLevel"]
                if theTagRiskLevel == "high":
                    theTagRiskLevel = "riskLevel-high"
                if theTagRiskLevel == "medium":
                    theTagRiskLevel = "riskLevel-medium"
                if theTagRiskLevel == "low":
                    theTagRiskLevel = "riskLevel-low"
                
            else:
                theTagRiskLevel = "Not Set"
                        
            if riskyUserObj[x]["ipAddress"] is not None:
                theIpAddress = riskyUserObj[x]["ipAddress"]
            else:
                theIpAddress = "Not Set"
            
            if riskyUserObj[x]["riskEventType"] is not None:
                theRiskEventType = riskyUserObj[x]["riskEventType"]
            else:
                theRiskEventType = "Not Set"
            
            if riskyUserObj[x]["detectionTimingType"] is not None:
                theDetectionTimingType = riskyUserObj[x]["detectionTimingType"]
            else:
                theDetectionTimingType = "Not Set"
            
            if riskyUserObj[x]["detectedDateTime"] is not None:
                theDetectedDateTime = riskyUserObj[x]["detectedDateTime"]
            else:
                theDetectedDateTime = "Not Set" 
            
            
            theDescription = 'Risk Event: ' + theRiskEventType + ' | IP Address: ' + theIpAddress + \
            ' | Detection Type: ' + theDetectionTimingType + ' | Detected: ' + theDetectedDateTime
            # removing quotations and other components want a clean value to post
            Dict = theDescription.strip('"')
            CreateDict = {"INFO": Dict }
            GetValuesOfStr = CreateDict["INFO"]
            SetupDesc = GetValuesOfStr
            
            if riskyUserObj != []:
                theBodyBuild = ({
                                "uniqueId": theUniqueId,
                                "name": theName,
                                "email": theEmail,
                                "firstName": theNameSplit[0],
                                "lastName": theNameSplit[1],
                                "description": SetupDesc,
                                "tags": [theTagRiskState, theTagRiskLevel, theRiskEventType],
                                "detectionTime": theDetectedDateTime
                                })
                
                body.append(theBodyBuild)
            else:
                print("Empty Data String!!!")
            
            try:
                x += 1
                canWeDoIt = riskyUserObj[x]["userId"]
            except:
                #If we get here end the While Loop
                notFinished = False

    else:
        print(result.get("error"))
        logging.info(result.get("error"))
        print(result.get("error_description"))
        logging.info(result.get("error_description"))
        print(result.get("correlation_id"))  # You may need this when reporting a bug
        logging.info(result.get("correlation_id"))
        
    # print("everything: ", myJSONdata)
    myJSONdata2 = {"data": body }
    body2 = myJSONdata2
    # body2 = json.dumps(test)
    #Now make a call to Authomize
    # print(body2)
    postRiskyUser(myAuthBaseURL,myAuthomizeAPIkey,myauthomizeRestAPIid,body2)
    
    
getRiskyUser()