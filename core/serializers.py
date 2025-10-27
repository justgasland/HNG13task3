
from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'id', 'name', 'capital', 'region', 'population',
            'currency_code', 'exchange_rate', 'estimated_gdp',
            'flag_url', 'last_refreshed_at'
        ]
        read_only_fields = ['id', 'estimated_gdp', 'last_refreshed_at']

    def validate(self, data):
        if not data.get('name'):
            raise serializers.ValidationError({
                "name": "is required"
            })
        if not data.get('population'):
            raise serializers.ValidationError({
                "population": "is required"
            })
        return data