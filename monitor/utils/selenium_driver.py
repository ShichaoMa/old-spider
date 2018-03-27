import socket
import http.client

from selenium.webdriver.firefox.remote_connection import FirefoxRemoteConnection
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.service import Service


class CustomDriver(WebDriver):

    def __init__(self, executable_path, log_path, capabilities):
        self.log_path = log_path
        self.service = Service(executable_path, log_path=log_path)
        self.service.start()
        executor = FirefoxRemoteConnection(remote_server_addr=self.service.service_url)
        super(CustomDriver, self).__init__(command_executor=executor, desired_capabilities=capabilities, keep_alive=True)

    def start_session(self, capabilities, profile=None):

        response = self.execute(Command.NEW_SESSION, capabilities)
        if 'sessionId' not in response:
            response = response['value']
        self.session_id = response['sessionId']
        self.capabilities = response.get('value')

        if self.capabilities is None:
            self.capabilities = response.get('capabilities')

        self.w3c = response.get('status') is None

    def quit(self):
        """Quits the driver and close every associated window."""
        try:
            super(CustomDriver, self).quit()
        except (http.client.BadStatusLine, socket.error):
            # Happens if Firefox shutsdown before we've read the response from
            # the socket.
            pass
        self.service.stop()