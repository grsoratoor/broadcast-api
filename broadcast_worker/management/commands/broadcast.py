import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from broadcast.models import Broadcast, User

import requests


class Command(BaseCommand):
    help = "Processes pending broadcasts and sends messages to users"

    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        exit("BOT_TOKEN environment variable not set")
    RATE_LIMIT = 30  # Telegram allows 30 messages per second
    BATCH_SIZE = 30  # Number of users to process in one batch
    TELEGRAM_BOT_API_URL = "https://api.telegram.org/bot{}".format(BOT_TOKEN)
    MAX_WORKERS = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the broadcast script...")
        try:
            self.process_broadcast()
        except KeyboardInterrupt:
            self.stdout.write("Broadcast script terminated by user.")

    def send_message(self, chat_id, broadcast):
        payload = {
            'chat_id': chat_id,
        }
        if broadcast.type == "text":
            url = f"{self.TELEGRAM_BOT_API_URL}/sendMessage"
            payload["text"] = broadcast.message
        elif broadcast.type == "image":
            url = f"{self.TELEGRAM_BOT_API_URL}/sendPhoto"
            payload['photo'] = broadcast.file_id
            payload["caption"] = broadcast.message
        elif broadcast.type == "video":
            url = f"{self.TELEGRAM_BOT_API_URL}/sendVideo"
            payload['video'] = broadcast.file_id
            payload["caption"] = broadcast.message

        if broadcast.buttons:
            inline_keyboard = []
            for btn in broadcast.buttons:
                if btn["web_app"]:
                    inline_keyboard.append([{"text": btn["text"], "web_app": {"url": btn["url"]}}])
                else:
                    inline_keyboard.append([{"text": btn["text"], "url": btn["url"]}])

            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return True
        except requests.exceptions.RequestException as e:
            # self.stderr.write(f"Failed to send message: {e}")
            return False

    def process_broadcast(self):
        while True:
            # Fetch the oldest pending broadcast
            broadcast = (
                Broadcast.objects
                .filter(status="pending")
                .order_by("created_at")
                .first()
            )

            if not broadcast:
                # self.stdout.write("No pending broadcasts. Sleeping for 10 seconds...")
                time.sleep(10)
                continue

            self.stdout.write(f"Processing broadcast ID: {broadcast.id}")
            broadcast.status = "inprogress"
            broadcast.save()

            # Update total targeted users
            total_targeted_users = len(broadcast.users) if broadcast.users else User.objects.count()
            broadcast.total_target_users = total_targeted_users
            broadcast.save(update_fields=["total_target_users"])

            successful = 0
            failed = 0

            # Process users in batches
            if broadcast.users:
                users = broadcast.users
            else:
                users = User.objects.values_list("telegram_id", flat=True).iterator(chunk_size=self.BATCH_SIZE)

            batch_no = 0
            for user_batch in self.batch_iterator(users, self.BATCH_SIZE):
                results = []
                batch_no += 1
                print(f"Processing batch {batch_no} with {len(user_batch)} users...")
                with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                    future_to_url = {executor.submit(self.send_message, user_id, broadcast): user_id for user_id in
                                     user_batch}
                    for future in as_completed(future_to_url):
                        results.append(future.result())

                # Handle results
                for result in results:
                    if result is False:
                        failed += 1
                    else:
                        successful += 1

                time.sleep(1)

                # Update progress incrementally in the database
                broadcast.total_successful = successful
                broadcast.total_failed = failed
                broadcast.save(update_fields=["total_successful", "total_failed"])

            # Mark broadcast as completed
            broadcast.total_successful = successful
            broadcast.total_failed = failed
            broadcast.status = "completed"
            broadcast.save()
            self.stdout.write(f"Broadcast {broadcast.id} completed: {successful} successful, {failed} failed.")

    def batch_iterator(self, iterator, batch_size):
        """Helper function to yield batches from an iterator."""
        batch = []
        for item in iterator:
            batch.append(item)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
