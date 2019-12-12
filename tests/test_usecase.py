from asyncio import run
from typing import Coroutine, Sequence
from unittest import TestCase

from transport_tycoon.common.simulator import Event
from transport_tycoon.common.util import Duration, hours
from transport_tycoon.usecase import useCase


class UseCaseTest(TestCase):

    def _run(self, useCaseCoro: Coroutine) -> Duration:
        occurredEvents: Sequence[Event] = run(useCaseCoro)
        return occurredEvents[-1].occurredAt - occurredEvents[0].occurredAt

    def testThatDeliveryToATakes5Hours(self):
        timeToDeliver = self._run(useCase('A'))
        self.assertEqual(timeToDeliver, hours(5))

    def testThatDeliveryToABTakes5Hours(self):
        timeToDeliver = self._run(useCase('A', 'B'))
        self.assertEqual(timeToDeliver, hours(5))

    def testThatDeliveryToBBTakes5Hours(self):
        timeToDeliver = self._run(useCase('B', 'B'))
        self.assertEqual(timeToDeliver, hours(5))

    def testThatDeliveryToABBTakes7Hours(self):
        timeToDeliver = self._run(useCase('A','B', 'B'))
        self.assertEqual(timeToDeliver, hours(7))

    def testThatDeliveryToAABABBABTakes29Hours(self):
        timeToDeliver = self._run(useCase('A', 'A', 'B', 'A', 'B', 'B', 'A', 'B'))
        self.assertEqual(timeToDeliver, hours(29))
