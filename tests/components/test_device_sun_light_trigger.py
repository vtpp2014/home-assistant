"""The tests device sun light trigger component."""
# pylint: disable=protected-access
from datetime import datetime
import os
import unittest
from unittest.mock import patch

from homeassistant.setup import setup_component
import homeassistant.loader as loader
from homeassistant.const import CONF_PLATFORM, STATE_HOME, STATE_NOT_HOME
from homeassistant.components import (
    device_tracker, light, device_sun_light_trigger)
from homeassistant.util import dt as dt_util

from tests.common import (
    get_test_config_dir, get_test_home_assistant, fire_time_changed)


KNOWN_DEV_YAML_PATH = os.path.join(get_test_config_dir(),
                                   device_tracker.YAML_DEVICES)


# pylint: disable=invalid-name
def setUpModule():
    """Write a device tracker known devices file to be used."""
    device_tracker.update_config(
        KNOWN_DEV_YAML_PATH, 'device_1', device_tracker.Device(
            None, None, True, 'device_1', 'DEV1',
            picture='http://example.com/dev1.jpg'))

    device_tracker.update_config(
        KNOWN_DEV_YAML_PATH, 'device_2', device_tracker.Device(
            None, None, True, 'device_2', 'DEV2',
            picture='http://example.com/dev2.jpg'))


# pylint: disable=invalid-name
def tearDownModule():
    """Remove device tracker known devices file."""
    os.remove(KNOWN_DEV_YAML_PATH)


class TestDeviceSunLightTrigger(unittest.TestCase):
    """Test the device sun light trigger module."""

    def setUp(self):  # pylint: disable=invalid-name
        """Setup things to be run when tests are started."""
        self.hass = get_test_home_assistant()

        self.scanner = loader.get_component(
            'device_tracker.test').get_scanner(None, None)

        self.scanner.reset()
        self.scanner.come_home('DEV1')

        loader.get_component('light.test').init()

        self.assertTrue(setup_component(self.hass, device_tracker.DOMAIN, {
            device_tracker.DOMAIN: {CONF_PLATFORM: 'test'}
        }))

        self.assertTrue(setup_component(self.hass, light.DOMAIN, {
            light.DOMAIN: {CONF_PLATFORM: 'test'}
        }))

    def tearDown(self):  # pylint: disable=invalid-name
        """Stop everything that was started."""
        self.hass.stop()

    def test_lights_on_when_sun_sets(self):
        """Test lights go on when there is someone home and the sun sets."""
        test_time = datetime(2017, 4, 5, 1, 2, 3, tzinfo=dt_util.UTC)
        with patch('homeassistant.util.dt.utcnow', return_value=test_time):
            self.assertTrue(setup_component(
                self.hass, device_sun_light_trigger.DOMAIN, {
                    device_sun_light_trigger.DOMAIN: {}}))

        light.turn_off(self.hass)

        self.hass.block_till_done()

        test_time = test_time.replace(hour=3)
        with patch('homeassistant.util.dt.utcnow', return_value=test_time):
            fire_time_changed(self.hass, test_time)
            self.hass.block_till_done()

        self.assertTrue(light.is_on(self.hass))

    def test_lights_turn_off_when_everyone_leaves(self): \
            # pylint: disable=invalid-name
        """Test lights turn off when everyone leaves the house."""
        light.turn_on(self.hass)

        self.hass.block_till_done()

        self.assertTrue(setup_component(
            self.hass, device_sun_light_trigger.DOMAIN, {
                device_sun_light_trigger.DOMAIN: {}}))

        self.hass.states.set(device_tracker.ENTITY_ID_ALL_DEVICES,
                             STATE_NOT_HOME)

        self.hass.block_till_done()

        self.assertFalse(light.is_on(self.hass))

    def test_lights_turn_on_when_coming_home_after_sun_set(self): \
            # pylint: disable=invalid-name
        """Test lights turn on when coming home after sun set."""
        test_time = datetime(2017, 4, 5, 3, 2, 3, tzinfo=dt_util.UTC)
        with patch('homeassistant.util.dt.utcnow', return_value=test_time):
            light.turn_off(self.hass)
            self.hass.block_till_done()

            self.assertTrue(setup_component(
                self.hass, device_sun_light_trigger.DOMAIN, {
                    device_sun_light_trigger.DOMAIN: {}}))

            self.hass.states.set(
                device_tracker.ENTITY_ID_FORMAT.format('device_2'), STATE_HOME)

            self.hass.block_till_done()
        self.assertTrue(light.is_on(self.hass))
