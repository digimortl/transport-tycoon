from enum import auto, Enum
from itertools import takewhile
from typing import Dict, NamedTuple, Optional, Sequence

from transport_tycoon.dom.warehouse import LocationCode, Warehouse
from transport_tycoon.common.util import Duration


class ShipmentOption(Enum):
    land = auto()
    sea = auto()


class Leg(NamedTuple):
    origin: Warehouse
    destination: Warehouse
    timeToTravel: Duration
    shipmentOption: ShipmentOption


class Itinerary:
    def __init__(self, *legs: Leg):
        self.__legs = legs

    def forShipBy(self, shipmentType: ShipmentOption) -> 'Itinerary':

        def hasTheShipmemtOption(leg: Leg) -> bool:
            return leg.shipmentOption == shipmentType

        return Itinerary(*takewhile(hasTheShipmemtOption, self.legs))

    def forComeBack(self) -> 'Itinerary':

        def wayBack(leg: Leg) -> Leg:
            return leg._replace(origin=leg.destination, destination =leg.origin)

        return Itinerary(*map(wayBack, self.legs))

    @property
    def legs(self) -> Sequence[Leg]:
        return self.__legs

    @property
    def origin(self) -> Optional[Warehouse]:
        if not self.legs:
            return None

        return self.legs[0].origin

    @property
    def destination(self) -> Optional[Warehouse]:
        if not self.legs:
            return None

        return self.legs[-1].destination

    @property
    def totalTimeToTravel(self) -> Duration:

        def timeToTravel(leg: Leg) -> Duration:
            return leg.timeToTravel

        return sum(map(timeToTravel, self.legs), Duration())

    def __repr__(self):
        return f'{self.__class__.__name__}({",".join(map(repr, self.legs))})'


class Navigator:

    def __init__(self):
        self.__graph: Dict[LocationCode, Dict[LocationCode, Leg]] = {}

    def link(self, loc1: Warehouse, loc2: Warehouse, timeToTravel: Duration, transportType: ShipmentOption) -> 'Navigator':
        self.__graph.setdefault(loc1.locationCode, {})[loc2.locationCode] = Leg(loc1, loc2, timeToTravel, transportType)
        self.__graph.setdefault(loc2.locationCode, {})[loc1.locationCode] = Leg(loc2, loc1, timeToTravel, transportType)
        return self

    def byLand(self, from_: Warehouse, to: Warehouse, timeToTravel: Duration) -> 'Navigator':
        return self.link(from_, to, timeToTravel, ShipmentOption.land)

    def bySea(self, from_: Warehouse, to: Warehouse, timeToTravel: Duration):
        return self.link(from_, to, timeToTravel, ShipmentOption.sea)

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
