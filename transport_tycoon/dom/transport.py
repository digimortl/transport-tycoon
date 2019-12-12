from logging import getLogger
from typing import List, Optional, overload, Sequence

from transport_tycoon.common.simulator import Event, Simulator, SimulationObject
from transport_tycoon.common.util import Duration, hours, Time
from transport_tycoon.dom.navigator import Itinerary, ShipmentOption, Navigator
from transport_tycoon.dom.warehouse import Cargo, LocationCode, Warehouse


LOG = getLogger(__name__)


class TransportArrived(Event):
    source: object
    atWarehouse: Warehouse
    cargoes: Sequence[Cargo] = ()
    occurredAt: Time = None


class TransportDeparted(Event):
    source: object
    fromWarehouse: Warehouse
    toWarehouse: Warehouse
    cargoes: Sequence[Cargo]
    occurredAt: Time = None


class Transport(SimulationObject):

    def __init__(self,
                 sim: Simulator,
                 name: str,
                 nav: Navigator,
                 shipmentOption: ShipmentOption,
                 maxCargoes: int = 1,
                 departAfter: Duration = Duration()
                 ):
        super().__init__(sim)
        self.__name = name
        self.__cargoes: List[Cargo] = []
        self.__assignedItinerary: Optional[Itinerary] = None
        self.__nav = nav
        self.__shipmentOption = shipmentOption
        self.__maxCargoes = maxCargoes
        self.__departAfter = departAfter

    @property
    def name(self) -> str:
        return self.__name

    def load(self, aCargo: Cargo):
        self.__cargoes.append(aCargo)

    def unloadACargo(self) -> Cargo:
        return self.__cargoes.pop()

    def assignItinerary(self, from_: LocationCode, to: LocationCode):
        itinerary = self.__nav.findItinerary(from_, to)
        self.__assignedItinerary = itinerary.forShipBy(self.__shipmentOption)
        LOG.debug('%r assigned itinerary %r', self, self.__assignedItinerary)

    def reAssignItineraryToComeBack(self):
        self.__assignedItinerary = self.__assignedItinerary.forComeBack()
        LOG.debug('%r (re)assigned itinerary %r', self, self.__assignedItinerary)

    def isEmpty(self) -> bool:
        return not self.__cargoes

    def isFull(self) -> bool:
        return len(self.__cargoes) == self.__maxCargoes

    async def startJourneyFrom(self, warehouse: Warehouse):
        await self._sim.schedule(TransportArrived(self, atWarehouse=warehouse))

    async def depart(self):
        transportDeparted = TransportDeparted(self,
                                              fromWarehouse=self.__assignedItinerary.origin,
                                              toWarehouse=self.__assignedItinerary.destination,
                                              cargoes=tuple(self.__cargoes))
        await self._sim.schedule(transportDeparted, after=self.__departAfter)

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
        while True:
            aCargo = warehouse.pickCargo()
            if aCargo:
                self.load(aCargo)

                if self.isFull():
                    break
            else:
                if not self.isEmpty():
                    break

                await warehouse.waitForACargo()

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
                                            atWarehouse=self.__assignedItinerary.destination,
                                            cargoes=tuple(self.__cargoes))
        await self._sim.schedule(transportArrived, after=self.__assignedItinerary.totalTimeToTravel)

    def __repr__(self):
        return f'{type(self).__name__}({self.__name})'


class Truck(Transport):
    def __init__(self, sim: Simulator, name: str, nav: Navigator):
        super().__init__(sim, name, nav, ShipmentOption.land)


class Vessel(Transport):
    def __init__(self, sim: Simulator, name: str, nav: Navigator):
        super().__init__(sim, name, nav, ShipmentOption.sea, maxCargoes=6, departAfter=hours(1))
