from json import dumps
from sys import stdout
from typing import Sequence

from transport_tycoon.common.simulator import Event
from transport_tycoon.common.util import Duration, Time
from transport_tycoon.dom.transport import *


def eventToDict(event: Event, startAt: Time):

    def inHours(dur: Duration) -> float:
        return dur.total_seconds() / 3600.0

    def relTime() -> Duration:
        return event.occurredAt - startAt

    rv = {
        'time': inHours(relTime()),
        'transport_id': event.source.name,
        'kind': event.source.__class__.__name__.upper(),
        'cargo': [{
            'cargo_id': cargo.trackNumber,
            'origin': cargo.originCode,
            'destination': cargo.destinationCode,
        } for cargo in event.cargoes]
    }
    if isinstance(event, TransportArrived):
        rv.update({
            'event': 'ARRIVE',
            'location': event.atWarehouse.locationCode,
        })
    elif isinstance(event, TransportDeparted):
        rv.update({
            'event': 'DEPART',
            'location': event.fromWarehouse.locationCode,
            'destination': event.toWarehouse.locationCode,
        })
    elif isinstance(event, CargoesLoaded):
        rv.update({
            'time': inHours(relTime() - event.duration),
            'event': 'LOAD',
            'duration': inHours(event.duration),
        })
    elif isinstance(event, CargoesUnloaded):
        rv.update({
            'time': inHours(relTime() - event.duration),
            'event': 'UNLOAD',
            'duration': inHours(event.duration),
        })
    else:
        raise NotImplementedError

    return rv


def printEvents(events: Sequence[Event]):
    if not events:
        return

    startAt = events[0].occurredAt
    for event in events:
        print(dumps(eventToDict(event, startAt)), file=stdout)