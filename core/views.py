from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse, JsonResponse
from django.db.models import Q
import requests
import random
from decimal import Decimal
from datetime import datetime
import os

from .models import Country, RefreshStatus
from .serializers import CountrySerializer
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

class RefreshCountriesView(APIView):
    """POST /countries/refresh - Fetch and cache all countries"""
    
    def post(self, request):
        try:
            # Fetch countries data
            countries_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
            try:
                countries_response = requests.get(countries_url, timeout=30)
                countries_response.raise_for_status()
                countries_data = countries_response.json()
            except requests.RequestException as e:
                return Response({
                    "error": "External data source unavailable",
                    "details": f"Could not fetch data from restcountries.com"
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Fetch exchange rates
            exchange_url = "https://open.er-api.com/v6/latest/USD"
            try:
                exchange_response = requests.get(exchange_url, timeout=30)
                exchange_response.raise_for_status()
                exchange_data = exchange_response.json()
                exchange_rates = exchange_data.get('rates', {})
            except requests.RequestException as e:
                return Response({
                    "error": "External data source unavailable",
                    "details": f"Could not fetch data from open.er-api.com"
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # Process and save countries
            saved_count = 0
            for country_data in countries_data:
                name = country_data.get('name', '')
                if not name:
                    continue

                capital = country_data.get('capital', '')
                region = country_data.get('region', '')
                population = country_data.get('population', 0)
                flag_url = country_data.get('flag', '')
                
                # Handle currencies
                currencies = country_data.get('currencies', [])
                currency_code = None
                exchange_rate = None
                estimated_gdp = None

                if currencies and len(currencies) > 0:
                    # Get first currency code
                    currency_code = currencies[0].get('code')
                    
                    if currency_code and currency_code in exchange_rates:
                        exchange_rate = Decimal(str(exchange_rates[currency_code]))
                        # Calculate estimated GDP
                        random_multiplier = random.uniform(1000, 2000)
                        estimated_gdp = Decimal(str(population * random_multiplier / float(exchange_rate)))
                
                # If no currency or exchange rate not found, set GDP to 0
                if estimated_gdp is None:
                    estimated_gdp = Decimal('0')

                # Update or create country
                Country.objects.update_or_create(
                    name__iexact=name,
                    defaults={
                        'name': name,
                        'capital': capital,
                        'region': region,
                        'population': population,
                        'currency_code': currency_code,
                        'exchange_rate': exchange_rate,
                        'estimated_gdp': estimated_gdp,
                        'flag_url': flag_url,
                    }
                )
                saved_count += 1

            # Update refresh status
            total_countries = Country.objects.count()
            RefreshStatus.objects.update_or_create(
                id=1,
                defaults={
                    'last_refreshed_at': timezone.now(),
                    'total_countries': total_countries
                }
            )

            # Generate summary image
            self.generate_summary_image(total_countries)

            return Response({
                "message": "Countries refreshed successfully",
                "total_countries": total_countries,
                "processed": saved_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Internal server error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def generate_summary_image(self, total_countries):
        """Generate summary image with top 5 countries by GDP"""
        try:
            # Get top 5 countries by GDP
            top_countries = Country.objects.filter(
                estimated_gdp__isnull=False
            ).order_by('-estimated_gdp')[:5]

            # Create image
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color='#667eea')
            draw = ImageDraw.Draw(img)

            # Try to use a nice font, fallback to default
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()

            # Draw title
            draw.text((50, 50), "Country Summary Report", fill='white', font=title_font)
            
            # Draw total countries
            draw.text((50, 120), f"Total Countries: {total_countries}", fill='white', font=text_font)
            
            # Draw top 5 countries
            draw.text((50, 180), "Top 5 Countries by Estimated GDP:", fill='white', font=text_font)
            
            y_position = 220
            for i, country in enumerate(top_countries, 1):
                gdp_formatted = f"${country.estimated_gdp:,.2f}"
                text = f"{i}. {country.name} - {gdp_formatted}"
                draw.text((70, y_position), text, fill='white', font=text_font)
                y_position += 40

            # Draw timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((50, height - 80), f"Last Updated: {timestamp}", fill='white', font=text_font)

            # Save image
            cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            image_path = os.path.join(cache_dir, 'summary.png')
            img.save(image_path)

        except Exception as e:
            print(f"Error generating image: {e}")


class CountriesListView(APIView):
    """GET /countries - Get all countries with filters and sorting"""
    
    def get(self, request):
        try:
            queryset = Country.objects.all()

            # Filter by region
            region = request.query_params.get('region')
            if region:
                queryset = queryset.filter(region__iexact=region)

            # Filter by currency
            currency = request.query_params.get('currency')
            if currency:
                queryset = queryset.filter(currency_code__iexact=currency)

            # Sorting
            sort = request.query_params.get('sort')
            if sort == 'gdp_desc':
                queryset = queryset.order_by('-estimated_gdp')
            elif sort == 'gdp_asc':
                queryset = queryset.order_by('estimated_gdp')
            elif sort == 'population_desc':
                queryset = queryset.order_by('-population')
            elif sort == 'population_asc':
                queryset = queryset.order_by('population')

            serializer = CountrySerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CountryDetailView(APIView):
    """GET/DELETE /countries/:name - Get or delete a country"""
    
    def get(self, request, name):
        try:
            country = Country.objects.get(name__iexact=name)
            serializer = CountrySerializer(country)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Country.DoesNotExist:
            return Response({
                "error": "Country not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, name):
        try:
            country = Country.objects.get(name__iexact=name)
            country.delete()
            return Response({
                "message": f"Country '{name}' deleted successfully"
            }, status=status.HTTP_200_OK)
        except Country.DoesNotExist:
            return Response({
                "error": "Country not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatusView(APIView):
    """GET /status - Show total countries and last refresh timestamp"""
    
    def get(self, request):
        try:
            total_countries = Country.objects.count()
            refresh_status = RefreshStatus.objects.filter(id=1).first()
            
            last_refreshed = None
            if refresh_status:
                last_refreshed = refresh_status.last_refreshed_at.isoformat()
            
            return Response({
                "total_countries": total_countries,
                "last_refreshed_at": last_refreshed
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CountryImageView(APIView):
    """GET /countries/image - Serve summary image"""
    
    def get(self, request):
        try:
            cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
            image_path = os.path.join(cache_dir, 'summary.png')
            
            if os.path.exists(image_path):
                return FileResponse(open(image_path, 'rb'), content_type='image/png')
            else:
                return Response({
                    "error": "Summary image not found"
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)