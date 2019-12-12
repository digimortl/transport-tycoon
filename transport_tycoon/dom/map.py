from enum import auto, Enum
from itertools import takewhile
from typing import Dict, NamedTuple, Optional, Sequence

from transport_tycoon.dom.warehouse import LocationCode, Warehouse
from transport_tycoon.common.util import Duration


__all__ = ('Itinerary', 'Segment', 'ShipmentOption', 'TransportMap')


class ShipmentOption(Enum):
    land = auto()
    sea = auto()


class Segment(NamedTuple):
    origin: Warehouse
    destination: Warehouse
    timeToTravel: Duration
    shipmentOption: ShipmentOption


class Itinerary:
    def __init__(self, *segments: Segment):
        self.__segments = segments

    def forShipBy(self, shipmentType: ShipmentOption) -> 'Itinerary':

        def hasTheShipmemtOption(seg: Segment) -> bool:
            return seg.shipmentOption == shipmentType

        return Itinerary(*takewhile(hasTheShipmemtOption, self.segments))

    def forComeBack(self) -> 'Itinerary':

        def wayBack(seg: Segment) -> Segment:
            return seg._replace(origin=seg.destination, destination=seg.origin)

        return Itinerary(*map(wayBack, self.segments))

    @property
    def segments(self) -> Sequence[Segment]:
        return self.__segments

    @property
    def origin(self) -> Optional[Warehouse]:
        if not self.segments:
            return None

        return self.segments[0].origin

    @property
    def destination(self) -> Optional[Warehouse]:
        if not self.segments:
            return None

        return self.segments[-1].destination

    @property
    def totalTimeToTravel(self) -> Duration:

        def timeToTravel(leg: Segment) -> Duration:
            return leg.timeToTravel

        return sum(map(timeToTravel, self.segments), Duration())

    def __repr__(self):
        return f'{self.__class__.__name__}({",".join(map(repr, self.segments))})'


class TransportMap:

    def __init__(self):
        self.__graph: Dict[LocationCode, Dict[LocationCode, Segment]] = {}

    def segment(self, loc1: Warehouse, loc2: Warehouse, timeToTravel: Duration, transportType: ShipmentOption) -> 'TransportMap':
        self.__graph.setdefault(loc1.locationCode, {})[loc2.locationCode] = Segment(loc1, loc2, timeToTravel, transportType)
        self.__graph.setdefault(loc2.locationCode, {})[loc1.locationCode] = Segment(loc2, loc1, timeToTravel, transportType)
        return self

    def byLand(self, from_: Warehouse, to: Warehouse, timeToTravel: Duration) -> 'TransportMap':
        return self.segment(from_, to, timeToTravel, ShipmentOption.land)

    def bySea(self, from_: Warehouse, to: Warehouse, timeToTravel: Duration):
        return self.segment(from_, to, timeToTravel, ShipmentOption.sea)

    def findItinerary(self, originCode: LocationCode, destinationCode: LocationCode) -> Itinerary:

        def find(orig: LocationCode, path: tuple = ()):
            if destinationCode in self.__graph[orig]:
                return path + (self.__graph[orig][destinationCode],)

            itinerary = ()
            for locationCode in self.__graph[orig]:
                itinerary = find(locationCode, path + (self.__graph[orig][locationCode],))
                if itinerary:
                    break

            return itinerary

        if originCode not in self.__graph:
            return Itinerary()

        return Itinerary(*find(originCode))
