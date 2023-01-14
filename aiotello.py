from typing import Iterator
import asyncio
import functools
import logging
import dataclasses

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TelloStatus:
    mid: int
    x: int
    y: int
    z: int
    pitch: float
    roll: float
    yaw: float
    vgx: int
    vgy: int
    vgz: int
    templ: float
    temph: float
    tof: float
    h: int
    bat: float
    baro: float
    time: float
    agx: float
    agy: float
    agz: float


class TelloProtocol:

    def __init__(self, *args, **kwargs) -> None:
        self.q = asyncio.Queue()

    def connection_made(self, transport):
        print(f'Connected from {transport}')
        self.transport = transport

    def connection_lost(self, transport):
        print(f'Lost connection from {transport}')
        self.transport = None

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        self.q.put_nowait(message)


class Tello:

    def __init__(self) -> None:
        self._command_transport: asyncio.Transport = None
        self._command_protocol: TelloProtocol = None
        
        self._status_transport: asyncio.Transport = None
        self._status_protocol: TelloProtocol = None

        self._status_task: asyncio.Task = None


    async def __aenter__(self) -> 'Tello':
        loop = asyncio.get_running_loop()
        self._command_transport, self._command_protocol = await loop.create_datagram_endpoint(
            TelloProtocol,
            local_addr=('0.0.0.0', 8889),
            remote_addr=('192.168.10.1', '8889')
        )
        connected = await self.send_command(b'command')
        if not connected:
            raise Exception('Cannot connect to Tello')

        # self._status_transport, self._status_protocol = await loop.create_datagram_endpoint(
        #     TelloProtocol,
        #     local_addr=('0.0.0.0', 8890),
        #     remote_addr=('192.168.10.1', '8889')
        # )

        return self

    async def send_command(self, command: bytearray) -> bool:
        self._command_transport.sendto(command)
        response = await self._command_protocol.q.get()
        return response == 'ok'

    async def __aexit__(self, *args, **kwargs):
        self._command_transport.close()
        # self._status_transport.close()



async def main():
    async with Tello() as tello:
        await tello.send_command(b'takeoff')
        await tello.send_command(b'up 150')

        await tello.send_command(b'flip f')
        await tello.send_command(b'flip r')

        # await tello.send_command(b'go 200 0 200 100')
        # await tello.send_command(b'go -200 0 -200 100')
        await tello.send_command(b'land')

if __name__ == '__main__':
    asyncio.run(main())