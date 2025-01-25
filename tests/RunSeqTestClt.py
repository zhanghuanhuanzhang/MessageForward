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

        # Prepare binary data to send (0~255 repeated 500 times)
        binaryData = ''.join([chr(i) for i in range(256)])  # Total 256 * 500 bytes
        # for index, byte in enumerate(binaryData):
        #     print("Byte {}: {}".format(index, ord(byte)))

        # Send binary data to the first connection
        cnt = 1
        for i in range(cnt):
            client1.SendData(binaryData)
        print("Sent binary data of size: {} bytes".format(len(binaryData) * cnt))

        # Receive data from the second connection
        client2.SendData("client2\0")
        cmpT = 0
        rst = True
        receivedData = b""
        while len(receivedData) < len(binaryData) * cnt:
            chunk = client2.ReceiveData(4096)
            # Verify
            for i in chunk:
                if ord(i) != cmpT:
                    rst = False
                cmpT = (cmpT + 1) % 256
            if not chunk:
                break
            receivedData += chunk
        
        print("Received binary data of size: {} bytes".format(len(receivedData)))

        # # Verify that sent and received data match
        # for i in receivedData:
        #     print(repr(i))
        #     if ord(i) != cmpT:
        #         rst = False
        #         break
        #     cmpT = (cmpT + 1) % 256

        if rst:
            print("Success: Sent and received data match!")
        else:
            print("Error: Sent and received data do not match!")

        # # Display the binaryData byte by byte
        # print("Sent binary data (byte by byte):")
        # for index, byte in enumerate(binaryData):
        #     print("Byte {}: {}".format(index, ord(byte)))
    finally:
        # Close both connections
        client1.CloseConnection()
        client2.CloseConnection()

if __name__ == "__main__":
    Main()

