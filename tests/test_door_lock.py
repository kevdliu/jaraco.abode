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
import tests.mock.devices.door_lock as DOOR_LOCK
import pytest


USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestDoorLock(unittest.TestCase):
    """Test the generic AbodePy device class."""

    def setUp(self):
        """Set up Abode module."""
        self.abode = jaraco.abode.Abode(
            username=USERNAME, password=PASSWORD, disable_cache=True
        )

    def tearDown(self):
        """Clean up after test."""
        self.abode = None

    @requests_mock.mock()
    def tests_lock_device_properties(self, m):
        """Tests that lock devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=DOOR_LOCK.device(
                devid=DOOR_LOCK.DEVICE_ID,
                status=CONST.STATUS_LOCKCLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our lock
        device = self.abode.get_device(DOOR_LOCK.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == CONST.STATUS_LOCKCLOSED
        assert not device.battery_low
        assert not device.no_response
        assert device.is_locked

        # Set up our direct device get url
        device_url = str.replace(CONST.DEVICE_URL, '$DEVID$', DOOR_LOCK.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            text=DOOR_LOCK.device(
                devid=DOOR_LOCK.DEVICE_ID,
                status=CONST.STATUS_LOCKOPEN,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == CONST.STATUS_LOCKOPEN
        assert device.battery_low
        assert device.no_response
        assert not device.is_locked

    @requests_mock.mock()
    def tests_lock_device_mode_changes(self, m):
        """Tests that lock device changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=DOOR_LOCK.device(
                devid=DOOR_LOCK.DEVICE_ID,
                status=CONST.STATUS_LOCKCLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(DOOR_LOCK.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_LOCKCLOSED
        assert device.is_locked

        # Set up control url response
        control_url = CONST.BASE_URL + DOOR_LOCK.CONTROL_URL
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=DOOR_LOCK.DEVICE_ID, status=CONST.STATUS_LOCKOPEN_INT
            ),
        )

        # Change the mode to "on"
        assert device.unlock()
        assert device.status == CONST.STATUS_LOCKOPEN
        assert not device.is_locked

        # Change response
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=DOOR_LOCK.DEVICE_ID, status=CONST.STATUS_LOCKCLOSED_INT
            ),
        )

        # Change the mode to "off"
        assert device.lock()
        assert device.status == CONST.STATUS_LOCKCLOSED
        assert device.is_locked

        # Test that an invalid status response throws exception
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=DOOR_LOCK.DEVICE_ID, status=CONST.STATUS_LOCKCLOSED_INT
            ),
        )

        with pytest.raises(jaraco.abode.AbodeException):
            device.unlock()
