from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteEvent, MegolmEvent, KeyVerificationStart, KeyVerificationCancel, KeyVerificationKey, KeyVerificationMac, LocalProtocolError
from glpi_client import GLPI
import traceback

class Callbacks:
    def __init__(self, client: AsyncClient, glpi: GLPI):
        self.client = client
        self.glpi = glpi

    async def message(self, room: MatrixRoom, event: RoomMessageText):
        if event.sender == self.client.user:
            return

        body = event.body
        print(f"[MESSAGE] {room.display_name} | {event.sender}: {body}")

        if body.startswith("!help"):
            help_text = (
                "Команды:\n"
                "!help — показать справку\n"
                "!tickets — показать последние тикеты GLPI (до 10)\n"
                "!create <Заголовок> | <Описание> — создать тикет\n\n"
                "Примеры:\n"
                "!tickets\n"
                "!create Не работает принтер | Не печатает со вчера, ошибка бумага\n"
            )
            await self.send(room.room_id, help_text)
        
        elif body.startswith("!tickets"):
            print("Fetching tickets...")
            tickets = self.glpi.get_tickets()
            if isinstance(tickets, list):
                # Format tickets
                msg = "Latest Tickets:\n"
                for t in tickets[:10]: # Limit to 10
                     msg += f"#{t.get('id')} - {t.get('name')} ({t.get('status')})\n"
            else:
                msg = str(tickets)
            await self.send(room.room_id, msg)

        elif body.startswith("!create"):
            parts = body[7:].split("|")
            if len(parts) < 2:
                await self.send(room.room_id, "Usage: !create Title | Content")
            else:
                title = parts[0].strip()
                content = parts[1].strip()
                res = self.glpi.create_ticket(title, content)
                await self.send(room.room_id, f"Ticket creation result: {res}")

    async def send(self, room_id, message):
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message},
                ignore_unverified_devices=True
            )
        except Exception as e:
            print(f"Failed to send message: {e}")

    async def invite(self, room: MatrixRoom, event: InviteEvent):
        print(f"[INVITE] Invited to {room.room_id} by {event.sender}")
        await self.client.join(room.room_id)
        print(f"[JOIN] Joined {room.room_id}")

    async def encrypted_message(self, room: MatrixRoom, event: MegolmEvent):
        print(f"[ENCRYPTED] Message in {room.display_name} from {event.sender}")
        # If we are here, it means nio failed to decrypt it automatically
        # or it's just notifying us of the event.
        # Check if decrypted content is available (nio might have decrypted it in the background)
        # But usually this callback is for the raw event.
        
        # If the event was not decrypted, request keys
        try:
            if not event.decrypted:
                 print(f"⚠️ Undecryptable message from {event.sender}. Requesting keys...")
                 await self.client.request_room_key(event)
        except Exception as e:
            pass # Already requested or other error

    # --- Verification Callbacks ---
    async def key_verification_start(self, event: KeyVerificationStart):
        print(f"[VERIFICATION] Request from {event.sender}")
        if "emoji" in event.methods:
            sas = self.client.key_verifications[event.transaction_id]
            sas.add_hooks({
                "show_sas": self.verification_show_sas,
                "done": self.verification_done,
            })
            await sas.accept_sas()

    async def verification_show_sas(self, sas, emojis, emoji_index, decimals):
        print(f"\n[VERIFICATION] EMOJIS: {emojis}")
        print("Auto-confirming emojis...")
        await sas.match()

    async def verification_done(self, sas):
        print(f"[VERIFICATION] Complete with {sas.other_device_id}")
