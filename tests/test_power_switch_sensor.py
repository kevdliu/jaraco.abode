"""Test the Abode device classes."""
import unittest

import requests_mock

import jaraco.abode
import jaraco.abode.helpers.constants as CONST

import tests.mock.login as LOGIN
import tests.mock.oauth_claims as OAUTH_CLAIMS
import tests.mock.logout as LOGOUT
import tests.mock.panel as PANEL
import tests.mock.devices as DEVICES
import tests.mock.devices.power_switch_sensor as POWERSENSOR
import pytest


USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestPowerSwitchSensor(unittest.TestCase):
    """Test the AbodePy power switch sensor."""

    def setUp(self):
        """Set up Abode module."""
        self.abode = jaraco.abode.Abode(
            username=USERNAME, password=PASSWORD, disable_cache=True
        )

    def tearDown(self):
        """Clean up after test."""
        self.abode = None

    @requests_mock.mock()
    def tests_switch_device_properties(self, m):
        """Tests that switch devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(POWERSENSOR.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.battery_low
        assert not device.no_response
        assert not device.is_on

        # Set up our direct device get url
        device_url = str.replace(CONST.DEVICE_URL, '$DEVID$', POWERSENSOR.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            text=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=CONST.STATUS_ON,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == CONST.STATUS_ON
        assert device.battery_low
        assert device.no_response
        assert device.is_on

    @requests_mock.mock()
    def tests_switch_status_changes(self, m):
        """Tests that switch device changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=POWERSENSOR.device(
                devid=POWERSENSOR.DEVICE_ID,
                status=CONST.STATUS_OFF,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(POWERSENSOR.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Set up control url response
        control_url = CONST.BASE_URL + POWERSENSOR.CONTROL_URL
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=CONST.STATUS_ON_INT
            ),
        )

        # Change the mode to "on"
        assert device.switch_on()
        assert device.status == CONST.STATUS_ON
        assert device.is_on

        # Change response
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        # Change the mode to "off"
        assert device.switch_off()
        assert device.status == CONST.STATUS_OFF
        assert not device.is_on

        # Test that an invalid status response throws exception
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=POWERSENSOR.DEVICE_ID, status=CONST.STATUS_OFF_INT
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.switch_on()
