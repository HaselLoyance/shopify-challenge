from app.query import get_n_random_images_with_hue_and_margin
from app.business import save_images
from asgiref.sync import sync_to_async
import websockets
import asyncio
import threading
import json
import base64
import os

# How many images to sent when the connection is first established
ON_CONNECTION_SEND_N_IMAGES = 20

# Margin for two hue values to be considered close (equal)
HUE_MARGIN = 2

# The loop for the server is going to run in another thread. This is safe for the development environment
# in the context of the technical question, but of course for the real deal this should not be allowed. The
# incoming websocket connections would have to be handled by something like Apache or nginx with separate
# load balancers and all that jazz.


def decode_payload(payload: str) -> dict:
    return json.loads(payload)


def encode_payload(payload: dict) -> str:
    return json.dumps(payload)


async def send_starting_images(websocket) -> None:
    images = await sync_to_async(get_n_random_images_with_hue_and_margin)(ON_CONNECTION_SEND_N_IMAGES, 0, HUE_MARGIN)

    payload = {
        'type': 'more_images',
        'images': [],
    }

    for image in (await sync_to_async(list)(images)):
        payload['images'].append(image.to_dict())

    await websocket.send(encode_payload(payload))


async def new_images_handler(images: list) -> None:
    await sync_to_async(save_images)(images)


async def more_images_handler(websocket, hue: int) -> None:
    images = await sync_to_async(get_n_random_images_with_hue_and_margin)(10, hue, HUE_MARGIN)

    payload = {
        'type': 'more_images',
        'images': [],
    }

    for image in (await sync_to_async(list)(images)):
        payload['images'].append(image.to_dict())

    await websocket.send(encode_payload(payload))


async def message_handler(websocket, payload) -> None:
    message = decode_payload(payload)

    if message['type'] == 'more_images':
        await more_images_handler(websocket, int(message['hue']))
    elif message['type'] == 'new_images':
        await new_images_handler(message['images'])

async def connection_handler(websocket, path: str) -> None:
    try:
        # Once connected, we should send out some images
        await send_starting_images(websocket)

        # Then we just wait for more image requests
        async for message in websocket:
            await message_handler(websocket, message)
    except Exception as e:
        pass


def websocket_loop(event_loop, server) -> None:
    event_loop.run_until_complete(server)
    event_loop.run_forever()


def start_websocket_loop() -> None:
    event_loop = asyncio.new_event_loop()
    server = websockets.serve(connection_handler, 'localhost', 8001, loop=event_loop, max_size= 2 ** 24)

    thread = threading.Thread(target=websocket_loop, args=(event_loop, server,), daemon=True)
    thread.start()


start_server = start_websocket_loop
