#!/usr/bin/python
'''
    This program runs together with RunTestVrfr.py.
    The data go this way:

        RunTestSndr.py(Sender) ---> MessageForward(MsgFwdr) ---> RunTestVrfr.py(Receiver)

    No matter in which sequence the Sender & Receiver are run, and no matter how many times Sender & Receiver
    are stopped and run again. The TestVrfr should receive the correct result.

    Sender will send 0, 1, 2 ... 255 loop indefinitely.
'''
import time
import threading
import socket
import sys

class ByteSender:
    def __init__(self, interval, host, port):
        """Initializes the ByteSender class with a configurable interval and socket details."""
        self.interval = interval  # Interval in seconds
        self.currentByte = 0  # Tracks the current byte being sent
        self.running = False  # Tracks whether the sending is active
        self.lock = threading.Lock()  # To ensure thread safety when modifying variables
        self.host = host  # Target host
        self.port = port  # Target port
        self.sock = None  # Socket object

    def StartSending(self):
        """Starts the byte sending process."""
        self.running = True
        self._SetupSocket()
        self._SendBytes()

    def StopSending(self):
        """Stops the byte sending process and closes the socket."""
        with self.lock:
            self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None

    def _SetupSocket(self):
        """Sets up the TCP socket connection."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print("Connected to {}:{}. Ready to send bytes.".format(self.host, self.port))
        except socket.error as e:
            print("Failed to connect to {}:{} - {}".format(self.host, self.port, e))
            self.running = False

    def _SendBytes(self):
        """Private method to send bytes in a loop until stopped."""
        while True:
            with self.lock:
                if not self.running:
                    break
                try:
                    x = chr(self.currentByte)
                    self.sock.sendall(x)  # Send the current byte
                    sys.stdout.write(repr(x))
                    sys.stdout.flush()

                    self.currentByte += 1
                    if self.currentByte > 255:
                        self.currentByte = 0

                except socket.error as e:
                    print("\nError sending byte - {}".format(e))
                    self.StopSending()
                    break

            time.sleep(self.interval)  # Wait for the configured interval

# Example usage
if __name__ == "__main__":
    host = "127.0.0.1"  # Change to your server's IP address
    port = 60001         # Change to your server's port number
    interval = 0.5       # Configurable interval in seconds (e.g., 0.5 seconds)

    sender = ByteSender(interval, host, port)
    try:
        print("Starting to send bytes...")
        sender.StartSending()
    except KeyboardInterrupt:
        print("\nStopping the sender...")
        sender.StopSending()
