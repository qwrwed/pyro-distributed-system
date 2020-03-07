# before running this, run:
# python -m Pyro4.naming
# TODO: add arguments

import Pyro4

@Pyro4.expose
class JHInterface(object):

    def __init__(self):
        self.__introMessage = "Welcome to Just Hungry!"
        self.__maxOrders = 10
        self.__menu = [
            "Chicken Burger",
            "Beef Burger",
            "Lamb Burger",
            "Cheese Burger",
            "Veggie Burger",
            "Turkey Burger"
        ]

    def run(self):
        return "Running"

    @property
    def introMessage(self):
        return self.__introMessage
    
    @property
    def menu(self):
        return self.__menu
    
    @property
    def maxOrders(self):
        return self.__maxOrders

#daemon = Pyro4.Daemon(host="192.168.1.66")                # make a Pyro daemon
daemon = Pyro4.Daemon()
ns = Pyro4.locateNS()                  # find the name server
uri = daemon.register(JHInterface)     # register the class as a Pyro object
ns.register("JH.Interface", uri)         # register the object with a name in the name server
print(uri)

print("Ready for client connection...")
daemon.requestLoop()                   #  