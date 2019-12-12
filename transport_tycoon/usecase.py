from asyncio import ensure_future, run
from itertools import chain, filterfalse
from functools import partial
from logging import getLogger
from logging.config import dictConfig
from typing import Sequence

from transport_tycoon import config
from transport_tycoon.dom import Cargo, LocationCode, Navigator, Transport, Warehouse
from transport_tycoon.common.simulator import Simulator
from transport_tycoon.common.util import Duration, hours, Time


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


async def useCase(*destinationCodes: LocationCode) -> Duration:
    A, B = 'A', 'B'

    checkIfLocationCodesValid([A, B], destinationCodes)

    cargoFromFactoryTo = partial(Cargo, 'Factory')

    cargosToDeliver = list(map(cargoFromFactoryTo, destinationCodes))

    startAt = Time.today().replace(hour=0, minute=0, second=0, microsecond=0)
    LOG.debug('Start simulation at %s', startAt.time())

    simulator = Simulator(startAt, ensure_future)

    factory = Warehouse(simulator, 'Factory')
    forEach(factory.bring, cargosToDeliver)
    port = Warehouse(simulator, 'Port')
    warehouseA = Warehouse(simulator, A)
    warehouseB = Warehouse(simulator, B)

    navigator = \
        Navigator() \
            .link(factory, port, hours(1)) \
            .link(port, warehouseA, hours(4)) \
            .link(factory, warehouseB, hours(5))

    await Transport(simulator, 'Truck 1', navigator) \
        .arriveAt(factory)
    await Transport(simulator, 'Truck 2', navigator) \
        .arriveAt(factory)
    await Transport(simulator, 'Vessel', navigator) \
        .arriveAt(port)

    def tillCargosHaveBeenDelivered() -> bool:
        return len(cargosToDeliver) == warehouseA.fullness() + warehouseB.fullness()

    await simulator.proceed(tillCargosHaveBeenDelivered)

    LOG.debug('Stop simulation at %s', simulator.currentTime.time())
    return simulator.currentTime - startAt


if __name__ == '__main__':
    import sys

    dictConfig(config.LOGGING_CONFIG)

    timeToDeliver: Duration = \
        run(useCase(*inputLocationCodes()))

    print(timeToDeliver.total_seconds() / 3600.0, file=sys.stdout)
