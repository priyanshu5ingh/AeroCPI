from app.services.scrapy.spiders.base_spider import BaseAeroGuideSpider
from app.services.scrapy.spiders.trip_com_spider import TripComFlightSpider
from app.services.scrapy.spiders.easemytrip_spider import EaseMyTripFlightSpider
from app.services.scrapy.spiders.google_flights_spider import GoogleFlightsSpider

__all__ = [
    "BaseAeroGuideSpider",
    "TripComFlightSpider",
    "EaseMyTripFlightSpider",
    "GoogleFlightsSpider"
]
