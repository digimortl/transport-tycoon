from typing import Sequence

from transport_tycoon.common.simulator import Event
from transport_tycoon.common.util import Duration, Time
from transport_tycoon.dom.warehouse import Cargo, Warehouse


__all__ = ('TransportArrived', 'TransportDeparted', 'CargoesLoaded', 'CargoesUnloaded')


class TransportArrived(Event):
    source: object
    atWarehouse: Warehouse
    cargoes: Sequence[Cargo] = ()
    occurredAt: Time = None


class TransportDeparted(Event):
    source: object
    fromWarehouse: Warehouse
    toWarehouse: Warehouse
    timeToDeliver: Duration
    cargoes: Sequence[Cargo]
    occurredAt: Time = None


class CargoesLoaded(Event):
    source: object
    fromWarehouse: Warehouse
    duration: Duration
    cargoes: Sequence[Cargo]
    occurredAt: Time = None


class CargoesUnloaded(Event):
    source: object
    toWarehouse: Warehouse
    duration: Duration
    cargoes: Sequence[Cargo]
    occurredAt: Time = None
