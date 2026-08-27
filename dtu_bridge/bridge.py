"""TCP server for receiving and sending data through a 4G DTU."""

from __future__ import annotations

import logging
import re
import socket
import threading
from collections.abc import Callable

LOGGER = logging.getLogger(__name__)
DataHandler = Callable[[bytes, socket.socket], bytes | None]
IMEI_PATTERN = re.compile(r"^[0-9]{15}$")


def is_valid_imei(value: bytes | str) -> bool:
    """Validate an ASCII 15-digit IMEI with its Luhn check digit."""
    if isinstance(value, bytes):
        try:
            value = value.decode("ascii")
        except UnicodeDecodeError:
            return False
    if not IMEI_PATTERN.fullmatch(value):
        return False
    checksum = 0
    for index, digit in enumerate(reversed(value)):
        number = int(digit)
        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        checksum += number
    return checksum % 10 == 0


class DtuTcpServer:
    """Accept one DTU connection and provide bidirectional transparent bytes."""

    def __init__(self, host: str, port: int, read_size: int = 4096, on_data: DataHandler | None = None) -> None:
        self.host = host
        self.port = port
        self.read_size = read_size
        self.on_data = on_data
        self._stop_event = threading.Event()
        self._listener: socket.socket | None = None
        self._connection: socket.socket | None = None

    def serve_forever(self) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(1)
        listener.settimeout(1)
        self._listener = listener
        LOGGER.info("listening for 4G DTU on %s:%d", self.host, self.port)
        try:
            while not self._stop_event.is_set():
                try:
                    connection, address = listener.accept()
                except socket.timeout:
                    continue
                self._connection = connection
                LOGGER.info("DTU connected from %s:%d", *address)
                try:
                    self._serve_connection(connection)
                finally:
                    connection.close()
                    self._connection = None
                    LOGGER.info("DTU disconnected: %s:%d", *address)
        finally:
            listener.close()
            self._listener = None

    def stop(self) -> None:
        self._stop_event.set()
        for connection in (self._connection, self._listener):
            if connection:
                connection.close()

    def send(self, data: bytes) -> None:
        """Send raw bytes to the currently connected DTU."""
        if self._connection is None:
            raise RuntimeError("no DTU is connected")
        self._connection.sendall(data)

    def _serve_connection(self, connection: socket.socket) -> None:
        while not self._stop_event.is_set():
            try:
                data = connection.recv(self.read_size)
            except OSError:
                return
            if not data:
                return
            LOGGER.info("received %d bytes: %s", len(data), data.hex(" "))
            if self.on_data:
                response = self.on_data(data, connection)
                if response:
                    connection.sendall(response)
                    LOGGER.info("sent %d bytes: %s", len(response), response.hex(" "))