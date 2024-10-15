#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script exposes the functions to interface with PiSugar. Mainly to retrieve the current battery level and also
to trigger the syncing of the PiSugar
"""

import subprocess
import logging
import socket

pi_sugar_tcp_port = 8423

class PiSugar:
    """
    Interface with PiSugar
    """

    def __init__(self):
        self.logger = logging.getLogger("maginkcal")

    def get_battery(self) -> float:
        # start displaying on eink display
        # command = ['echo "get battery" | nc -q 0 127.0.0.1 8423']
        battery_float = float(-1)
        try:
            # ps = subprocess.Popen(('echo', 'get battery'), stdout=subprocess.PIPE)
            # result = subprocess.check_output(('nc', '-q', '0', '127.0.0.1', '8423'), stdin=ps.stdout)
            # ps.wait()
            # result_str = result.decode('utf-8').rstrip()
            # battery_level = result_str.split()[-1]
            battery_float = float(0.3)
            # battery_level = "{:.3f}".format(battery_float)
        except (ValueError, subprocess.CalledProcessError) as e:
            self.logger.info("Invalid battery output")
        return battery_float

    def sync_time(self) -> None:
        """
        Synchronise with PiSugar time
        """
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("127.0.0.1", pi_sugar_tcp_port))
                sock.sendall(b"rtc_rtc2pi")
                sock.recv(1024)  # Buffer size of 1024 bytes
        except socket.error as e:
            self.logger.info(f"Socket error: {e}")
