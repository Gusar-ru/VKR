import asyncio
import logging
import sys
import os
from nio import AsyncClient, AsyncClientConfig, RoomMessageText, InviteEvent, MegolmEvent, KeyVerificationStart, KeyVerificationCancel, KeyVerificationKey, KeyVerificationMac, KeyVerificationAccept
from nio.crypto import Olm

from config import Config
from storage import Storage
from glpi_client import GLPI
from callbacks import Callbacks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def main():
    config = Config(os.path.join(os.getcwd(), "config", "config.yaml"))
    
    # Ensure store directory exists
    if not os.path.exists(config.store_path):
        os.makedirs(config.store_path)

    # Initialize GLPI
    glpi = GLPI(config.glpi_url, config.glpi_user, config.glpi_password, config.glpi_app_token)

    # Client Config
    client_config = AsyncClientConfig(
        encryption_enabled=True,
        store_sync_tokens=True,
    )

    # Initialize Client (store_path=None to avoid auto-init with broken DefaultStore)
    client = AsyncClient(
        config.homeserver,
        config.user_id,
        device_id=config.device_id,
        store_path=None, 
        config=client_config
    )
    
    # Restore access_token if available
    if config.access_token:
        client.access_token = config.access_token
        client.user_id = config.user_id # Ensure user_id is set
        client.device_id = config.device_id # Ensure device_id is set

    # Manual Store Initialization (Windows Fix)
    sanitized_user = config.user_id.replace(":", "_").replace("@", "")
    db_name = f"{sanitized_user}_{config.device_id}.db"
    
    print(f"Initializing Storage: {db_name}")
    client.store = Storage(
        config.user_id,
        config.device_id,
        config.store_path,
        database_name=db_name,
        pickle_key="DEFAULT_KEY"
    )

    print("Initializing Encryption...")
    client.olm = Olm(config.user_id, config.device_id, client.store)
    
    # Load the store
    print("Loading Store...")
    client.load_store()

    # Callbacks
    callbacks = Callbacks(client, glpi)
    client.add_event_callback(callbacks.message, RoomMessageText)
    client.add_event_callback(callbacks.invite, InviteEvent)
    client.add_event_callback(callbacks.encrypted_message, MegolmEvent)
    
    # Verification Callbacks
    client.add_to_device_callback(callbacks.key_verification_start, (KeyVerificationStart,))
    client.add_to_device_callback(callbacks.key_verification_start, (KeyVerificationCancel,))
    client.add_to_device_callback(callbacks.key_verification_start, (KeyVerificationKey,))
    client.add_to_device_callback(callbacks.key_verification_start, (KeyVerificationMac,))
    client.add_to_device_callback(callbacks.key_verification_start, (KeyVerificationAccept,))

    # Login
    if not client.access_token:
        print(f"Logging in as {config.user_id}...")
        try:
            resp = await client.login(config.password)
            print(f"Login Response Type: {type(resp)}")
            if hasattr(resp, 'access_token'):
                print(f"Logged in! Access Token: {resp.access_token[:10]}...")
            else:
                print(f"Login failed: {resp}")
                return
        except Exception as e:
            print(f"Login Error: {e}")
            import traceback
            traceback.print_exc()
            return
    else:
        print(f"Using existing access token for {config.user_id}")

    # Sync Loop
    print("Starting Initial Sync...")
    try:
        await client.sync(timeout=30000, full_state=True)
        print("Querying keys for encrypted rooms...")
        for room_id, room in client.rooms.items():
            if room.encrypted:
                client.users_for_key_query.update(room.users.keys())
        print("Executing keys_query...")
        await client.keys_query()
        print("Claiming keys for devices...")
        user_device_map = {}
        for room_id, room in client.rooms.items():
            if room.encrypted:
                for user_id in room.users:
                    devices = client.device_store[user_id]
                    if devices:
                        user_device_map[user_id] = list(devices.keys())
        if user_device_map:
            await client.keys_claim(user_device_map)
        print("Starting Sync Loop...")
        await client.sync_forever(timeout=30000)
    except Exception as e:
        print(f"Sync Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
