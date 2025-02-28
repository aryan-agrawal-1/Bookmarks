from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    conf_password = serializers.CharField(write_only=True)
    # Adding these fields as write only so that they can not be read by the API
    class Meta:
        model = User
        fields = ["id", "name", "email", "username", "password", "conf_password"]
        extra_kwargs = {"password": {"write_only": True}, "conf_password": {"write_only": True}}
    
    def validate(self, data):
        if len(data["password"]) < 6:
            raise serializers.ValidationError({"detail": "Passwords must be 6+ characters"})

        if data["password"] != data["conf_password"]:
            raise serializers.ValidationError({"detail": "Passwords do not match."})
        return data
    
    def create(self, validated):
        try:
            validated.pop("conf_password")
            user = User.objects.create_user(**validated)
            return user
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

# CUSTOMISING THE LOGIN
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError({"detail":"Both username and password are required."})

        user = User.objects.filter(email__iexact=email).first() or User.objects.filter(username__iexact=email).first()

        if not user:
            raise serializers.ValidationError({"detail": "User does not exist."})
        
        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Incorrect password."})

        if user and user.check_password(password):
            attrs['email'] = user.email
            return super().validate(attrs)

# FORGOT PASSWORD
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_pass = serializers.CharField(write_only = True)
    conf_pass = serializers.CharField(write_only = True)
    
    def validate(self, attrs):
        if attrs['new_pass'] != attrs['conf_pass']:
            raise serializers.ValidationError({"detail": "Passwords do not match."})
        
        if len(attrs['new_pass']) < 6:
            raise serializers.ValidationError({"detail": "Password must be at least 6 characters."})

        return attrs
