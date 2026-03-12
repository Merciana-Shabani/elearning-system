from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'full_name', 'role', 'bio', 'avatar', 'city', 'country',
                  'institution', 'department', 'date_joined']
        read_only_fields = ['id', 'date_joined']
