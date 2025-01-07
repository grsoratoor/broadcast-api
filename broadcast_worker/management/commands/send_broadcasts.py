import asyncio
import os

from django.core.management.base import BaseCommand

from broadcast.models import Broadcast, User
from telegram import Bot
from telegram.error import TelegramError
from asgiref.sync import sync_to_async


class Command(BaseCommand):
    help = "Processes pending broadcasts and sends messages to users asynchronously"

    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        exit("BOT_TOKEN environment variable not set")
    RATE_LIMIT = 30  # Telegram allows 30 messages per second
    BATCH_SIZE = 30  # Number of users to process in one batch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = Bot(token=self.BOT_TOKEN)

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the broadcast script asynchronously...")
        try:
            asyncio.run(self.process_broadcast())
        except KeyboardInterrupt:
            self.stdout.write("Broadcast script terminated by user.")

    async def process_broadcast(self):
        while True:
            # Fetch the oldest pending broadcast asynchronously
            broadcast = await sync_to_async(self.get_pending_broadcast)()

            if not broadcast:
                self.stdout.write("No pending broadcasts. Sleeping for 10 seconds...")
                await asyncio.sleep(10)
                continue

            self.stdout.write(f"Processing broadcast ID: {broadcast.id}")
            broadcast.status = "inprogress"
            await sync_to_async(broadcast.save)()

            # Update total targeted users
            total_targeted_users = (
                len(broadcast.users) if broadcast.users else await sync_to_async(User.objects.count)()
            )
            broadcast.total_target_users = total_targeted_users
            await sync_to_async(broadcast.save)(update_fields=["total_target_users"])

            successful, failed = 0, 0

            # Process users in batches
            users = (
                broadcast.users
                if broadcast.users
                else await sync_to_async(
                    lambda: list(User.objects.values_list("telegram_id", flat=True))
                )()
            )

            for user_batch in self.batch_iterator(users, self.BATCH_SIZE):
                tasks = [
                    self.send_message(user_id, broadcast.message) for user_id in user_batch
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Handle results
                for result in results:
                    if isinstance(result, Exception):
                        failed += 1
                        self.stderr.write(f"Failed to send message: {result}")
                    else:
                        successful += 1

                # Respect Telegram rate limits
                await asyncio.sleep(1)

                # Update progress incrementally in the database
                broadcast.total_successful = successful
                broadcast.total_failed = failed
                await sync_to_async(broadcast.save)(update_fields=["total_successful", "total_failed"])

            # Mark broadcast as completed
            broadcast.total_successful = successful
            broadcast.total_failed = failed
            broadcast.status = "completed"
            await sync_to_async(broadcast.save)()
            self.stdout.write(f"Broadcast {broadcast.id} completed: {successful} successful, {failed} failed.")

    @staticmethod
    def batch_iterator(iterator, batch_size):
        """Helper function to yield batches from an iterator."""
        batch = []
        for item in iterator:
            batch.append(item)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    @staticmethod
    def get_pending_broadcast():
        """Fetch the oldest pending broadcast."""
        return Broadcast.objects.filter(status="pending").order_by("created_at").first()

    async def send_message(self, user_id, message):
        """Asynchronously send a message using the Telegram bot."""
        try:
            await self.bot.send_message(chat_id=user_id, text=message)
        except TelegramError as e:
            raise e
