"""Constants for the NGrok integration."""

from datetime import timedelta

""" This is needed, it impact on the name to be called in configurations.yaml """
""" Ref: https://developers.home-assistant.io/docs/en/creating_integration_manifest.html"""
DOMAIN = 'ngrok'
OBJECT_ID_PUBLIC_URL = 'public_url'

""" NGRok authentication token """
CONF_NGROK_AUTH_TOKEN = 'auth_token'
CONF_NGROK_DOMAIN = 'domain'
CONF_NGROK_INSTALL_DIR = 'install_dir'
CONF_NGROK_OS_VERSION = 'os_version'

""" NGrok authentication token """
CONF_HA_LOCAL_PROTOCOL = 'protocol'
CONF_HA_LOCAL_IP_ADDRESS = 'ip_address'
CONF_HA_LOCAL_PORT = 'port'

""" Optional parameters """
DEFAULT_SCAN_INTERVAL = timedelta(seconds=5)
DEFAULT_NGROK_INSTALL_DIR = 'custom_components/ngrok/.ngrock'
DEFAULT_NGROK_OS_VERSION = 'Linux (ARM)'
DEFAULT_HA_LOCAL_PROTOCOL = 'http'