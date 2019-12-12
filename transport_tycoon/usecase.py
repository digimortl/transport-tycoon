from asyncio import ensure_future, run
from itertools import chain, filterfalse
from functools import partial
from logging import getLogger
from logging.config import dictConfig
from typing import Sequence

from transport_tycoon import config
from transport_tycoon.dom import Cargo, LocationCode, TransportMap, Truck, Vessel, Warehouse
from transport_tycoon.common.simulator import Event, Simulator
from transport_tycoon.common.util import hours, Time


LOG = getLogger(__name__)


def inputLocationCodes() -> Sequence[LocationCode]:
    import sys
    return list(filter(bool,
                       map(str.upper,
                           map(str.strip,
                               chain(*sys.argv[1:])))))


def checkIfLocationCodesValid(knownLocationCodes: Sequence[LocationCode], locationCodes: Sequence[LocationCode]):
    unknownLocatinCodes = list(filterfalse(knownLocationCodes.__contains__,
                                           locationCodes))
    if unknownLocatinCodes:
        raise ValueError(f'Unknown location codes: {",".join(unknownLocatinCodes)}')


def forEach(func, iterable):
    for it in iterable:
        func(it)


async def useCase(*destinationCodes: LocationCode) -> Sequence[Event]:
    startAt = Time.today().replace(hour=0, minute=0, second=0, microsecond=0)
    simulator = Simulator(startAt, ensure_future)

    factory = Warehouse(simulator, 'Factory')
    port = Warehouse(simulator, 'Port')
    warehouseA = Warehouse(simulator, 'A')
    warehouseB = Warehouse(simulator, 'B')

    checkIfLocationCodesValid([warehouseA.locationCode,
                               warehouseB.locationCode], destinationCodes)

    def cargoFromFactoryTo(pair) -> Cargo:
        return Cargo(str(pair[0]), factory.locationCode, pair[1])

    cargoesToDeliver = list(map(cargoFromFactoryTo, enumerate(destinationCodes)))

    forEach(factory.bring, cargoesToDeliver)
    transportMap = \
        TransportMap() \
            .byLand(factory, port, hours(1)) \
                .bySea(port, warehouseA, hours(6)) \
            .byLand(factory, warehouseB, hours(5))

    await Truck(simulator, 'Truck 1', transportMap) \
        .startJourneyFrom(factory)
    await Truck(simulator, 'Truck 2', transportMap) \
        .startJourneyFrom(factory)
    await Vessel(simulator, 'Vessel 1', transportMap) \
        .startJourneyFrom(port)

    def tillCargoesHaveBeenDelivered() -> bool:
        return len(cargoesToDeliver) == warehouseA.fullness() + warehouseB.fullness()

    LOG.debug('Start simulation at %s', startAt.time())

    occurredEvents = await simulator.proceed(tillCargoesHaveBeenDelivered)

    LOG.debug('Stop simulation at %s', simulator.currentTime.time())
    return occurredEvents


if __name__ == '__main__':
    import sys
    from transport_tycoon.event_adapter import printEvents

    dictConfig(config.LOGGING_CONFIG)

    occurredEvents: Sequence[Event] = \
        run(useCase(*inputLocationCodes()), debug=True)
    printEvents(occurredEvents)
