"""Reconnect remains bounded, cancellable and diagnostic on busy machines."""

import unittest
from unittest.mock import patch

from _path import installPackagePath

installPackagePath()
from globalPlugins.whatsappWebPlusCompanion import cdp
from globalPlugins.whatsappWebPlusCompanion.models import LoaderError


class FakeClockEvent:
	def __init__(self):
		self.now = 0.0
		self.cancelled = False

	def is_set(self):
		return self.cancelled

	def wait(self, seconds):
		self.now += seconds
		return self.cancelled


class BusyReconnectTests(unittest.TestCase):
	def test_successful_discovery_after_deadline_reports_timeout_without_connecting(self):
		clock = FakeClockEvent()

		def discover():
			clock.now = 2
			return (41,)

		with (
			patch.object(cdp.time, "monotonic", side_effect=lambda: clock.now),
			self.assertRaises(LoaderError) as raised,
		):
			cdp.reconnect(discover, lambda target: self.fail("deadline must still apply"), clock, deadline=2)
		self.assertEqual(raised.exception.code, "cdp.reconnect")
		self.assertEqual(raised.exception.safeDetail, "operation.timeout: stage=reconnect.discovery")

	def test_cancellation_wins_when_failed_probe_exhausts_deadline(self):
		clock = FakeClockEvent()

		def discover():
			clock.now = 2
			clock.cancelled = True
			raise LoaderError("powershell.failed", "timeout;stage=package.processes")

		with (
			patch.object(cdp.time, "monotonic", side_effect=lambda: clock.now),
			self.assertRaises(LoaderError) as raised,
		):
			cdp.reconnect(discover, lambda target: target, clock, deadline=2)
		self.assertEqual(raised.exception.code, "operation.cancelled")

	def test_already_cancelled_expired_operation_does_not_probe(self):
		clock = FakeClockEvent()
		clock.cancelled = True
		with (
			patch.object(cdp.time, "monotonic", side_effect=lambda: clock.now),
			self.assertRaises(LoaderError) as raised,
		):
			cdp.reconnect(lambda: self.fail("must not probe"), lambda target: target, clock, deadline=0)
		self.assertEqual(raised.exception.code, "operation.cancelled")

	def test_fourth_attempt_can_recover_after_slow_probes(self):
		clock = FakeClockEvent()
		attempts = []

		def discover():
			attempts.append(clock.now)
			clock.now += 8
			if len(attempts) < 4:
				raise LoaderError("powershell.failed", "timeout;stage=listener.identity")
			return "target"

		with patch.object(cdp.time, "monotonic", side_effect=lambda: clock.now):
			self.assertEqual(cdp.reconnect(discover, lambda target: target, clock), "target")
		self.assertEqual(len(attempts), 4)
		self.assertGreater(clock.now, 20)

	def test_caller_deadline_and_underlying_safe_detail_are_preserved(self):
		clock = FakeClockEvent()
		failure = LoaderError("powershell.failed", "timeout;stage=listener.identity;budget=1.00s")
		with (
			patch.object(cdp.time, "monotonic", side_effect=lambda: clock.now),
			self.assertRaises(LoaderError) as raised,
		):
			cdp.reconnect(lambda: (_ for _ in ()).throw(failure), lambda target: target, clock, deadline=2)
		self.assertEqual(clock.now, 2)
		self.assertEqual(raised.exception.code, "cdp.reconnect")
		self.assertEqual(raised.exception.safeDetail, "powershell.failed: " + failure.safeDetail)

	def test_cancellation_during_wait_stops_retries(self):
		clock = FakeClockEvent()

		def discover():
			clock.cancelled = True
			raise LoaderError("target.missing")

		with (
			patch.object(cdp.time, "monotonic", side_effect=lambda: clock.now),
			self.assertRaises(LoaderError) as raised,
		):
			cdp.reconnect(discover, lambda target: target, clock)
		self.assertEqual(raised.exception.code, "operation.cancelled")
