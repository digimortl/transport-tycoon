from logging import getLogger
from typing import overload

from transport_tycoon.dom import Navigator
from transport_tycoon.common.simulator import Event, Simulator, SimulationObject
from transport_tycoon.dom.warehouse import Cargo, Warehouse


LOG = getLogger(__name__)


class CameToOrigin(Event):
    source: object
    toLocation: Warehouse


class CameToDestination(Event):
    source: object
    fromLocation: Warehouse
    toLocation: Warehouse
    cargo: Cargo


class Transport(SimulationObject):
    name: str

    def __init__(self, sim: Simulator, name: str, nav: Navigator):
        super().__init__(sim)
        self.name = name
        self._nav = nav

    async def arriveAt(self, location: Warehouse):
        await self._sim.schedule(CameToOrigin(self, toLocation=location))

    async def comeBackTo(self, location: Warehouse, fromLocation: Warehouse):
        destination, timeToTravel = self._nav.findNextLocation(fromLocation.locationCode,
                                                               location.locationCode)
        LOG.debug('%r will come back to %s in %s hour(s)', self, destination.locationCode, timeToTravel)

        cameBack = CameToOrigin(self,
                                toLocation=destination)
        await self._sim.schedule(cameBack, after=timeToTravel)

    @overload
    async def when(self, came: CameToOrigin):
        ...

    @overload
    async def when(self, came: CameToDestination):
        ...

    async def when(self, event):
        if isinstance(event, CameToOrigin):
            await self.whenCameToOrigin(event)
        elif isinstance(event, CameToDestination):
            await self.whenCameToDestination(event)
        else:
            raise NotImplementedError

    async def whenCameToOrigin(self, came: CameToOrigin):
        currentLocation = came.toLocation
        LOG.info('%r came to %s', self, currentLocation.locationCode)

        cargo = await currentLocation.pickCargo()
        LOG.info('%r picked up a cargo %r from %s', self, cargo, currentLocation.locationCode)

        destination, timeToTravel = self._nav.findNextLocation(currentLocation.locationCode,
                                                               cargo.destinationCode)
        LOG.debug('%r will deliver a cargo %r to %s in %s hour(s)',
                  self, cargo, destination.locationCode, timeToTravel)
        cameToDest = CameToDestination(self,
                                       fromLocation=currentLocation,
                                       toLocation=destination,
                                       cargo=cargo)
        await self._sim.schedule(cameToDest, after=timeToTravel)

    async def whenCameToDestination(self, came: CameToDestination):
        currentLocation = came.toLocation
        LOG.info('%r came to to %s', self, currentLocation.locationCode)

        currentLocation.bring(came.cargo)
        LOG.info('%r brought the cargo %r to %s', self, came.cargo, currentLocation.locationCode)

        await self.comeBackTo(came.fromLocation, currentLocation)

    def __repr__(self):
        return f'{type(self).__name__}({self.name})'
