from asyncio.locks import Event as Waiter
from typing import List, NamedTuple as Object

from transport_tycoon.common.simulator import Simulator, SimulationObject


LocationCode = str


class Cargo(Object):
    originCode: LocationCode
    destinationCode: LocationCode


class Warehouse(SimulationObject):
    locationCode: LocationCode

    def __init__(self, sim: Simulator, locationCode: LocationCode):
        super().__init__(sim)
        self.locationCode = locationCode
        self.__queue: List[Cargo] = []
        self.__waiters: List[Waiter] = []

    def __pickNoWait(self) -> Cargo:
        return self.__queue.pop(0)

    async def pickCargo(self) -> Cargo:
        if self.empty():
            self._sim.suspendProcess()

            waiter = Waiter()
            self.__waiters.append(waiter)
            await waiter.wait()

        return self.__pickNoWait()

    def bring(self, aCargo: Cargo):
        self.__queue.append(aCargo)

        if self.__waiters:
            waiter = self.__waiters.pop(0)
            waiter.set()
            self._sim.resumeProcess()

    def empty(self) -> bool:
        return not self.__queue

    def fullness(self) -> int:
        return len(self.__queue)

    def __repr__(self):
        return f'{type(self).__name__}({self.locationCode})'
