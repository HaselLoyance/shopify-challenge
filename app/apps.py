from django.apps import AppConfig
import os


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        # At cold start Django executes ready method twice, so we use some internal Django environment
        #   variables to only run it once
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        # Starts the websocket server ONCE!
        from app.websocket_server import start_server
        start_server()
