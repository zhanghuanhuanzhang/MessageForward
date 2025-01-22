#!/usr/bin/python

import socket

class TcpClientHandler:
    """Handles the creation and management of TCP connections."""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connection = None
    
    def EstablishConnection(self):
        """Establish a TCP connection."""
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((self.host, self.port))
    
    def SendData(self, data):
        """Send data through the connection."""
        if self.connection:
            self.connection.sendall(data)
    
    def ReceiveData(self, bufferSize=4096):
        """Receive data from the connection."""
        if self.connection:
            return self.connection.recv(bufferSize)
    
    def CloseConnection(self):
        """Close the TCP connection."""
        if self.connection:
            self.connection.close()

def Main():
    # Define server addresses and ports for two connections
    host1, port1 = "127.0.0.1", 60001  # Replace with actual server1 details
    host2, port2 = "127.0.0.1", 60002  # Replace with actual server2 details

    # Create two TCP client handlers
    client1 = TcpClientHandler(host1, port1)
    client2 = TcpClientHandler(host2, port2)

    try:
        # Establish connections
        client1.EstablishConnection()
        client2.EstablishConnection()

        # Data to send
        dataToSend = "Hello, this is a test message!"

        # Send data to the first connection
        client1.SendData(dataToSend)
        print("Sent: {}".format(dataToSend))

        # Receive data from the second connection
        receivedData = client2.ReceiveData()
        print("Received: {}".format(receivedData))

        # Compare sent and received data
        if dataToSend == receivedData:
            print("Success: Sent and received data match!")
        else:
            print("Error: Sent and received data do not match!")
    finally:
        # Close both connections
        client1.CloseConnection()
        client2.CloseConnection()

if __name__ == "__main__":
    Main()