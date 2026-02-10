import socketio


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ):
    return None


@sio.event
async def disconnect(sid):
    return None


@sio.on("join-station")
async def join_station(sid, station):
    if station:
        await sio.enter_room(sid, f"station:{station}")
