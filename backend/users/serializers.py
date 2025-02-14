from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    conf_password = serializers.CharField(write_only=True)
    # Adding these fields as write only so that they can not be read by the API
    class Meta:
        model = User
        fields = ["id", "name", "email", "username", "password", "conf_password"]
        extra_kwargs = {"password": {"write_only": True}, "conf_password": {"write_only": True}}
    
    def validate(self, data):
        if data["password"] != data["conf_password"]:
            raise serializers.ValidationError({"conf_password": "Passwords do not match."})
        return data
    
    def create(self, validated):
        validated.pop("conf_password")
        user = User.objects.create_user(**validated)
        return user