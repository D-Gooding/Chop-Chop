import asyncio
import websockets
import json

from backend.src.api.Request import Request
from backend.src.config import UPDATE_STEP_INTERVAL
from backend.src.controller.controller import CONTROLLER_INSTANCE


async def consumer_handler(websocket):
    request = []
    try:
        request = Request(json.loads(await websocket.recv()))
    except:
        await websocket.send("Poorly formatted JSON")

    print(f"<<< {request}")

    match (request.keyword, request.recipe_id):
        # returns basic info for all recipes
        case ("get", 0):
            print(">>> all recipes' info")
            await websocket.send(CONTROLLER_INSTANCE.get_all_recipe_metadata())

        # returns specific info for one recipe
        case ("get", recipe_id):
            print(f">>> recipe {recipe_id} info")
            await websocket.send(CONTROLLER_INSTANCE.get_recipe_metadata(recipe_id))

        # "loads" the recipe to the controller
        case ("start", recipe_id):
            print(f">>> starting recipe {recipe_id}")
            CONTROLLER_INSTANCE.new_recipe(recipe_id)
            await websocket.send("Started")

        # Sets current step (to be implemented later)
        case ("step", recipe_id):
            print(">>> step set")
            await websocket.send(f"set step {request.step}")


async def producer_handler(websocket):
    while True:  # run forever
        if CONTROLLER_INSTANCE.step_changed_flag.state:
            response = {"step": CONTROLLER_INSTANCE.current_recipe.current_step}
            await websocket.send(json.dumps(response))
            CONTROLLER_INSTANCE.step_changed_flag.state = False
        await asyncio.sleep(UPDATE_STEP_INTERVAL)


async def handler(websocket, path):
    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    await asyncio.gather(consumer_task, producer_task)


def start_websocket():
    start_server = websockets.serve(handler, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
