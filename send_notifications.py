import os
import json
import firebase_admin
from firebase_admin import credentials, db, messaging

SERVICE_ACCOUNT = json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])
DATABASE_URL = os.environ["FIREBASE_DATABASE_URL"]

cred = credentials.Certificate(SERVICE_ACCOUNT)
firebase_admin.initialize_app(cred, {
    "databaseURL": DATABASE_URL
})

def send_to_user(uid, sender, text, chat_id):
    token_data = db.reference(f"fcmTokens/{uid}/token").get()

    if not token_data:
        return False

    msg = messaging.Message(
        token=token_data,
        notification=messaging.Notification(
            title=sender,
            body=text[:200]
        ),
        data={
            "chatId": chat_id,
            "senderName": sender,
            "message": text[:200]
        }
    )

    messaging.send(msg)
    return True

def main():
    chats = db.reference("chats").get() or {}

    for chat_id, chat in chats.items():
        messages = chat.get("messages", {})
        members = chat.get("members", {})

        if not isinstance(messages, dict):
            continue

        if not isinstance(members, dict):
            continue

        for message_id, message in messages.items():
            if not isinstance(message, dict):
                continue

            sender_uid = message.get("sender")
            text = message.get("text", "")

            if not sender_uid or not text:
                continue

            sender_name = message.get("senderName", "Новое сообщение")

            for uid in members:
                if uid == sender_uid:
                    continue

                marker = db.reference(
                    f"notificationSent/{chat_id}/{message_id}/{uid}"
                )

                if marker.get():
                    continue

                try:
                    sent = send_to_user(
                        uid, sender_name, text, chat_id
                    )

                    if sent:
                        marker.set(True)

                except Exception as e:
                    print("Send failed:", str(e))

if __name__ == "__main__":
    main()
