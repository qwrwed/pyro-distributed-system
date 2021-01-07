# CREATED USING PYTHON 3.7.4 - MAY NOT WORK ON OLDER VERSIONS
# before running this program, ensure the nameserver is running (in another terminal window)
#   python -m Pyro4.naming [--host {HOST} [--port {PORT}]]
# default host is localhost, default port is 9090

# Passive Replication:
# To run multiple backends (system supports up to 3) there are two options:
#  1. Duplicate this file twice and rename such that there are 3 identical files, then run them all
#     "python backend1.py", "python backend2.py", "python backend3.py"
#  2. Have just one copy of this file and run multiple times with the server index as a command-line argument:
#     "python ./backend.py 1" ,"python ./backend.py 2", "python ./backend.py 3"
# Note: the command-line arguent takes precedence over the file name.

import Pyro4
import sys
import re

selfAddress = None# defaults to localhost
selfPort = 0 # defaults to 9090

@Pyro4.expose
class OrderContainer(object):
    # each server has its own instance of orderContainer
    def __init__(self, orders = list()):
        self.__orders = orders
        self.__nextOrder = 1
    
    @property
    def orders(self):
        return self.__orders
    
    @property
    def nextOrder(self):
        return self.__nextOrder

    def add(self, order):
        orderNumber = self.__nextOrder
        #self.orderDict.append(order)
        order['id'] = orderNumber
        self.__nextOrder += 1

        self.__orders.append(order)
        #self.orderDict[orderNumber] = order
        print(f"Adding order to orderlist. Order: {order}")
        print(f"New order list on this server: {self.__orders}")
        return orderNumber

    def overwrite(self, receivedOrderContainer, source=None):
        if not source == None:
            sourceString = f' from server {source}'
        else:
            sourceString = ''

        self.__orders = receivedOrderContainer.orders
        self.__nextOrder = receivedOrderContainer.nextOrder
        print(f"Receiving overwrite data{sourceString}.")
        print(f"New order list on this server: {self.__orders}")

    @orders.setter
    def orders(self, new):
        self.__orders = new

numberOfServers = 3

if len(sys.argv) == 1:
    fileName = sys.argv[0]
    pattern = re.compile(r'^backend([0-9]+).py$')
    if pattern.match(fileName) != None:
        thisServer = int([m.groups()[0] for m in pattern.finditer(fileName)][0])
    else:
        print(r"Missing server number: give it as command line argument ('python backend.py {number}'), or rename this file to 'backend{number}.py'")
        sys.exit(1)
elif len(sys.argv) == 2:
    thisServer = sys.argv[1]
    if not thisServer.isdigit():
        print("Server number argument is not a number")
        sys.exit(1)
    thisServer = int(thisServer)
else:
    print("Error: Too many arguments")
    sys.exit(1)

if thisServer not in range(1, numberOfServers+1):
    print(f"Server number argument outside range (1-{numberOfServers})")

#thisServer = 1

OrderContainers = dict()

JHOrderContainer = OrderContainer()

for serverNumber in range(1, numberOfServers+1):
    # set up OrderContainer proxies for all other servers
    if serverNumber != thisServer:
        OrderContainers[serverNumber] = Pyro4.Proxy(f"PYRONAME:JHOrderContainer{serverNumber}")
        # FAILURE TRANSPARENCY: If the other server(s) are already active, the OrderContainer with the most elements...
        #  from those servers will be copied into this server's OrderContainer, allowing this server to be brought up to date after a failure and recovery
        try:
            if len(OrderContainers[serverNumber].orders) > len(JHOrderContainer.orders):
                JHOrderContainer.overwrite(OrderContainers[serverNumber], serverNumber)
        except:
            pass


def validateOrder(order):
    try:
        if len(order['content']) == 0:
            return False, f"No items ordered"
        # check these exist:
        order['address']['postcode']
        order['address']['building']
    except KeyError as e:
        return False, f"Order is missing {e}"
    return True, None

@Pyro4.expose
class JHBridgeFB(object):
    def ping(self):
        return True

    def request(self, client, requestType, requestContent=None):
        # 0: request completed successfully
        # 1: request failed due to client error
        # 2: request failed due to server error
        
        print(f"Request recieved. Type: {requestType}, content: {requestContent}")
        responseCode = 0
        if requestType == 'getIntroMessage':
            responseContent = "Welcome to Just Hungry!"
            responseCode = 0
        elif requestType == 'getMenu':
            responseContent = [
                "Chicken Burger",
                "Beef Burger",
                "Lamb Burger",
                "Cheese Burger",
                "Veggie Burger",
                "Turkey Burger"
            ]
        elif requestType == 'getMaxQuantity':
            responseContent = 10
        elif requestType == 'postOrder':
            order = requestContent
            orderValid, invalidError = validateOrder(order)
            if orderValid:
                order['client'] = client
                JHOrderContainer.add(order)
                
                responseCode = 0
                responseContent = order

                for index in OrderContainers:
                    try:
                        OrderContainers[index].overwrite(JHOrderContainer, thisServer)
                        print(f"Information sent to server {index}")
                    except Pyro4.errors.ConnectionClosedError as e:
                        print(f"Could not send information to server {index}")
                    except Pyro4.errors.CommunicationError as e:
                        print(f"Could not send information to server {index}")
                    except Pyro4.errors.NamingError as e:
                        print(f"Could not send information to server {index}")
                print()
            else:
                responseCode = 1
                responseContent = invalidError
        elif requestType == 'getOrders':
            responseContent = [order for order in (JHOrderContainer.orders) if order['client'][0] == client[0]] # match IP address
            responseCode = 0
        else:
            responseContent = 'Request unrecognised'
            responseCode = 1

        return {'code': responseCode, 'content': responseContent}
    
print(f"Backend server {thisServer} ready for frontend connection")
# LOCATION TRANSPARENCY: Use a nameserver to serve backend options, which are only accessed by the frontend
#   The client only uses the location of the frontend; the location of the backend is hidden from the client in this way
# RELOCATION TRANSPARENCY: Use of the nameserver means that this file can be hosted anywhere, under any filename (provided the server index is given),
#  and the nameserver will still serve it to the frontend using the same Pyroname
Pyro4.Daemon.serveSimple(
    {
        JHOrderContainer: f"JHOrderContainer{thisServer}",
        JHBridgeFB: f"JH.BridgeFB{thisServer}"
    },
    host=selfAddress,
    port=selfPort,
    verbose=False,
)