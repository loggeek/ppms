from threading import Thread, Condition
from socket import socket, AF_INET, SHUT_RDWR, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from configparser import ConfigParser


MESSAGE = ""

def main():
    # Read config
    cfg = ConfigParser()
    cfg.read("config.ini", encoding='utf-8')

    # Parse config
    recv_ip = cfg["recv"]["ip"]
    recv_port = int(cfg["recv"]["port"])
    alert_ip = cfg["alert"]["ip"]
    alert_port = int(cfg["alert"]["port"])
    alert_allowed = [item.strip() for item in cfg["alert"]["allowed"].split(";")]

    # Init alert server
    alert_server = socket(AF_INET, SOCK_STREAM)
    alert_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    alert_server.bind((alert_ip, alert_port))

    # Init receiver server
    recv_server = socket(AF_INET, SOCK_STREAM)
    recv_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    recv_server.bind((recv_ip, recv_port))
    
    # Init alert condition
    condition = Condition()

    # Run alert server
    alert_thread = Thread(target=alert_run, args=(alert_server, alert_allowed, condition))
    alert_thread.start()

    # Run receiver server
    recv_thread = Thread(target=recv_run, args=(recv_server, condition))
    recv_thread.start()

    # Finish
    alert_thread.join()
    recv_thread.join()


def alert_run(server, allowed, condition):
    threads = []
    try:
        while True:
            # Wait for connections
            print("AS> Waiting for connections")
            server.listen(4)
            (conn, (ip, port)) = server.accept()
            
            # Authenticate user
            if ip in allowed:
                print("AS> Connection accepted to:", ip)
                thread = AlertServerThread(conn, ip, port, condition)
                thread.start()
                threads.append(thread)
            else:
                print("AS> Connection denied to:", ip)
                conn.shutdown(SHUT_RDWR)
                conn.close()
    finally:
        # Finish
        for thread in threads:
            thread.join()


class AlertServerThread(Thread):
    def __init__(self, conn, ip, port, condition):
        Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.condition = condition
    
    def run(self):
        global MESSAGE
        try:
            # Get message
            MESSAGE = self.conn.recv(1024)
            print("AT> Received alert message:", MESSAGE)
            
            # Send acknowledgment
            self.conn.send(b"OK")
            
            # Notifying to receiver server
            with self.condition:
                self.condition.notify_all()
            
        except Exception as e:
            print(str(e))
            
        finally:
            # Finish
            print("AT> Socket disconnected:", self.ip)
            self.conn.close()


def recv_run(server, condition):
    threads = []
    try:
        while True:
            # Wait for connections
            print("RS> Waiting for connections")
            server.listen(4)
            (conn, (ip, port)) = server.accept()
            
            # Connect
            print("RS> Connection accepted to:", ip)
            thread = RecvServerThread(conn, ip, port, condition)
            thread.start()
            threads.append(thread)
    finally:
        # Finish
        for thread in threads:
            thread.join()


class RecvServerThread(Thread):
    def __init__(self, conn, ip, port, condition):
        Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.condition = condition
    
    def run(self):
        global MESSAGE
        try:
            # Get message (we don't care about its contents)
            self.conn.recv(1024)
            print("RT> Received initial message")
            
            while True:
                with self.condition:
                    self.condition.wait()
                    print("RT> Sending alert message:", MESSAGE)
                    self.conn.send(MESSAGE)
            
        except Exception as e:
            print(str(e))
            
        finally:
            # Finish
            print("RT> Socket disconnected:", self.ip)
            self.conn.close()


if __name__ == "__main__":
    main()
