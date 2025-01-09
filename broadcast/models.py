from django.db import models


class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    blocked = models.BooleanField(default=False)


class Broadcast(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('inprogress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    MESSAGE_TYPE = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    message = models.TextField()
    buttons = models.JSONField(default=list)
    file_id = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=20, choices=MESSAGE_TYPE, default='text')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_target_users = models.PositiveIntegerField(default=0)  # Total users targeted
    total_successful = models.PositiveIntegerField(default=0)  # Users reached
    total_failed = models.PositiveIntegerField(default=0)  # Users not reached
    users = models.JSONField(null=True, blank=True)


class BroadcastTarget(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    broadcast = models.ForeignKey(Broadcast, on_delete=models.CASCADE, related_name='targets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='broadcasts')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
