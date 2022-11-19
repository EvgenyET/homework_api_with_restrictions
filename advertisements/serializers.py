from django.contrib.auth.models import User
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from advertisements.models import Advertisement, Favorites, AdvertisementStatusChoices

class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at',)

    def create(self, validated_data):
        """Метод для создания"""

        # Простановка значения поля создатель по-умолчанию.
        # Текущий пользователь является создателем объявления
        # изменить или переопределить его через API нельзя.
        # обратите внимание на `context` – он выставляется автоматически
        # через методы ViewSet.
        # само поле при этом объявляется как `read_only=True`
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):

        advs_open_count = self.Meta.model.objects.filter(creator=self.context["request"].user,
                                                    status=AdvertisementStatusChoices.OPEN).count()
        if advs_open_count > 9 and self.context["request"].method == "POST" or (self.context["request"].method == "PATCH" and data.get('status') == "OPEN"):
            raise ValidationError('Нельзя создать больше 10 объявлений')

        return data


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:

        model = Favorites
        fields = ('advertisement',)

    def validate(self, attrs):
        if self.context['request'].user == attrs['advertisement'].creator:
            raise ValidationError({'error': 'Нельзя добавлять собственные объявления'})

        if attrs['advertisement'].status == 'DRAFT':
            raise ValidationError({'error': 'Нельзя добавить объявление со статусом "Черновик"'})

        existing_fav = Favorites.objects.filter(user=self.context['request'].user)
        if attrs['advertisement'] in [fav.advertisement for fav in existing_fav]:
            raise ValidationError({'error': 'Данное объявление уже существует'})
        return attrs

    def create(self, validated_data):
        validated_data['user_id'] = self.context['request'].user.id
        return super().create(validated_data)
