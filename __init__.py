import logging
import voluptuous as vol
from os.path import dirname, basename
import urllib.request
import zipfile
import os
import subprocess
import stat
import threading
import json

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from .const import *


""" NGRok for Hassio: https://community.home-assistant.io/t/ngrok-and-hass-io/33953/2 """


""" Setting log """
_LOGGER = logging.getLogger('ngrok_init')
_LOGGER.setLevel(logging.DEBUG)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_NGROK_AUTH_TOKEN): cv.string,
        vol.Required(CONF_HA_LOCAL_IP_ADDRESS): cv.string,
        vol.Required(CONF_HA_LOCAL_PORT): cv.port,
        vol.Required(CONF_HA_LOCAL_PROTOCOL, default=DEFAULT_HA_LOCAL_PROTOCOL): cv.string,
        vol.Required(CONF_NGROK_OS_VERSION, default=DEFAULT_NGROK_OS_VERSION): cv.string,

        vol.Optional(CONF_NGROK_INSTALL_DIR, default=DEFAULT_NGROK_INSTALL_DIR): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

NGROK_EXECUTABLE_URL_MAP = {
    'Linux (64-Bit)': {'url': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip', 'ext': '', 'prefix': './'},
    'Linux (ARM64)': {'url': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.zip', 'ext': '', 'prefix': './'},
    'Linux (ARM)': {'url': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.zip', 'ext': '', 'prefix': './'},
    'Linux (32-Bit)': {'url': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-386.tgz', 'ext': '', 'prefix': './'},
}

def run_subprocess(command_line):
    return subprocess.run(command_line, capture_output=True)

async def async_setup(hass, config):
    # Deja esta función vacía ya que la configuración se manejará a través de la interfaz de usuario
    return True

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry):
    _LOGGER.debug('async_setup_entry()')

    """Get Meross Component configuration"""
    ngrok_auth_token = entry.data[CONF_NGROK_AUTH_TOKEN]
    ngrok_domain = entry.data[CONF_NGROK_DOMAIN]
    ngrok_install_dir = entry.data[CONF_NGROK_INSTALL_DIR]
    ha_local_ip_address = entry.data[CONF_HA_LOCAL_IP_ADDRESS]
    ha_local_port = entry.data[CONF_HA_LOCAL_PORT]
    ha_local_protocol = entry.data[CONF_HA_LOCAL_PROTOCOL]
    ngrok_os_version = entry.data[CONF_NGROK_OS_VERSION]

    hass.data[DOMAIN] = {
        'thread': None,
        'public_url': None,
    }

    def thread_run_ngrok(command_line):
        try:
            _LOGGER.debug('Executing: ' + str(command_line))
            output_bytes = subprocess.run(command_line, capture_output=True)
            output_str = output_bytes.stdout.decode()
            _LOGGER.debug(output_str)
        except subprocess.CalledProcessError as CPE:
            _LOGGER.error('ERROR: ' + str(CPE))
        pass

    """ Check if NGRok is installed """
    async def async_ngrok_installation():

        if ngrok_os_version not in NGROK_EXECUTABLE_URL_MAP:
            _LOGGER.error('ngrok os version ' + ngrok_os_version + ' is not supported')
            return

        # get the prefix for the executable file
        prefix = NGROK_EXECUTABLE_URL_MAP[ngrok_os_version]['prefix']

        # get the executable ngrok file extension (e.g. ".exe" in windows, "" in linux)
        ext = NGROK_EXECUTABLE_URL_MAP[ngrok_os_version]['ext']

        # get the current ngrok custom-component folder
        ngrok_custom_component_dir = os.path.dirname(os.path.realpath(__file__))

        # get up of 2 folders >>> up to homeassistant config directory
        homeassitant_dir = dirname(dirname(ngrok_custom_component_dir))

        if not os.path.isdir(homeassitant_dir):
            _LOGGER.error(homeassitant_dir + ' dir does not exist')
            return

        _LOGGER.debug(homeassitant_dir + ' dir exists')

        # ngrok installation dir
        ngrok_dir = os.path.join(homeassitant_dir, ngrok_install_dir)

        if not os.path.isdir(ngrok_dir):
            # ngrok dir does not exists >>> create it!
            _LOGGER.debug(ngrok_dir + ' dir does not exist')
            try:
                # trying to create ngrok dir
                os.mkdir(ngrok_dir)
            except OSError:
                _LOGGER.error("Creation of the ngrok directory %s failed" % ngrok_dir)
                return

            # ngrok dir created!
            _LOGGER.debug(ngrok_dir + ' dir created')

        # Create path to ngrok execution file
        ngrok_file = os.path.join(ngrok_dir, 'ngrok')
        ngrok_file_ext = ngrok_file + ext

        if not os.path.isfile(ngrok_file_ext):
            # ngrok execution file does not exist >>> try to get it
            _LOGGER.debug(ngrok_file + ext + ' file not found >>> downloading it...')

            # get url to download ngrok zip file on the basis of OS version
            url = NGROK_EXECUTABLE_URL_MAP[ngrok_os_version]['url']

            # get zip filename and related file
            ngrok_zip_filename = basename(url)
            ngrok_zip_file = os.path.join(ngrok_dir, ngrok_zip_filename)

            # downloading ngrok zip filename
            _LOGGER.debug('Downloading ngrok zip file...')
            await hass.async_add_executor_job(urllib.request.urlretrieve, url, ngrok_zip_file)

            # check if download succeeded
            if not os.path.isfile(ngrok_zip_file):
                _LOGGER.error('ngrok zip file download failed')
                return

            # ngork download succeessfully
            _LOGGER.debug('ngrok zip file downloaded')
            # unzip ngork downloaded zip file...
            zip_ref = zipfile.ZipFile(ngrok_zip_file, 'r')
            _LOGGER.debug('Extracting ngrok zip file...')
            await hass.async_add_executor_job(zip_ref.extractall, ngrok_dir)
            await hass.async_add_executor_job(zip_ref.close)

        if not os.path.isfile(ngrok_file_ext):
            _LOGGER.error('ngrok execution file not found: '+ngrok_file_ext)
            return

        # ngrok execution file exists!
        _LOGGER.debug(ngrok_file_ext + ' file found.')
        _LOGGER.debug('Changing working directory to: ' + ngrok_dir)
        # make ngrok file executable
        if not os.access(ngrok_file + ext, os.X_OK):
            await hass.async_add_executor_job(os.chmod, ngrok_file_ext, stat.S_IEXEC)
        # changing working directory to ngrok directory
        await hass.async_add_executor_job(os.chdir, ngrok_dir)
        current_dir = await hass.async_add_executor_job(os.getcwd)
        _LOGGER.debug('working directory is: ' + current_dir)
        # create command line to generate authentication token
        ngrok_exec = prefix + 'ngrok' + ext
        try:
            command_line = [
                ngrok_exec, 
                'http',
                '--authtoken=' + ngrok_auth_token,
                '--domain=' + ngrok_domain,
                ha_local_ip_address + ':' + str(ha_local_port)
            ]
            # create thread and starts it
            hass.data[DOMAIN]['thread'] = threading.Thread(target=thread_run_ngrok, args=[command_line])
            hass.data[DOMAIN]['thread'].start()
        except (subprocess.CalledProcessError, PermissionError) as E:
            _LOGGER.error('Permission error')
            _LOGGER.debug(str(E))
            _LOGGER.debug(oct(stat.S_IMODE(os.lstat(ngrok_file + ext).st_mode)))
            _LOGGER.debug(oct(stat.S_IMODE(os.stat(ngrok_file + ext).st_mode)))
            _LOGGER.debug(os.access(ngrok_file + ext, os.X_OK))
            return

    await async_ngrok_installation()

    """ Called at the very beginning and periodically, each 5 seconds """
    async def async_update_ngrok_status():
        _LOGGER.debug('async_update_devices_status()')
        
        if hass.data[DOMAIN]['thread'] is None or not hass.data[DOMAIN]['thread'].is_alive():
            hass.async_create_task(async_ngrok_installation())
        pass

    await async_update_ngrok_status()

    """ Called at the very beginning and periodically, each 5 seconds """
    async def async_periodic_update_ngrok_status(event_time):
        _LOGGER.debug('async_periodic_update_ngrok_status()')
        hass.async_create_task(async_update_ngrok_status())
        pass

    """ This is used to update the Meross Devices status periodically """
    async_track_time_interval(hass, async_periodic_update_ngrok_status, timedelta(seconds=5))

    return True
