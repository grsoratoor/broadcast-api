from django.contrib import admin

from broadcast.models import User, Broadcast


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'blocked')
    search_fields = ('telegram_id',)
    list_filter = ('blocked',)


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'created_at', 'status', 'total_target_users',
                    'total_successful', 'total_failed', 'users')
    search_fields = ('message',)
    list_filter = ('status', 'created_at')
