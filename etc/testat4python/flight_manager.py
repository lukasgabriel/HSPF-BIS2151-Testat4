# flight_manager.py

'''
This console application manages the information used by an air travel catering company.
'''

import pandas as pd
import urllib.request
from datetime import datetime, timedelta
from hashids import Hashids

import data.examples


# airports_url = 'https://raw.githubusercontent.com/datasets/airport-codes/master/data/airport-codes.csv'  # Only using local copy while testing
airports_fallback = 'data\\airport-codes.csv'

# countries_url = 'https://raw.githubusercontent.com/datasets/country-codes/master/data/country-codes.csv'  # Only using local copy while testing
countries_fallback = 'data\\country-codes.csv'

flights = []
dishes = []

def load_airports():
    try:
        filename = airports_url  # Try to get current list from dataset mirror on github
        urllib.request.urlopen(airports_url).getcode()
    except:
        print('Cannot reach airport dataset. Using local copy...')
        filename = airports_fallback  # Local copy as fallback if that fails for any reason

    # Read csv source file into a pandas dataframe for faster lookup
    airport_reader = pd.read_csv(filename, usecols=lambda column: column not in [
                                 'elevation_ft', 'gps_code', 'local_code', 'coordinates', 'ident'], engine='c', keep_default_na=False)
    # Drop airports without IATA code (small airports/helipads etc)
    airports_iata = airport_reader.dropna(subset=['iata_code'])
    airports_indexed = airports_iata.set_index('iata_code')
    return airports_indexed
airports = load_airports()


def load_countries():
    try:
        filename = countries_url  # Try to get current list from dataset mirror on github
        urllib.request.urlopen(countries_url).getcode()
    except:
        print('Cannot reach country dataset. Using local copy...')
        filename = countries_fallback  # Local copy as fallback if that fails for any reason

    # Read csv source file into a pandas dataframe for faster lookup
    country_reader = pd.read_csv(filename, usecols=[
                                 'ISO3166-1-Alpha-2', 'CLDR display name'], engine='c', keep_default_na=False)
    countries_indexed = country_reader.set_index('ISO3166-1-Alpha-2')
    return countries_indexed
countries = load_countries()

def get_airport_data(origin_airport_iata, destination_airport_iata):
    origin_data = dict(airports.loc[origin_airport_iata])
    destination_data = dict(airports.loc[destination_airport_iata])
    return origin_data, destination_data

def get_country_data(origin_iso_country, destination_iso_country):
    origin_country = dict(countries.loc[origin_iso_country])[
        'CLDR display name']
    destination_country = dict(countries.loc[destination_iso_country])[
        'CLDR display name']
    return origin_country, destination_country


class Dish():

    dish_hashid = Hashids()
    dish_data_fields = [
        'dish_data',
        'dish_id',
        'dish_shortname',
        'dish_name',
        'is_vegetarian',
        'is_vegan',
        'is_alcohol',
        'allergens',
        'dish_type',
        'dish_type_short',
        'price',
        'weight',
        'calories',
        'flights'
    ]

    dish_types = {'dessert': 'DST', 'warm-lunch': 'WLU', 'cold-lunch': 'CLU', 'warm-dinner': 'WDI', 'cold-dinner': 'CDI',
                  'warm-breakfast': 'WBR', 'cold-breakfast': 'CBR', 'sidedish': 'SDE', 'warm-beverage': 'WBV', 'cold-beverage': 'CBV', 'snack': 'SNA'}

    __slots__ = dish_data_fields

    def __init__(self, dish_data: dict):
        self.dish_data = dish_data

        self.dish_name = dish_data['dish_name']
        self.is_vegetarian = dish_data['is_vegetarian']
        self.is_vegan = False if not self.is_vegetarian else dish_data['is_vegan']
        self.is_alcohol = dish_data['is_alcohol']
        self.allergens = dish_data['allergens'] if 'allergens' in dish_data else []
        self.dish_type = dish_data['dish_type']
        self.dish_type_short = self.dish_types[self.dish_type]
        self.price = dish_data['price']
        self.weight = dish_data['weight']
        self.calories = dish_data['calories']

        dish_to_ints = ''
        for x in [ord(char) + 2 for char in (self.dish_name.replace(" ", "").lower() + self.dish_type_short).lower()]:
            dish_to_ints += (str(x))

        self.dish_id = self.dish_hashid.encode(int(self.price * 100), self.weight, self.calories, int(
            self.is_vegetarian), int(self.is_vegan), int(self.is_alcohol), int(dish_to_ints))
        self.dish_shortname = f'{self.dish_id[:3].upper()}_{self.dish_name.replace(" " , "").replace("-", "").replace("_", "").upper()[:6]}-{self.dish_type_short}_{int(self.price * 100)}_{int(self.is_vegetarian)}{int(self.is_vegan)}{int(self.is_alcohol)}'

        self.flights = []

    def add_flight(self, flight):
        if not isinstance(flight, Flight): 
            raise TypeError
        
        self.flights.append(flight)

    def remove_flight(self, flight):
        self.flights.remove(flight)
        print(f'Removed {flight} from {self} in dish record.')

    def __str__(self):
        return self.dish_shortname

    def __repr__(self):
        return f'Dish({self.dish_data})'

    def delete(self):
        while self.flights:
            for flight in self.flights:
                flight.remove_dish(self)
        dishes.remove(self)
        print(f'Deleting dish {self}...')
        del self


class Flight():

    flight_hashid = Hashids()
    flight_data_fields = [
        'flight_data',
        'flight_id',
        'flight_shortname',
        'flight_description',
        'origin_airport_iata',
        'destination_airport_iata',
        'origin_data',
        'destination_data',
        'origin_airport_name',
        'destination_airport_name',
        'origin_iso_country',
        'destination_iso_country',
        'origin_country',
        'destination_country',
        'origin_municipality',
        'destination_municipality',
        'origin_iso_region',
        'destination_iso_region',
        'departure_time',
        'arrival_time',
        'flight_duration',
        'is_international',
        'is_intercontinental',
        'flight_type',
        'passengers',
        'passenger_count',
        'dishes'
    ]

    __slots__ = flight_data_fields

    def __init__(self, flight_data: dict):
        self.flight_data = flight_data

        self.origin_airport_iata = flight_data['origin_airport_iata']
        self.destination_airport_iata = flight_data['destination_airport_iata']
        self.origin_data, self.destination_data = get_airport_data(
            self.origin_airport_iata, self.destination_airport_iata)

        self.origin_airport_name = self.origin_data['name']
        self.destination_airport_name = self.destination_data['name']

        self.origin_iso_country = self.origin_data['iso_country']
        self.destination_iso_country = self.destination_data['iso_country']
        self.origin_country, self.destination_country = get_country_data(
            self.origin_iso_country, self.destination_iso_country)

        self.origin_iso_region = self.origin_data['iso_region']
        self.destination_iso_region = self.destination_data['iso_region']
        self.origin_municipality = self.origin_data['municipality']
        self.destination_municipality = self.destination_data['municipality']

        self.passengers = flight_data['passengers']
        self.passenger_count = sum(self.passengers.values())

        self.departure_time = flight_data['departure_time']
        self.arrival_time = flight_data['arrival_time']
        self.flight_duration = self.arrival_time - self.departure_time

        self.is_intercontinental = True if self.origin_data[
            'continent'] != self.destination_data['continent'] else False
        self.is_international = True if self.origin_data[
            'iso_country'] != self.destination_data['iso_country'] else False
        self.flight_type = 'Intercontinental' if self.is_intercontinental else 'International' if self.is_international else 'Domestic'

        iata_to_ints = ''
        for x in [ord(char) + 2 for char in (self.origin_airport_iata + self.destination_airport_iata).lower()]:
            iata_to_ints += (str(x))

        self.flight_id = self.flight_hashid.encode(self.passenger_count, int(self.departure_time.strftime(
            "%y%m%d%H%M")), int(self.flight_duration.total_seconds()), int(iata_to_ints))
        self.flight_shortname = f'{self.flight_id[:3].upper()}_{self.origin_airport_iata}-{self.destination_airport_iata}_{self.departure_time.strftime("%y%m%d%H%M")}'
        self.flight_description = f'{self.flight_type} flight from {self.origin_airport_name} in {self.origin_municipality}{", " + self.origin_country if self.is_international else ""} to {self.destination_airport_name} in {self.destination_municipality}{", " + self.destination_country if self.is_international else ""}, departing on {self.departure_time.strftime("%d.%m.%y")} at {self.departure_time.strftime("%H:%M")} with {self.passenger_count} passengers.'


        self.dishes = []

    def add_dish(self, dish):
        if not isinstance(dish, Dish):
            raise TypeError

        dish.add_flight(self)
        self.dishes.append(dish)

    def remove_dish(self, dish):
        dish.remove_flight(self)
        self.dishes.remove(dish)
        print(f'Removed {dish} from {self} in flight record.')

    def __str__(self):
        return self.flight_shortname

    def __repr__(self):
        return f'Flight({self.flight_data})'

    def delete(self):
        while self.dishes:
            for dish in self.dishes:
                self.remove_dish(dish)
        flights.remove(self)
        print(f'Deleting flight {self}...')
        del self


def new_flight(flight_data: dict) -> Flight:
    flight = Flight(flight_data)
    flights.append(flight)
    return

def new_dish(dish_data: dict) -> Dish:
    dish = Dish(dish_data)
    dishes.append(dish)
    return


for dish in data.examples.example_dishes:
    new_dish(dish)

for flight in data.examples.example_flights:
    new_flight(flight)
