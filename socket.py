"""Socket communications for ekey home rs485"""
import asyncio
import errno
import re
import socket
import time
from urllib.parse import urlparse

from .const import CONF_MAPPING, EKEY_USER_ID, EKEY_HA_USER
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.helpers.network import get_url
import logging

from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)


async def connection(hass, config):
    """
    Connect to the socket in background and parse
    """
    parsed_url = urlparse(get_url(hass))
    ha_ip_address = parsed_url.hostname
    ekey_ip_address = config.get(CONF_IP_ADDRESS)
    port = config.get(CONF_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind((ha_ip_address, port))
    except OSError as e:
        _LOGGER.error("Could not connect to socket: " + e.strerror + ". The combination  of IP " + str(ha_ip_address) + " and port " + str(port) + " failed maybe due to another integration is already using this connection.")
        return

    sock.setblocking(False)
    sock.connect((ekey_ip_address, port))
    _LOGGER.info("Ping ekey home converter KNX RS-485 on ip address " + ekey_ip_address + ", port " + str(port))
    sock.send("G'Day\n".encode('utf-8'))

    while True:
        await asyncio.sleep(0.2)
        try:
            data, addr = sock.recvfrom(1024)
        except ConnectionRefusedError:
            _LOGGER.error("Could not connect to ekey home rs485 on " + ekey_ip_address)
            time.sleep(10)
            sock.close()
            await connection(hass, config)
        except socket.error as e:
            if e.errno == errno.EAGAIN:
                pass
            else:
                raise
        else:
            received = data.decode('utf-8').replace('\n', '')

            if is_valid(received):
                chunks = received.split('_')
                entity_name = get_entity_name(int(chunks[1]), config.get(CONF_MAPPING))
                set_state(hass, entity_name, chunks)
            else:
                _LOGGER.error("Invalid packet received: " + received)

            pass


def set_state(hass, entity_name, chunks):
    finger_name = get_finger_name(chunks[2])
    hass.states.async_set(entity_name, finger_name)


def get_finger_name(number):
    hand = {
        "1": "little-finger-left",
        "2": "ring-finger-left",
        "3": "middle-finger-left",
        "4": "index-finger-left",
        "5": "thumb-left",
        "6": "thumb-right",
        "7": "index-finger-right",
        "8": "middle-finger-right",
        "9": "ring-finger-right",
        "0": "little-finger-right",
        "-": "unknown-finger",
        "R": "rfid",
    }

    return hand.get(number, "unknown")


def get_entity_name(ekey_id: int, mapping):
    entity_name = None

    for ekey in mapping:
        if ekey[EKEY_USER_ID] == ekey_id:
            ekey_id = int(ekey[EKEY_USER_ID])
            username = str(ekey[EKEY_HA_USER])
            entity_name = slugify(username + " - ekey_id:" + str(ekey_id))

    return "sensor." + entity_name


def is_valid(packet):
    """
    Validate incoming packet

    Expected string:
    1       _ 0046    _ 4         _ 80156809150025 _ 1      _ 2
    ^         ^         ^           ^                ^        ^
    PAKETTYP  USER ID   FINGER ID   SERIENNR FS      AKTION   RELAIS

    ################################################################

    PAKETTYP always '1'

    USER ID must be in range 0000-9999 (default 0000)

    FINGER ID must be in range '0'-'9', '-' or 'R'
    '1' = little finger left
    '2' = ring-finger left
    '3' = middle-finger left
    '4' = index-finger left
    '5' = thumb left
    '6' = thumb right
    '7' = index-finger right
    '8' = middle-finger right
    '9' = ring-finger right
    '0' = little finger right
    '-' = No/unknown finger
    'R' = RFID

    SERIENNR FS must be 14 digits

    AKTION must be 1 or 2
    1 = open
    2 = bounce/refuse, unknown finger

    RELAIS must be in range '1'-'4', '-' or 'd'
    1 - 4 = relay
    d = double relay
    "-" = no relay
    """

    return re.match("^[1]_\d{4}_[0-9R-]_\d{14}_[1-2]_[1-4d-]$", packet)
