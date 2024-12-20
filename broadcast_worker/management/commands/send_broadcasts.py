import time

from django.core.management.base import BaseCommand

from broadcast.models import Broadcast, User


# from telegram import Bot, TelegramError


class Command(BaseCommand):
    help = "Processes pending broadcasts and sends messages to users"

    BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    RATE_LIMIT = 30  # Telegram allows 30 messages per second
    BATCH_SIZE = 1000  # Number of users to process in one batch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.bot = Bot(token=self.BOT_TOKEN)

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting the broadcast script...")
        try:
            self.process_broadcast()
        except KeyboardInterrupt:
            self.stdout.write("Broadcast script terminated by user.")

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
                self.stdout.write("No pending broadcasts. Sleeping for 10 seconds...")
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

            for user_batch in self.batch_iterator(users, self.BATCH_SIZE):
                for i, user_id in enumerate(user_batch):
                    try:
                        # self.bot.send_message(chat_id=user_id, text=broadcast.message)
                        print(user_id, broadcast.message)
                        successful += 1
                    except Exception as e:  # TelegramError as e:
                        self.stderr.write(f"Failed to send message to user {user_id}: {e}")
                        failed += 1

                    # Respect Telegram rate limits
                    if (i + 1) % self.RATE_LIMIT == 0:
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
