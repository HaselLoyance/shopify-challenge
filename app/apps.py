from django.apps import AppConfig
import os


class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        # At cold start Django executes ready method twice, so we use some internal Django environment
        #   variables to only run it once
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        # The plan:
        #   If the database is empty, then start N workers to get M latest imgur images saved. Then stop all workers.
        #   Start a single worker to poll Imgur for new images and save them when there are new ones available
        #   Continue executing the django app code
        #   Clicking an image will soft delete it from the database
        # Yoooo: give two basic screens: one is to make infinite scroller from your own uploaded pictures,
        #   and the other is a infinite scroller from imgure images

        # Time-permitting:
        #   Re-enable django sessions app and middleware. Use it to sync up 'infinite scrolling' view across all
        #   connected devices
        print('Hooking up workers to download imgur images')
