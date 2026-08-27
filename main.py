from __future__ import annotations

import argparse
import logging
import socket

from dtu_bridge.bridge import DtuTcpServer, is_valid_imei


def create_data_handler():
    registered_connections = set()

    def handle_data(data: bytes, connection: socket.socket) -> bytes | None:
        if connection not in registered_connections:
            if not is_valid_imei(data):
                logging.warning("rejected DTU registration: %s", data.hex(" "))
                connection.close()
                return None
            registered_connections.add(connection)
            logging.info("DTU registered, IMEI=%s", data.decode("ascii"))
            return None

        logging.info("DTU data: %s", data.hex(" "))
        return None

    return handle_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="4G DTU TCP transparent server")
    parser.add_argument("--tcp-host", default="0.0.0.0", help="Listen address")
    parser.add_argument("--tcp-port", type=int, required=True)
    parser.add_argument("--read-size", type=int, default=4096)
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")
    server = DtuTcpServer(args.tcp_host, args.tcp_port, args.read_size, create_data_handler())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.stop()
        logging.info("stopping DTU server")


if __name__ == "__main__":
    main()