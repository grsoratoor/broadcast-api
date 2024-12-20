from rest_framework import serializers

from .models import User, Broadcast


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['telegram_id', 'blocked']


class BroadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broadcast
        fields = ['id', 'message', 'created_at', 'status', 'total_target_users',
                  'total_successful', 'total_failed', 'users']
