#! python

import csv
import math
import os
import sqlite3
import sys
import zipfile

from bottle import route, run

# Set up a database/data-structure and thin frontend system with a REST interface that
# supports the following operations:

# Given a city identifier X, we can query for the K "closest" cities (optionally limited to
# the same country), where "closeness" is measured using an appropriately chosen measure of
# distance by latitude and longitude.

# (Depending on time) Given an input string (potentially multiple words), query for the city
# identifiers that match it.

class GeoDatabase(object):
    """Represents a (typically in-memory) geonames database."""

    def __init__(self, sql_path=':memory:'):
        self._connection = None
        self.load_cities(sql_path)

    # http://gis.stackexchange.com/questions/4906/why-is-law-of-cosines-more-preferable-than-haversine-when-calculating-distance-b
    @staticmethod
    def spatial_distance(lat1, lon1, lat2, lon2):
        """Function to register in SQL to do distances"""
        lat1, lon1, lat2, lon2 = tuple(math.radians(float(value))
                                       for value in (lat1, lon1, lat2, lon2))

        return (math.acos(math.sin(lat1) * math.sin(lat2) +
                          math.cos(lat1) *
                          math.cos(lat2) *
                          math.cos(lon2-lon1))*6371.0)

    def create_sql_db(self, sqlpath, row_sequence):
        """Create SQL database, register distance finding function"""
        self._connection = sqlite3.connect(sqlpath)

        self._connection.create_function('geo_distance', 4, self.spatial_distance)

        with self._connection as conn:
            conn.execute(
                """
                    create table geonames(
                        geonameid         int,
                        name              varchar(200),
                        asciiname         varchar(200),
                        latitude          float,
                        longitude         float,
                        country_code      varchar(4)
                    )
                """
            )

        with self._connection as conn:
            conn.executemany("""
                            insert into geonames(geonameid, name, asciiname,
                                                latitude, longitude, country_code)
                            values (?, ?, ?, ?, ?, ?)
                            """, row_sequence)

    @staticmethod
    def filter_rows(reader):
        """Pull out necessary columns, format them correctly for insertion to DB"""
        for row in reader:
            geo_id = int(row[0])
            name = row[1].decode('utf-8')
            ascii_name = row[2].decode('utf-8')
            latitude = float(row[4])
            longitude = float(row[5])
            country_code = row[8].decode('utf-8')

            yield (geo_id, name, ascii_name, latitude, longitude, country_code)


    def load_cities(self, sqlpath=":memory:"):
        """Loads in the contents of cities1000.zip into a sqlite database"""

        # cities1000.zip should be in this same directory
        file_dir = os.path.dirname(os.path.abspath(__file__))
        file_name = 'cities1000.zip'
        full_zip_path = os.path.join(file_dir, file_name)

        # File in zip archive
        member_name = 'cities1000.txt'

        with zipfile.ZipFile(full_zip_path, mode='r') as z:
            handle = z.open(member_name)

            reader = csv.reader(handle, delimiter='\t')

            # Hack: work around default field size limit in CSV module
            csv.field_size_limit(sys.maxsize)

            self.create_sql_db(sqlpath, self.filter_rows(reader))

geo_db = GeoDatabase()

@route('/city/<city_id:int>')
def city_info(city_id):
    geo_db.get_city(city_id)

if __name__ == "__main__":
    run(host='localhost', port=8080)