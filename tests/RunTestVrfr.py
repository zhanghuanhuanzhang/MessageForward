#!/usr/bin/python
'''
    This program runs together with RunTestVrfr.py.
    The data go this way:

        RunTestSndr.py(Sender) ---> MessageForward(MsgFwdr) ---> RunTestVrfr.py(Receiver)

    No matter in which sequence the Sender & Receiver are run, and no matter how many times Sender & Receiver
    are stopped and run again. The TestVrfr should receive the correct result.

    Receiver will only accept 0, 1, 2 ... 255 loop indefinitely.
'''
import socket
import sys

class RunTestVrfr:
    def __init__(self, host, port):
        """Initializes the RunTestVrfr class with socket details."""
        self.host = host  # Server host to connect to
        self.port = port  # Server port to connect to
        self.sock = None  # Socket object
        self.expectedByte = 0  # Tracks the expected byte for verification
        self.running = False  # Tracks whether the verification is active

    def StartReceiving(self):
        """Starts the byte receiving and verification process."""
        self.running = True
        self._SetupSocket()
        self._ReceiveAndVerify()

    def StopReceiving(self):
        """Stops the receiving process and closes the socket."""
        self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None

    def _SetupSocket(self):
        """Sets up the TCP client socket connection."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.sock.sendall('client2\0')
            print("Connected to {}:{}".format(self.host, self.port))
        except socket.error as e:
            print("Failed to connect to {}:{} - {}".format(self.host, self.port, e))
            self.running = False

    def _ReceiveAndVerify(self):
        """Receives data from the socket and verifies the content."""
        try:
            while self.running:
                data = self.sock.recv(1024)  # Receive up to 1024 bytes at a time
                if not data:
                    print("Connection closed by server.")
                    break

                for byte in data:
                    receivedByte = ord(byte)  # Convert the byte to an integer
                    if receivedByte != self.expectedByte:
                        print("Verification failed! Expected: {}, Received: {}".format(self.expectedByte, receivedByte))
                        # self.StopReceiving()
                        # return

                    sys.stdout.write(repr(byte))
                    sys.stdout.flush()

                    self.expectedByte += 1
                    if self.expectedByte > 255:
                        self.expectedByte = 0

                    # print("Verified byte:", receivedByte)
        except socket.error as e:
            print("Error during receiving or verification - {}".format(e))
        finally:
            self.StopReceiving()

# Example usage
if __name__ == "__main__":
    host = "127.0.0.1"  # Change to your server's IP address
    port = 60002         # Change to your server's port number

    receiver = RunTestVrfr(host, port)
    try:
        print("Starting to receive and verify bytes...")
        receiver.StartReceiving()
    except KeyboardInterrupt:
        print("\nStopping the receiver...")
        receiver.StopReceiving()
