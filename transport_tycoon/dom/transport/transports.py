from logging import getLogger
from typing import List, Optional, overload

from transport_tycoon.common.simulator import Simulator, SimulationObject
from transport_tycoon.common.util import Duration, hours
from transport_tycoon.dom.map import Itinerary, ShipmentOption, TransportMap
from transport_tycoon.dom.warehouse import Cargo, LocationCode, Warehouse
from .events import *


__all__ = ('Transport', 'Truck', 'Vessel')


LOG = getLogger(__name__)


class Transport(SimulationObject):
    capacity: int = 1
    departAfter: Duration = hours(0)

    def __init__(self,
                 sim: Simulator,
                 name: str,
                 transportMap: TransportMap,
                 shipmentOption: ShipmentOption
                 ):
        super().__init__(sim)
        self.__name = name
        self.__cargoes: List[Cargo] = []
        self.__assignedItinerary: Optional[Itinerary] = None
        self.__transportMap = transportMap
        self.__shipmentOption = shipmentOption

    @property
    def name(self) -> str:
        return self.__name

    def load(self, aCargo: Cargo):
        self.__cargoes.append(aCargo)

    def unloadACargo(self) -> Cargo:
        return self.__cargoes.pop()

    def assignItinerary(self, from_: LocationCode, to: LocationCode):
        itinerary = self.__transportMap.findItinerary(from_, to)
        self.__assignedItinerary = itinerary.forShipBy(self.__shipmentOption)
        LOG.debug('%r assigned itinerary %r', self, self.__assignedItinerary)

    def reAssignItineraryToComeBack(self):
        self.__assignedItinerary = self.__assignedItinerary.forComeBack()
        LOG.debug('%r (re)assigned itinerary %r', self, self.__assignedItinerary)

    def isEmpty(self) -> bool:
        return not self.__cargoes

    def isFull(self) -> bool:
        return len(self.__cargoes) == self.capacity

    async def startJourneyFrom(self, warehouse: Warehouse):
        await self._sim.schedule(TransportArrived(self, atWarehouse=warehouse))

    async def depart(self):
        transportDeparted = TransportDeparted(self,
                                              fromWarehouse=self.__assignedItinerary.origin,
                                              toWarehouse=self.__assignedItinerary.destination,
                                              timeToDeliver=self.__assignedItinerary.totalTimeToTravel,
                                              cargoes=tuple(self.__cargoes))
        await self._sim.schedule(transportDeparted, after=self.departAfter)

    async def comeBack(self):
        self.reAssignItineraryToComeBack()
        await self.depart()

    @overload
    async def when(self, arrived: TransportArrived):
        ...

    @overload
    async def when(self, departed: TransportDeparted):
        ...

    async def when(self, event):
        if isinstance(event, TransportArrived):
            await self.whenArrived(event)
        elif isinstance(event, TransportDeparted):
            await self.whenDeparted(event)
        else:
            raise NotImplementedError

    async def loadCargoesFrom(self, warehouse: Warehouse):
        while not self.isFull():
            aCargo = warehouse.pickCargo()
            if aCargo is not None:
                self.load(aCargo)
            elif self.isEmpty():
                await warehouse.waitForACargo()
            else:
                break

    def unloadCargoesTo(self, warehouse: Warehouse):
        while not self.isEmpty():
            aCargo = self.unloadACargo()
            warehouse.bring(aCargo)

    async def whenArrived(self, arrived: TransportArrived):
        warehouse = arrived.atWarehouse

        if self.isEmpty():
            await self.loadCargoesFrom(warehouse)

            self.assignItinerary(from_=warehouse.locationCode,
                                 to=self.__cargoes[0].destinationCode)
            await self.depart()
        else:
            self.unloadCargoesTo(warehouse)
            await self.comeBack()

    async def whenDeparted(self, departed: TransportDeparted):
        transportArrived = TransportArrived(self,
                                            atWarehouse=departed.toWarehouse,
                                            cargoes=tuple(self.__cargoes))
        await self._sim.schedule(transportArrived, after=departed.timeToDeliver)

    def __repr__(self):
        return f'{type(self).__name__}({self.__name})'


class Truck(Transport):
    def __init__(self, sim: Simulator, name: str, transportMap: TransportMap):
        super().__init__(sim, name, transportMap, ShipmentOption.land)


class Vessel(Transport):
    capacity: int = 4
    departAfter: Duration = hours(1)

    def __init__(self, sim: Simulator, name: str, transportMap: TransportMap):
        super().__init__(sim, name, transportMap, ShipmentOption.sea)
