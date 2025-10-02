from rest_framework import serializers
from accounts.models import MyUsers, UserProfile

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.name', read_only=True)
    profile_img = serializers.ImageField(source='profile.profile_img', read_only=True)

    class Meta:
        model = MyUsers
        fields = ['id', 'username', 'email', 'name', 'profile_img', 'is_verified']
