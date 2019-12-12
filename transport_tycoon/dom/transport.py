from logging import getLogger
from typing import Optional, overload

from transport_tycoon.common.simulator import Event, Simulator, SimulationObject
from transport_tycoon.common.util import Time
from transport_tycoon.dom.navigator import Itinerary, ShipmentOption, Navigator
from transport_tycoon.dom.warehouse import Cargo, LocationCode, Warehouse


LOG = getLogger(__name__)


class TransportArrived(Event):
    source: object
    atWarehouse: Warehouse
    cargo: Optional[Cargo] = None
    occurredAt: Time = None


class TransportDeparted(Event):
    source: object
    fromWarehouse: Warehouse
    toWarehouse: Warehouse
    cargo: Cargo
    occurredAt: Time = None


class Transport(SimulationObject):

    def __init__(self, sim: Simulator, name: str, nav: Navigator, shipmentOption: ShipmentOption):
        super().__init__(sim)
        self.__name = name
        self.__cargo: Optional[Cargo] = None
        self.__assignedItinerary: Optional[Itinerary] = None
        self.__nav = nav
        self.__shipmentOption = shipmentOption

    @property
    def name(self) -> str:
        return self.__name

    def load(self, aCargo: Cargo):
        self.__cargo = aCargo

    def unloadACargo(self) -> Cargo:
        cargo, self.__cargo = self.__cargo, None
        return cargo

    def assignItinerary(self, from_: LocationCode, to: LocationCode):
        itinerary = self.__nav.findItinerary(from_, to)
        self.__assignedItinerary = itinerary.forShipBy(self.__shipmentOption)
        LOG.debug('%r assigned itinerary %r', self, self.__assignedItinerary)

    def reAssignItineraryToComeBack(self):
        self.__assignedItinerary = self.__assignedItinerary.forComeBack()
        LOG.debug('%r (re)assigned itinerary %r', self, self.__assignedItinerary)

    def hasNotCargo(self) -> bool:
        return self.__cargo is None

    async def startJourneyFrom(self, warehouse: Warehouse):
        await self._sim.schedule(TransportArrived(self, atWarehouse=warehouse))

    async def depart(self):
        transportDeparted = TransportDeparted(self,
                                              fromWarehouse=self.__assignedItinerary.origin,
                                              toWarehouse=self.__assignedItinerary.destination,
                                              cargo=self.__cargo)
        await self._sim.schedule(transportDeparted)

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

    async def whenArrived(self, arrived: TransportArrived):
        if self.hasNotCargo():
            aCargo = await arrived.atWarehouse.pickCargo()
            self.load(aCargo)
            self.assignItinerary(from_=arrived.atWarehouse.locationCode, to=aCargo.destinationCode)
            await self.depart()
        else:
            aCargo = self.unloadACargo()
            arrived.atWarehouse.bring(aCargo)
            await self.comeBack()

    async def whenDeparted(self, departed: TransportDeparted):
        transportArrived = TransportArrived(self,
                                            atWarehouse=self.__assignedItinerary.destination,
                                            cargo=self.__cargo)
        await self._sim.schedule(transportArrived, after=self.__assignedItinerary.totalTimeToTravel)

    def __repr__(self):
        return f'{type(self).__name__}({self.__name})'


class Truck(Transport):
    def __init__(self, sim: Simulator, name: str, nav: Navigator):
        super().__init__(sim, name, nav, ShipmentOption.land)


class Vessel(Transport):
    def __init__(self, sim: Simulator, name: str, nav: Navigator):
        super().__init__(sim, name, nav, ShipmentOption.sea)
