from json import dumps
from sys import stdout
from typing import Sequence

from transport_tycoon.common.simulator import Event
from transport_tycoon.common.util import Time
from transport_tycoon.dom.transport import TransportArrived, TransportDeparted


def eventToDict(event: Event, startAt: Time):
    rv = {
        'time': (event.occurredAt - startAt).total_seconds() / 3600,
        'transport_id': event.source.name,
        'kind': event.source.__class__.__name__.upper(),
    }
    if event.cargoes:
        rv.update({
            'cargo': [{
                'cargo_id': cargo.trackNumber,
                'origin': cargo.originCode,
                'destination': cargo.destinationCode,
            } for cargo in event.cargoes]
        })
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
    else:
        raise NotImplementedError

    return rv


def printEvents(events: Sequence[Event]):
    if not events:
        return

    startAt = events[0].occurredAt
    for event in events:
        print(dumps(eventToDict(event, startAt)), file=stdout)