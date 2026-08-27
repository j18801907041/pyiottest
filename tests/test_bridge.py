import socket
import threading

from dtu_bridge.bridge import DtuTcpServer, is_valid_imei


def test_validates_imei_format_and_check_digit():
    assert is_valid_imei("490154203237518")
    assert not is_valid_imei("490154203237519")
    assert not is_valid_imei("49015420323751")
    assert not is_valid_imei(b"49015420323751\xff")


def test_server_receives_and_sends_bytes():
    received = []
    ready = threading.Event()

    def on_data(data, connection):
        received.append(data)
        return b"response\xff"

    server = DtuTcpServer("127.0.0.1", 0, on_data=on_data)

    def serve():
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind((server.host, server.port))
        server.port = listener.getsockname()[1]
        listener.close()
        ready.set()
        server.serve_forever()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    ready.wait(1)
    client = socket.create_connection(("127.0.0.1", server.port))
    client.sendall(b"request\x00")
    assert client.recv(64) == b"response\xff"
    client.close()
    server.stop()
    thread.join(2)
    assert received == [b"request\x00"]
