import Pyro4
import sys

nextRequestId = 0
# function to display (usually static) string with (usually dynamic) info underneath, after 'clearing' terminal with newlines
def printWithInfo(s, info='', newlines = 50):
    print('\n'.join(['\n'*newlines, s, info]))

# main function sets up proxy, then repeatedly calls placeOrder until the user chooses to exit
def main():

    nameServerAddress = None#"192.168.1.66"
    nameServerPort = None#18000

    nameString = "PYRONAME:JH.BridgeCF"
    if not nameServerAddress == None:
        nameString += f"@{nameServerAddress}"
        if not nameServerPort == None:
            nameString += f":{nameServerPort}"
    JHBridgeCF = Pyro4.Proxy(nameString)

    willPlaceOrder = True
    try:
        while willPlaceOrder == True:
            willPlaceOrder = placeOrder(JHBridgeCF)
    except Pyro4.errors.NamingError as e:
        print("ERROR: Failed to connect to server")
        sys.exit(1)

# generic function for making requests of all types to the frontend, which will pass it to a DS component and return the reponse in a standardised format
def makeRequest(JHBridgeCF, requestType, requestContent = None):
    global nextRequestId
    #return JHBridgeCF.request(nextRequestId, requestType, requestContent)
    
    # if no response was received, resend request (with same id to ensure duplicate requests do not get executed)
    maxAttempts = 3
    for attempt in range(maxAttempts):
        try:
            response = JHBridgeCF.request(nextRequestId, requestType, requestContent)
            nextRequestId += 1
            return response
        except:
            if attempt < maxAttempts-1: 
                continue
            else:
                print(f"Failed to connect to server after {maxAttempts} attempts. Service unavailable; please try again later.")
                sys.exit(1)

def stringifyOrder(order, menu):
    orderStringList = []
    if 'id' in order:
        orderStringList.append(f"Order number: {order['id']}")
    orderStringList.append(f"Items ordered:")
    if len(order['content']) > 0:
        orderStringList.append(', '.join([f"{menu[orderNumber]} x{order['content'][orderNumber]}" for orderNumber in order['content']]))
    else:
        orderStringList.append("No items added to menu")
    orderStringList.append(f"Delivery address:")
    try:
        orderStringList.append(f"{order['address']['building']} {order['address']['postcode']}")
    except KeyError:
        orderStringList.append(f"Not set")
    
    return '\n'.join(orderStringList)

def placeOrder(JHBridgeCF):
    order = {
        'content': dict(),
        'address': dict()
    }
    # format of order is {orderContent = { orderNumber: orderQuantity, ... }, orderAddress = {orderPostcode, orderBuilding}}

    mainMenu = '\n'.join([
        "1: Select food items",
        "2: Enter delivery address",
        "3: Display order",
        "4: Submit order",
        "0: Exit"
    ])

    introMessage = makeRequest(JHBridgeCF, 'getIntroMessage')['content']
    
    mainMenuInfo = ''
    menu = []
    while True:
        printWithInfo(f"{introMessage}\n{mainMenu}", mainMenuInfo)
        userChoice = input("Select an option: ")
        info=''
        if userChoice == '1': # add content to order
            while True:
                modified = False
                menu = makeRequest(JHBridgeCF, 'getMenu')['content']
                maxOrders = makeRequest(JHBridgeCF, 'getMaxOrders')['content']
                menuString = '\n'.join([f"{index+1}: {menu[index]}" for index in range(len(menu))])
                printWithInfo(menuString, info)
                orderNumber = input("Enter item's number (leave blank to exit):  ")
                if orderNumber == "":
                    break
                elif not orderNumber.isdigit():
                    info = "Invalid input: Not a number"
                    continue
                elif int(orderNumber)-1 in range(len(menu)):
                    orderNumber = int(orderNumber) - 1
                    info = f"You have chosen {menu[orderNumber]}"
                else:
                    info = "Invalid input: Unrecognised"
                    continue
                while True:
                    printWithInfo(menuString, info)
                    orderQuantity = input("Enter quantity (leave blank for 1): ")
                    if orderQuantity == "":
                        orderQuantity = 1
                        break
                    elif not orderQuantity.isdigit():
                        info = "Invalid input: Not a number"
                        continue
                    orderQuantity = int(orderQuantity)
                    if orderQuantity > maxOrders:
                        info = f"Quantity too high, maximum is {maxOrders}" 
                        continue
                    elif orderQuantity == 0:
                        del order['content'][orderNumber]
                        info = f"{menu[orderNumber]} removed from order"
                        break
                    else: # valid
                        break
                modified = True
                if orderQuantity > 0:
                    info = f"Added {menu[orderNumber]} (x{orderQuantity}) to order"
                    printWithInfo(menuString, info)
                    order['content'][orderNumber] = orderQuantity
                if modified:
                    mainMenuInfo = 'Order updated'
                else:
                    mainMenuInfo = ''
        elif userChoice == '2': # enter address
            postcodeValid = False
            while True:
                printWithInfo('', info)
                postcode = input("Enter your postcode (leave blank to cancel): ")
                if postcode == "":
                    break
                response = makeRequest(JHBridgeCF, 'validatePostCode', postcode)
                if response['code'] == 0: #valid
                    postcodeValid = True
                    postcode = response['content']
                    break
                else: # invalid
                    info = response['content']
                    continue
            if postcodeValid:
                building = input("Enter building name or number: ")
                order['address']['postcode'] = postcode
                order['address']['building'] = building
                mainMenuInfo = f"Delivery address set to {building} {postcode}"
            else:
                mainMenuInfo = ''
        elif userChoice == '3': #display order
            printWithInfo(stringifyOrder(order, menu), "Press Enter to continue")
            input()
        elif userChoice == '4': # Submit order
            response = makeRequest(JHBridgeCF, 'postOrder', order)
            if response['code'] == 0:
                print("Your order has been confirmed")
                orderResponse = response['content']
                print(stringifyOrder(orderResponse, menu))
                print(f"Please retain this information as proof of purchase.")
                while True:
                    orderAgain = input(f"Would you like to place another order? (y/N): ")
                    if orderAgain == '' or orderAgain.upper() == 'N':
                        return False
                    elif orderAgain.upper() == 'Y':
                        return True
                    else:
                        print('Unrecognised')
            elif response['code'] == 1:
                mainMenuInfo = f"Invalid order: {response['content']}"

        elif userChoice == '0':
            return False
        else:
            mainMenuInfo = "Unrecognised input"

if __name__ == '__main__':
    main()


