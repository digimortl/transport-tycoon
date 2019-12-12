from typing import Dict, Sequence, Tuple

from transport_tycoon.dom.warehouse import LocationCode, Warehouse
from transport_tycoon.common.util import Duration


Link = Tuple[Warehouse, Warehouse, Duration]
Itinerary = Sequence[Link]


class Navigator:

    def __init__(self):
        self.__graph: Dict[LocationCode, Dict[LocationCode, Link]] = {}

    def link(self, loc1: Warehouse, loc2: Warehouse, timeToTravel: Duration) -> 'Navigator':
        self.__graph.setdefault(loc1.locationCode, {})[loc2.locationCode] = (loc1, loc2, timeToTravel)
        self.__graph.setdefault(loc2.locationCode, {})[loc1.locationCode] = (loc2, loc1, timeToTravel)
        return self

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
            return ()

        return find(originCode)

    def findNextLocation(self, originCode: LocationCode, destinationCode: LocationCode) -> Tuple[Warehouse, Duration]:

        def isEmpty(it: Itinerary) -> bool:
            return not it

        def firstSegment(it: Itinerary) -> Link:
            return it[0]

        itinerary = self.findItinerary(originCode, destinationCode)
        if isEmpty(itinerary):
            raise ValueError(f'Itinerary from {originCode} to {destinationCode} not found')

        _, dest, timeToTravel = firstSegment(itinerary)
        return dest, timeToTravel
