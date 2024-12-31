from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from broadcast.models import User, Broadcast
from broadcast.serialisers import BroadcastSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = UserSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Users created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BroadcastViewSet(ModelViewSet):
    queryset = Broadcast.objects.all()
    serializer_class = BroadcastSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Specify fields for exact match filtering
    filterset_fields = ['status', 'created_at']

    # Specify fields for text search
    search_fields = ['message']

    # Specify fields for ordering
    ordering_fields = ['created_at', 'total_target_users', 'total_successful', 'total_failed']
    ordering = ['created_at']  # Default ordering


def index(request):
    return render(request, 'index.html')
