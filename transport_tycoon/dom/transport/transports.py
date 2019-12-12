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
    timeToLoad: Duration = hours(0)
    timeToUnload: Duration = hours(0)

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

    def unload(self) -> Cargo:
        return self.__cargoes.pop()

    def assignItinerary(self, from_: LocationCode, to: LocationCode):
        itinerary = self.__transportMap.findItinerary(from_, to)
        self.__assignedItinerary = itinerary.forShipBy(self.__shipmentOption)
        LOG.debug('[%r] assigned itinerary %r', self, self.__assignedItinerary)

    def reAssignItineraryToComeBack(self):
        self.__assignedItinerary = self.__assignedItinerary.forComeBack()
        LOG.debug('[%r] (re)assigned itinerary %r', self, self.__assignedItinerary)

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
        await self._sim.schedule(transportDeparted)

    async def comeBack(self):
        self.reAssignItineraryToComeBack()
        await self.depart()

    async def loadCargoesFrom(self, warehouse: Warehouse):
        while not self.isFull():
            aCargo = warehouse.pickCargo()
            if aCargo is not None:
                self.load(aCargo)
            elif self.isEmpty():
                await warehouse.waitForACargo()
            else:
                break

        cargoesLoaded = CargoesLoaded(self,
                                      fromWarehouse=warehouse,
                                      duration=self.timeToLoad,
                                      cargoes=tuple(self.__cargoes))
        await self._sim.schedule(cargoesLoaded, after=self.timeToLoad)

    async def unloadCargoesTo(self, warehouse: Warehouse):
        while not self.isEmpty():
            aCargo = self.unload()
            warehouse.bring(aCargo)

        cargoesUnloaded = CargoesUnloaded(self,
                                          toWarehouse=warehouse,
                                          duration=self.timeToUnload,
                                          cargoes=tuple(self.__cargoes))
        await self._sim.schedule(cargoesUnloaded, after=self.timeToUnload)

    def __repr__(self):
        return f'{type(self).__name__}({self.__name})'

    #
    # Event handlers:
    #
    @overload
    async def when(self, arrived: TransportArrived):
        ...

    @overload
    async def when(self, departed: TransportDeparted):
        ...

    @overload
    async def when(self, loaded: CargoesLoaded):
        ...

    @overload
    async def when(self, unloaded: CargoesUnloaded):
        ...

    async def when(self, event):
        if isinstance(event, TransportArrived):
            await self.whenArrived(event)
        elif isinstance(event, TransportDeparted):
            await self.whenDeparted(event)
        elif isinstance(event, CargoesLoaded):
            await self.whenLoaded(event)
        elif isinstance(event, CargoesUnloaded):
            await self.whenUnloaded(event)
        else:
            raise NotImplementedError

    async def whenArrived(self, arrived: TransportArrived):
        if self.isEmpty():
            await self.loadCargoesFrom(arrived.atWarehouse)
        else:
            await self.unloadCargoesTo(arrived.atWarehouse)

    async def whenDeparted(self, departed: TransportDeparted):
        transportArrived = TransportArrived(self,
                                            atWarehouse=departed.toWarehouse,
                                            cargoes=tuple(self.__cargoes))
        await self._sim.schedule(transportArrived, after=departed.timeToDeliver)

    async def whenLoaded(self, loaded: CargoesLoaded):
        self.assignItinerary(from_=loaded.fromWarehouse.locationCode,
                             to=loaded.cargoes[0].destinationCode)
        await self.depart()

    async def whenUnloaded(self, unloaded: CargoesUnloaded):
        await self.comeBack()


class Truck(Transport):
    def __init__(self, sim: Simulator, name: str, transportMap: TransportMap):
        super().__init__(sim, name, transportMap, ShipmentOption.land)


class Vessel(Transport):
    capacity: int = 4
    timeToLoad: Duration = hours(1)
    timeToUnload: Duration = hours(1)

    def __init__(self, sim: Simulator, name: str, transportMap: TransportMap):
        super().__init__(sim, name, transportMap, ShipmentOption.sea)
