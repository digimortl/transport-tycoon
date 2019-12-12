from asyncio.locks import Event as Waiter
from typing import List, NamedTuple as Object, Optional

from transport_tycoon.common.simulator import Simulator, SimulationObject


__all__ = ('Cargo', 'LocationCode', 'Warehouse')


LocationCode = str


class Cargo(Object):
    trackNumber: str
    originCode: LocationCode
    destinationCode: LocationCode


class Warehouse(SimulationObject):
    locationCode: LocationCode

    def __init__(self, sim: Simulator, locationCode: LocationCode):
        super().__init__(sim)
        self.locationCode = locationCode
        self.__queue: List[Cargo] = []
        self.__waiters: List[Waiter] = []

    async def waitForACargo(self):
        if self.isEmpty():
            self._sim.suspendProcess()

            waiter = Waiter()
            self.__waiters.append(waiter)
            await waiter.wait()

    def pickCargo(self) -> Optional[Cargo]:
        if self.isEmpty():
            return None

        return self.__queue.pop(0)

    def bring(self, aCargo: Cargo):
        self.__queue.append(aCargo)

        if self.__waiters:
            waiter = self.__waiters.pop(0)
            waiter.set()
            self._sim.resumeProcess()

    def isEmpty(self) -> bool:
        return not self.__queue

    def fullness(self) -> int:
        return len(self.__queue)

    def __repr__(self):
        return f'{type(self).__name__}({self.locationCode})'
