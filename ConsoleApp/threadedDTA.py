import sys
import requests
import json
from threading import Thread

headerInfo = {"Content-Type":"application/json", "X-Requested-With":"XMLHttpRequest"}
userDict = {}
userHeaders = {}
s = requests.Session()
count = 0

def fileProcessor():

    with open(sys.argv[1]) as f: #Reading in the file
        lines = f.readlines() 

    lines_formatted = [] 

    for i in range(len(lines)): #String formatting and appending to larger list
        without_line_breaks = lines[i].replace("\n","")
        separate_by_comma = without_line_breaks.split(",")
        lines_formatted.append(separate_by_comma)
        lines_formatted[i][0] = lines_formatted[i][0].split(" ")

    fname = lines_formatted[i][1]

    for j in range(len(lines_formatted)):
        if lines_formatted[j][0][1] == "ADD":
            userDict[lines_formatted[j][1]] = []


    for key in userDict:
        for element in lines_formatted:
            
            if (element[1].strip(" ")==key):
                userDict[key] += [element]

    return userDict, fname

def requestManager(batch,username):

    print("ENTERING REGISTRATION PHASE FOR " + username)

    endpoint = "localhost:8000/api/create_user"
    payload = {"username":username + "@gmail.com", "name":username, "password":username}

    r = s.post(url = endpoint, data = payload, headers = headerInfo)
    res = r.json()

    # if ("errors" in res):

    #     print("REGISTRATION FAIL TRYIN TO LOG IN")
    #     endpoint = "localhost:8000/api/users/login/"
    #     payload = {"user": {"email":username + "@gmail.com", "password":username}}

    #     r = s.post(url = endpoint, data = payload, headers = headerInfo)
    #     # print(r.text)
    #     res = r.json()
        

    #     if ("errors" in res):
    #         print("ERROR UNABLE TO LOGIN OR REGISTER")
            #exit() 
        
        # print("LOG IN SUCCESSFUL FOR " + username)

    token = "d0946e53d85e7a611ba84f813b7c8ee7269d1c2cbf5dec78a1d3636c25851865d5eed5b99d96fefe6da6f456c281f52ba11040cf921bdd1a281f94a9973bda77"
    tempHeader = headerInfo
    tempHeader["Authorization"] = token
    userHeaders[username] = tempHeader

    print("AUTHENTICATION SUCCESSFUL FOR " + username)
    
    for element in batch:
        # print(count)
        # print(element[0][1])
        if element[0][1] == "ADD":
            username = element[1]
            amount = element[2].strip(" ")
            endpoint = "localhost:8000/api/add/"
            payload = {"username" : username, "amount" : amount}
            
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])
            # print("ADD ->  Status Code = " + str(r.status_code) + "\n" + r.text)
            # if(r.status_code == 500):

            #     f = open("errors.txt","w",encoding="utf-8")
            #     f.write(r.text)

            # print("ADD ->  " + r.text)

        if element[0][1] == "QUOTE":
            username = element[1]
            ticker = element[2].strip(" ")
            endpoint = "localhost:8000/api/quote"
            parameters = {"username":username,"ticker": ticker}   

            r = s.get(url=endpoint, params=parameters, headers=userHeaders[username])
            # print("QUOTE ->  " + r.text)
        if element[0][1] == "BUY":
            username = element[1]
            ticker = element[2]
            amount = element[3].strip(" ")

            endpoint = "localhost:8000/api/buy"
            payload = {"username" : username, "ticker" : ticker, "amount" : amount}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])
            # print("BUY ->  Status Code = " + str(r.status_code) + "\n" + r.text)
        if element[0][1] == "COMMIT_BUY":
            username = element[1].strip()
            endpoint = "localhost:8000/api/commitbuy/"
            payload = {"username" : username}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])
            # print("COMMIT_BUY ->  Status Code = " + str(r.status_code) + "\n" + r.text)     
        if element[0][1] == "CANCEL_BUY":
            username = element[1].strip()
            endpoint = "localhost:8000/api/cancelbuy/"
            payload = {"username" : username}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])
            # print("CANCEL_BUY ->  " + r.text)
        if element[0][1] == "SELL":
            username = element[1]
            ticker = element[2]
            amount = element[3].strip()
            endpoint = "localhost:8000/api/sell/"
            payload = {"username" : username, "ticker" : ticker, "amount" : amount}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])
            # print("SELL ->  " + r.text)
        if element[0][1] == "COMMIT_SELL":
            username = element[1].strip()
            endpoint = "localhost:8000/api/commitsell/"
            payload = {"username" : username}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("COMMIT_SELL ->  " + r.text)
        if element[0][1] == "CANCEL_SELL":
            username = element[1].strip()
            endpoint = "localhost:8000/api/cancelsell/"
            payload = {"username" : username}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("CANCEL_SELL ->  " + r.text)
        if element[0][1] == "SET_BUY_AMOUNT":
            username = element[1]
            ticker = element[2]
            amount = element[3].strip()
            endpoint = "localhost:8000/api/setbuyamount/"
            payload = {"username" : username, "ticker" : ticker, "amount" : amount}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("SET_BUY_AMOUNT ->  " + r.text)
        if element[0][1] == "CANCEL_SET_BUY":
            username = element[1]
            ticker = element[2].strip()
            endpoint = "localhost:8000/api/cancelsetbuy/"
            payload = {"username" : username, "ticker" : ticker}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("CANCEL_SET_BUY ->  " + r.text)
        if element[0][1] == "SET_BUY_TRIGGER":
            username = element[1]
            ticker = element[2]
            amount = element[3].strip()
            endpoint = "localhost:8000/api/setbuytrigger/"
            payload = {"username" : username, "ticker" : ticker, "amount" : amount}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("SET_BUY_TRIGGER ->  " + r.text)
        if element[0][1] == "SET_SELL_AMOUNT":
            username = element[1]
            ticker = element[2]
            amount = element[3].strip()
            endpoint = "localhost:8000/api/setsellamount/"
            payload = {"username" : username, "ticker" : ticker, "amount" : amount}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("SET_SELL_AMOUNT ->  " + r.text)
        if element[0][1] == "SET_SELL_TRIGGER":
            username = element[1]
            ticker = element[2]
            amount = element[3].strip()
            endpoint = "localhost:8000/api/setselltrigger/"
            payload = {"username" : username, "ticker" : ticker, "amount" : amount}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username])           
            # print("SET_SELL_TRIGGER ->  " + r.text)
        if element[0][1] == "CANCEL_SET_SELL":
            username = element[1]
            ticker = element[2].strip()
            endpoint = "localhost:8000/api/cancelsetsell/"
            payload = {"username" : username, "ticker" : ticker}
            r = s.post(url=endpoint, data=payload, headers=userHeaders[username]) 
            # print("CANCEL_SET_SELL ->  " + r.text)
        if element[0][1] == "DISPLAY_SUMMARY":
            username = element[1].strip()
            endpoint = "localhost:8000/api/displaysummary"
            parameters = {"username":username}        
            r = s.get(url = endpoint, params=parameters)
            # print("DISPLAY SUMMARY")
        global count
        count += 1
        print(count)

def main():

    iterationDict,fname = fileProcessor()
    

    threads = [Thread(target=requestManager, args=(iterationDict[key],key)) for key in iterationDict]

    for thread in threads:
        thread.start()

    for t in threads:
        t.join()

    
    endpoint = "localhost:8000/api/dumplog/"  
    r = s.get(url = endpoint)
    res = r.json()

    f = open(fname + ".xml", "w+", encoding="utf-8")
    f.write(r.text)
    print("DUMPLOG")

    

if __name__ == '__main__':
    main()
