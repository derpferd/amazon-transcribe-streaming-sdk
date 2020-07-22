from io import BufferedIOBase
from typing import Optional


class BufferableByteStream(BufferedIOBase):
    def __init__(self):
        self._byte_chunks: list = []
        self.__done: bool = False
        self.__closed: bool = False

    def read(self, size=-1) -> Optional[bytes]:  # type: ignore
        if len(self._byte_chunks) < 1 and not self.__done:
            # This behavior is a quirk of CRT where we have
            # an open stream but no data to be read.
            return None
        elif (self.__done and not self._byte_chunks) or self.closed:
            return b""

        temp_bytes = self._byte_chunks.pop(0)
        remaining_bytes = b""
        if size == -1:
            return temp_bytes
        elif size > 0:
            remaining_bytes = temp_bytes[size:]
            temp_bytes = temp_bytes[:size]
        else:
            remaining_bytes = temp_bytes
            temp_bytes = b""

        if len(remaining_bytes) > 0:
            self._byte_chunks.insert(0, remaining_bytes)
        return temp_bytes

    def read1(self, size=-1) -> Optional[bytes]:  # type: ignore
        return self.read(size)

    def readinto(self, b, read1=False):
        if not isinstance(b, memoryview):
            b = memoryview(b)
            b = b.cast("B")

        if read1:
            data = self.read1(len(b))
        else:
            data = self.read(len(b))

        if data is None:
            return None

        n = len(data)

        b[:n] = data

        return n

    def write(self, b: bytes) -> int:
        if not isinstance(b, bytes):
            type_ = type(b)
            raise ValueError(
                f"Unexpected value written to BufferableByteStream. "
                f"Only bytes are support but {type_} was provided."
            )

        if self.closed or self.__done:
            raise IOError(
                "Stream is completed and doesn't support further writes."
            )

        if b:
            self._byte_chunks.append(b)

        return len(b)

    @property
    def closed(self) -> bool:
        return self.__closed

    def close(self):
        self._buffered_bytes_chunks = None
        self.__done = True
        self.__closed = True

    def end_stream(self):
        self.__done = True
