# Copyright 2021 iiPython

# Modules
import json
import socket
from iipython import Hellman

# Plasma Overflow Protection
try:
    import psutil
    def _gen_def_overflow(s) -> int:  # noqa
        return round((psutil.virtual_memory().available / 2) / len(s.clients))

    _ovfl_needsserver = True

except ImportError:
    def _gen_def_overflow(s) -> int:
        return 1048576  # 1mb

    _ovfl_needsserver = False

# Socket class
class Socket(socket.socket):
    def __init__(self) -> None:
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)

        # Initialization
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

class SocketWrapper(object):
    def __init__(self, socket: socket.socket, server = None) -> None:
        self.sock = socket
        self.buffer_size = (2048 * 2)

        self.server = server
        self.hellman = None

    def close(self) -> None:
        return self.sock.close()

    def recv_json(self, limit: int = None, decrypt: bool = True) -> dict:
        data, limit = b"", (limit or (_gen_def_overflow(self.server if (_ovfl_needsserver and self.server) else None)))
        while self.sock:
            try:
                data += self.sock.recv(self.buffer_size)
                if len(data) > limit:
                    size = len(data)
                    del data
                    raise OverflowError(size)

            except OSError:
                # ... close socket & client
                break

            # Load JSON
            try:
                if self.hellman is not None and decrypt:
                    try:
                        data = json.loads(self.hellman.decrypt(data))

                    except ValueError:
                        raise self.SSLError

                else:
                    data = json.loads(data.decode("utf8"))

                break

            except (json.JSONDecodeError, UnicodeDecodeError):
                pass  # Likely will be fine next pass

        if not data:
            return None

        return data

    def send_json(self, data: dict) -> None:
        try:
            if self.hellman is not None:
                return self.sock.sendall(self.hellman.encrypt(json.dumps(data)) + b"\0x55")

            raw = json.dumps(data).encode("utf8") + b"\0x55"
            return self.sock.sendall(raw)

        except Exception:
            raise OSError

    # Exceptions
    class SSLError(Exception):
        pass
