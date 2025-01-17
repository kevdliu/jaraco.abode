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
import tests.mock.devices.secure_barrier as COVER


USERNAME = 'foobar'
PASSWORD = 'deadbeef'


class TestSecureBarrier(unittest.TestCase):
    """Test the AbodePy cover class."""

    def setUp(self):
        """Set up Abode module."""
        self.abode = jaraco.abode.Abode(
            username=USERNAME, password=PASSWORD, disable_cache=True
        )

    def tearDown(self):
        """Clean up after test."""
        self.abode = None

    @requests_mock.mock()
    def tests_cover_device_properties(self, m):
        """Tests that cover devices properties work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=COVER.device(
                devid=COVER.DEVICE_ID,
                status=CONST.STATUS_CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(COVER.DEVICE_ID)

        # Test our device
        assert device is not None
        assert device.status == CONST.STATUS_CLOSED
        assert not device.battery_low
        assert not device.no_response
        assert not device.is_on
        assert not device.is_open

        # Set up our direct device get url
        device_url = str.replace(CONST.DEVICE_URL, '$DEVID$', COVER.DEVICE_ID)

        # Change device properties
        m.get(
            device_url,
            text=COVER.device(
                devid=COVER.DEVICE_ID,
                status=CONST.STATUS_OPEN,
                low_battery=True,
                no_response=True,
            ),
        )

        # Refesh device and test changes
        device.refresh()

        assert device.status == CONST.STATUS_OPEN
        assert device.battery_low
        assert device.no_response
        assert device.is_on
        assert device.is_open

    @requests_mock.mock()
    def tests_cover_status_changes(self, m):
        """Tests that cover device changes work as expected."""
        # Set up URL's
        m.post(CONST.LOGIN_URL, text=LOGIN.post_response_ok())
        m.get(CONST.OAUTH_TOKEN_URL, text=OAUTH_CLAIMS.get_response_ok())
        m.post(CONST.LOGOUT_URL, text=LOGOUT.post_response_ok())
        m.get(CONST.PANEL_URL, text=PANEL.get_response_ok(mode=CONST.MODE_STANDBY))
        m.get(
            CONST.DEVICES_URL,
            text=COVER.device(
                devid=COVER.DEVICE_ID,
                status=CONST.STATUS_CLOSED,
                low_battery=False,
                no_response=False,
            ),
        )

        # Logout to reset everything
        self.abode.logout()

        # Get our power switch
        device = self.abode.get_device(COVER.DEVICE_ID)

        # Test that we have our device
        assert device is not None
        assert device.status == CONST.STATUS_CLOSED
        assert not device.is_open

        # Set up control url response
        control_url = CONST.BASE_URL + COVER.CONTROL_URL
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=COVER.DEVICE_ID, status=CONST.STATUS_OPEN_INT
            ),
        )

        # Change the cover to open
        assert device.open_cover()
        assert device.status == CONST.STATUS_OPEN
        assert device.is_open

        # Change response
        m.put(
            control_url,
            text=DEVICES.status_put_response_ok(
                devid=COVER.DEVICE_ID, status=CONST.STATUS_CLOSED_INT
            ),
        )

        # Change the mode to "off"
        assert device.close_cover()
        assert device.status == CONST.STATUS_CLOSED
        assert not device.is_open
