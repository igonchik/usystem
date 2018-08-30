import os
import asyncio
import _thread
import time
import socket


class UFileTransfer:
    @staticmethod
    def file_transfer_client(filename, host, port):
        s = socket.socket()  # Create a socket object
        s.connect((host, port))
        f = open(filename, 'rb')
        print('Sending...')
        line = f.read(1024)
        while line:
            print('Sending...')
            s.send(line)
            line = f.read(1024)
        f.close()
        print("Done Sending")
        print(s.recv(1024))
        s.shutdown(socket.SHUT_WR)  # Close the socket when done
        print(s.recv(1024))
        s.close()

    @staticmethod
    def file_transfer_server(filename, port):
        s = socket.socket()  # Create a socket object
        host = socket.gethostname()  # Get local machine name
        s.bind((host, port))  # Bind to the port
        f = open(filename, 'wb')
        s.listen(30)  # Now wait for client connection.
        while True:
            c, addr = s.accept()  # Establish connection with client.
            print('Got connection from'.format(addr))
            print("Receiving...")
            line = c.recv(1024)
            while line:
                print("Receiving...")
                f.write(line)
                line = c.recv(1024)
            f.close()
            print("Done Receiving")
            c.close()  # Close the connection

    async def transfer_ping(self):
        time.sleep(5)

    def thread_tranfer_server(self):
        try:
            self.transfer_loop.run_until_complete(self.transfer_task)
        except asyncio.CancelledError:
            pass

    def __init__(self):
        self.transfer_task = asyncio.Task(self.transfer_ping())
        self.transfer_loop = asyncio.get_event_loop()


if __name__ == '__main__':
    app = UFileTransfer()
    _thread.start_new_thread(app.thread_tranfer_server, ())

    file_transfer_server(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', 'security-hight.png'), )
    while True:
        pass
