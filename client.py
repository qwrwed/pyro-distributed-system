import Pyro4

def main():
    willPlaceOrder = True
    while willPlaceOrder == True:
        willPlaceOrder = placeOrder()

def placeOrder():
    #JHInterface = Pyro4.Proxy("PYRONAME:JH.Interface@192.168.1.66:18000")    # use name server object to lookup uri shortcut
    JHInterface = Pyro4.Proxy("PYRONAME:JH.Interface")    
    #print(JHInterface.introMessage)
    #runOutput = JHInterface.run()
    #print(runOutput)
    mainMenu = '\n'.join([
        "1: Select food items",
        "2: Enter delivery address",
        "3: Review order",
        "0: Exit"
    ])
    #print("Welcome to Just Hungry!") #replace with server-side intro message?
    print(JHInterface.introMessage)
    while True:
        print(mainMenu)
        userChoice = input("Select an option: ")
        if userChoice == '1':            
            while True:
                print('\n'.join([f"{index+1}: {JHInterface.menu[index]}" for index in range(len(JHInterface.menu))]))
                orderNumber = input("Enter item's number (leave blank to exit): ")
                if orderNumber == "":
                    break
                elif not orderNumber.isdigit():
                    print("not a number")
                    continue
                elif int(orderNumber)-1 in range(len(JHInterface.menu)):
                    orderNumber = int(orderNumber) - 1
                    print(f"You have chosen {JHInterface.menu[orderNumber]}")
                    #check if orderNumber already in orderContent
                else:
                    print("Unrecognised")
                    continue
                
                while True:
                    orderQuantity = input("Enter quantity (leave blank for 1): ")
                    if orderQuantity == "":
                        orderQuantity = 1
                        break
                    elif not orderQuantity.isdigit():
                        print("not a number")
                        continue
                    elif int(orderQuantity) > JHInterface.maxOrders:
                        print(f"Too many orders, maximum is {JHInterface.maxOrders}")
                        continue
                    elif int(orderQuantity) == 0:
                        print("cancelling")
                        break
                    else:
                        orderQuantity = int(orderQuantity)
                        print("good number")
                        break
                    
                if orderQuantity > 0:
                    print(f"Adding {JHInterface.menu[orderNumber]} (x{orderQuantity}) to order")
                    # then add orderNumber and orderQuantity to order
        elif userChoice == '2':
            while True:
                postCode = input("Enter your postcode (leave blank to cancel): ")
                if postCode == "":
                    break
                #then validate the postcode
                postCodeValid = True
                if postCodeValid:
                    building = input("Enter building name or number: ")
                print(f"Delivery address set to {building} {postCode}")
        elif userChoice == '3':
            #submit orderDict = {orderContent = { orderNumber: orderQuantity, ... }, orderAddress = {orderPostcode, orderBuilding}}
            #return value = orderID
            orderID = 66
            print(f"Your order:")
            print(f"Order number: {orderID}")
            print(f"Delivery address: ")
            print(f"Items ordered:")
            print(f"Please retain this information as proof of purchase.")
            print()
            while True:
                orderAgain = input(f"Would you like to place another order? (y/N): ")
                if orderAgain == '' or orderAgain.upper() == 'N':
                    return False
                elif orderAgain.upper() == 'Y':
                    return True
                else:
                    print('Unrecognised')

        elif userChoice == '0':
            return False
        else:
            print("Unrecognised")





if __name__ == '__main__':
    main()


