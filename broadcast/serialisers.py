from rest_framework import serializers

from .models import User, Broadcast


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['telegram_id']


class BroadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broadcast
        fields = ['id', 'message', 'type', 'buttons', 'file_id', 'created_at', 'status', 'total_target_users',
                  'total_successful', 'total_failed', 'users']
