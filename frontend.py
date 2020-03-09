import Pyro4
import json
import urllib.request
import re

numberOfServers = 3
JHBridgeFB = None

# LOCATION TRANSPARENCY: Connections to all backend servers are performed here on the frontend, not the client
# REPLICATION TRANSPARENCY: The setBridge function causes the frontend to decide which replicated backend should act as the primary backend to forward client messages to
# it is assumed that all programs are connected to the same nameserver; for different nameservers, modify nameServerAddresses and nameServerPorts
def setBridge():

    nameServerAddresses = [None]*numberOfServers
    nameServerPorts = [None]*numberOfServers

    global JHBridgeFB
    JHBridgeFB = None
    for serverNumber in range(1, numberOfServers+1):
        try:
            nameString = f"PYRONAME:JH.BridgeFB{serverNumber}"
            if not nameServerAddresses[serverNumber-1] == None:
                nameString += f"@{nameServerAddresses[serverNumber-1]}"
                if not nameServerPorts[serverNumber-1] == None:
                    nameString += f":{nameServerPorts[serverNumber-1]}"
            potentialJHBridgeFB = Pyro4.Proxy(nameString)
            response = potentialJHBridgeFB.ping()
            if response == True:
                print("Primary server:", serverNumber)
                primaryServerIndex = serverNumber
                JHBridgeFB = potentialJHBridgeFB
                return
        except Pyro4.errors.CommunicationError:
            print(f"Failed to connect to server {serverNumber}")
        except Pyro4.errors.NamingError:
            print(f"Failed to connect to server {serverNumber}")
    print("Could not connect to any servers")
    return

setBridge()

@Pyro4.expose
class JHBridgeCF(object):

    def __init__(self):
        self.__completedRequests = []

    def request(self, requestId, requestType, requestContent=None):
        print(self.__completedRequests)
        # 0: request completed successfully
        # 1: request failed due to client error
        # 2: request failed due to server error (or result of server error)

        if requestId in self.__completedRequests:
            return {'code': 2, 'content': 'Request already completed'}
        
        print(f"Request recieved. Type: {requestType}, content: {requestContent}")
        validClientRequests = ['getIntroMessage', 'getMenu', 'getMaxOrders', 'postOrder', 'validatePostCode']
        if requestType == 'validatePostCode':
            
            postcode = ' '.join(requestContent.upper().split())

            postcodePattern = re.compile(r'^[A-Z0-9 ]+$')
            if postcodePattern.match(postcode) == None:
                self.__completedRequests.append(requestId)
                return {'code': 1, 'content': "Invalid postcode"}

            postcodeNoSpaces = postcode.replace(' ', '%20')
            try:
                res = urllib.request.urlopen(f"http://api.postcodes.io/postcodes/{postcodeNoSpaces}/validate")
                str_response = res.read().decode('utf-8')
                js = json.loads(str_response)
                result = js['result']
            except urllib.error.URLError:
                try:
                    res = urllib.request.urlopen(f"http://api.getthedata.com/postcode/{postcodeNoSpaces}")
                    str_response = res.read().decode('utf-8')
                    js = json.loads(str_response)
                    result = js['status'] == 'match' and js['match_type'] == 'unit_postcode'
                except urllib.error.URLError:
                    self.__completedRequests.append(requestId)
                    return {'code': 2, 'content': 'Could not verify postcode, please retry later'}
            if result == True:
                self.__completedRequests.append(requestId)
                return {'code': 0, 'content': postcode}
            else:
                self.__completedRequests.append(requestId)
                return {'code': 1, 'content': 'Invalid postcode'}
                

        elif requestType in validClientRequests:
            for _ in range(1):
                try:
                    response = JHBridgeFB.request(requestType, requestContent)
                    print(f"Response recieved: {response}")
                    self.__completedRequests.append(requestId)
                    return response
                    # FAILURE TRANSPARENCY: On failure to connect, switch to a functional backend and try again
                except Pyro4.errors.ConnectionClosedError as e:
                    setBridge()
                except AttributeError as e:
                    setBridge()
            self.__completedRequests.append(requestId)
            return {'code': 2, 'content': 'ERROR: Failed to connect to server'}
                
        else:
            self.__completedRequests.append(requestId)
            return {'code': 1, 'content': 'Invalid request type'}


daemon = Pyro4.Daemon()
ns = Pyro4.locateNS()
uri = daemon.register(JHBridgeCF)
ns.register("JH.BridgeCF", uri)
print("Ready for client connection...")
daemon.requestLoop()