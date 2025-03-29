import os
import uuid
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import uvicorn

app = FastAPI()

class MessageType:
    STATE = "STATE"
    OFFER = "OFFER"
    ANSWER = "ANSWER"
    ICE = "ICE"

class SessionManager:
    """ Manages WebRTC rooms for peer-to-peer video streaming. """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.rooms: Dict[str, Dict[str, WebSocket]] = {}  # {room_id: {peer_id: websocket}}
        return cls._instance

    async def join_room(self, room_id: str, peer_id: str, websocket: WebSocket):
        """ Adds a peer to a specific room. Only allows two peers per room for video streaming. """
        async with self._lock:
            if room_id not in self.rooms:
                self.rooms[room_id] = {}
                print(f"🆕 Room {room_id} created.")
                
            print(f"🔹 [JOIN REQUEST] Peer {peer_id} wants to join Room {room_id}")

            if len(self.rooms[room_id]) >= 2:
                print(f"❌ Room {room_id} is full. Peer {peer_id} rejected.")
                await websocket.send_text("Room is full. Only 2 peers are allowed.")
                await websocket.close()
                return

            self.rooms[room_id][peer_id] = websocket
            print(f"✅ Peer {peer_id} joined Room {room_id}. Current peers: {list(self.rooms[room_id].keys())}")

            # Notify both peers once two peers are in the room
            if len(self.rooms[room_id]) == 2:
                for other_peer_id, other_peer_ws in self.rooms[room_id].items():
                    print(f"🔔 Notifying Peer {other_peer_id} that Room {room_id} is now Ready.")
                    await other_peer_ws.send_text(f"{MessageType.STATE} Ready")


    async def relay_message(self, room_id: str, sender_id: str, message: str):
        """ Sends WebRTC signaling messages (OFFER, ANSWER, ICE) to the other peer in the same room. """
        print(f"📩 [MESSAGE RECEIVED] from Peer {sender_id} in Room {room_id}: {message}")

        if room_id in self.rooms:
            for peer_id, peer_ws in self.rooms[room_id].items():
                if peer_id != sender_id:  # Don't send message to the sender
                    print(f"📤 Relaying message to Peer {peer_id} in Room {room_id}")
                    await peer_ws.send_text(message)

    async def leave_room(self, room_id: str, peer_id: str):
        """ Removes a peer from the room. If empty, deletes the room. """
        async with self._lock:
            if room_id in self.rooms and peer_id in self.rooms[room_id]:
                print(f"🚪 Peer {peer_id} is leaving Room {room_id}")
                del self.rooms[room_id][peer_id]

                # Notify the remaining peer (if any) that the other peer disconnected
                for remaining_peer_id, remaining_peer_ws in self.rooms[room_id].items():
                    print(f"⚠️ Notifying Peer {remaining_peer_id} that Peer {peer_id} has disconnected.")
                    await remaining_peer_ws.send_text(f"{MessageType.STATE} Disconnected")

                # Delete room if empty
                if not self.rooms[room_id]:
                    print(f"🗑️ Room {room_id} is now empty and will be deleted.")
                    del self.rooms[room_id]

@app.get("/")
async def root():
    print("🌍 WebRTC Signaling Server is running")
    return {"message": "WebRTC Signaling Server Running for Video Streaming"}

@app.websocket("/rtc/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """ Handles WebSocket connections for WebRTC signaling per room. """
    await websocket.accept()
    peer_id = str(uuid.uuid4())  # Unique ID for each peer
    session_manager = SessionManager()

    try:
        print(f"🔗 WebSocket Connection Opened for ✅ Peer {peer_id} in 🆕 Room {room_id}")
        print('.......')
        print('.......')
        print('.......')
        await session_manager.join_room(room_id, peer_id, websocket)

        while True:
            data = await websocket.receive_text()
            print(f"📨 Received WebRTC signaling message from Peer {peer_id} in Room {room_id}: {data}")
            await session_manager.relay_message(room_id, peer_id, data)

    except WebSocketDisconnect:
        print(f"🔴 Peer {peer_id} disconnected from Room {room_id}")
        await session_manager.leave_room(room_id, peer_id)
    except Exception as e:
        print(f"❌ ERROR: Session issue for Peer {peer_id} in Room {room_id}: {e}")
        await session_manager.leave_room(room_id, peer_id)

if __name__ == "__main__":
    print("🚀 Starting WebRTC Signaling Server...")
    uvicorn.run(app, host="0.0.0.0", port= int(os.environ.get('PORT', 8080)))
