#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import socket

pi_sugar_tcp_port = 8423

class PiSugar:
    """
    PiSugar interface
    
    `https://github.com/PiSugar/PiSugar/wiki/PiSugar-Power-Manager-(Software)`
    """

    def __init__(self):
        self.logger = logging.getLogger("maginkcal")

    def get_battery(self) -> float:
        """
        Connects to the server to get the battery status using a socket.
        """

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("127.0.0.1", pi_sugar_tcp_port))            
                sock.sendall(b'get battery')            
                raw_data = sock.recv(1024)
                
            data_str = raw_data.decode('utf-8')        
            battery_level = float(data_str.split(":")[1].strip())
            print(type(battery_level))

        except (ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse battery level: {e}")
            return 0.0
        
        return battery_level

    def sync_time(self) -> None:
        """
        Synchronise with PiSugar time
        """
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("127.0.0.1", pi_sugar_tcp_port))
                sock.sendall(b"rtc_rtc2pi")
                sock.recv(1024)
        except socket.error as e:
            self.logger.info(f"Socket error: {e}")
      
if __name__ == "__main__":
    print(PiSugar().get_battery())
