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

    def testThatDeliveryToABBBABAAABBBTakes39Hours(self):
        timeToDeliver = self._run(useCase('A','B','B','B','A','B','A','A','A','B','B','B'))
        self.assertEqual(timeToDeliver, hours(39))
