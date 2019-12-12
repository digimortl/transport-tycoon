from asyncio import sleep
from asyncio.queues import PriorityQueue
from logging import getLogger
from typing import Callable, Coroutine, NamedTuple as Event

from transport_tycoon.common.util import Duration, Time


LOG = getLogger(__name__)


class Simulator:
    currentTime: Time

    Pred = Callable[[], bool]
    SpawnProcess = Callable[[Coroutine], None]

    def __init__(self, startAt: Time, spawn: SpawnProcess):
        self.__processesReadyToGo = 0
        self.__spawn = spawn
        self.__eventsQueue = PriorityQueue()
        self.currentTime = startAt
        self.__eventSeq = 0

    def nextEventSeq(self) -> int:
        self.__eventSeq += 1
        return self.__eventSeq

    async def schedule(self, anEvent: Event, after: Duration = Duration()):
        willOccurrAt = self.currentTime + after
        LOG.debug('%r will occur at %s', anEvent, willOccurrAt.time())
        await self.__eventsQueue.put((willOccurrAt, self.nextEventSeq(), anEvent))

    def suspendProcess(self):
        self.__processesReadyToGo -= 1

    def resumeProcess(self):
        self.__processesReadyToGo += 1

    def readyToContinue(self) -> bool:
        return self.__processesReadyToGo == 0

    def newProcessFor(self, coro: Coroutine):

        async def fork():
            await coro
            self.suspendProcess()

        self.resumeProcess()
        return self.__spawn(fork())

    async def proceed(self, till: Pred):

        async def switch():
            await sleep(0)

        while True:

            while not self.readyToContinue():
                await switch()

            if self.__eventsQueue.empty() or till():
                break

            currentTime, _, anEvent = await self.__eventsQueue.get()
            self.currentTime = currentTime
            LOG.info('At %s an event %r occurred', self.currentTime.time(), anEvent)

            self.newProcessFor(anEvent.source.when(anEvent))


class SimulationObject:
    sim: Simulator

    def __init__(self, sim: Simulator):
        self._sim = sim
