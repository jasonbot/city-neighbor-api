#! python

"""Simple bottle webapp that uses an in-memory sqlite3 database to query cities from the
Geonames cities1000 file."""

import csv
import math
import os
import sqlite3
import sys
import zipfile

from bottle import abort, route, run, request

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
        """Function to register in SQL to do spatial distances"""
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
                        geonameid         int unique,
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

    def city_info(self, city_id):
        """Return a dict with the important information about a city by ID. Returns
        None if the city is missing from the database."""
        with self._connection as conn:
            for row in conn.execute("""
                select name, longitude, latitude, country_code from geonames
                where geonameid = ?
            """, (city_id,)):
                return {
                    'name': row[0],
                    'longitude': row[1],
                    'latitude': row[2],
                    'country_code': row[3]
                }

    def city_neighbors(self, city_id, result_count=None, limit_to_country=False):
        """Returns a sequence of dictionaries of the closest cities to the specified
        city_id. If result_count is set, it will add an optional record limit to the
        query. If limit_to_country is true, only records with the same country code
        will load.
        """

        city_info = self.city_info(city_id)

        base_query = """
            select geonameid, name, longitude, latitude, country_code,
                   geo_distance(?, ?, latitude, longitude) as distance
            from geonames
            {where_clause}
            order by distance ASC
            {limit_clause}
        """

        limit_clause = 'LIMIT ?' if result_count is not None else ''
        where_clause = 'WHERE country_code = ?' if limit_to_country else ''

        # Add the WHERE country_code and LIMIT n pieces to the clause if needed
        query = base_query.format(limit_clause=limit_clause, where_clause=where_clause)

        base_arguments = (city_info['latitude'], city_info['longitude'])

        # Alter the parameters called into the .execute function if needed
        if where_clause:
            base_arguments += (city_info['country_code'],)

        if limit_clause:
            base_arguments += (result_count,)

        with self._connection as conn:
            for row in conn.execute(query, base_arguments):
                yield {
                    'id': row[0],
                    'name': row[1],
                    'longitude': row[2],
                    'latitude': row[3],
                    'country_code': row[4],
                    'distance': row[5]
                }


class Application(object):
    """Adds a small abstraction layer on top of bottle's routing system so the sqlite3
    connection is initialized and cached before each query."""
    def __init__(self, database):
        self._database = database
        self.register_routes()

    def city_info(self, city_id):
        """City info (/city_id) endpoint"""
        city_info = self._database.city_info(city_id)
        if not city_info:
            abort(404, 'Missing city')
        return city_info

    def city_neighbors(self, city_id):
        """Nearest neighbors (/city_id/neighbors endpoint)"""
        city_info = self._database.city_info(city_id)
        if not city_info:
            abort(404, 'Missing city')

        q_limit = int(request.query.limit or '-1')  # pylint: disable=E1101
        q_country = request.query.in_country or 'false'  # pylint: disable=E1101

        limit = None if q_limit == -1 else q_limit
        country = True if q_country.lower() == 'true' else False

        print (limit, country)

        return {'results': list(self._database.city_neighbors(city_id, result_count=limit,
                                                              limit_to_country=country))}

    def register_routes(self):
        """Add routes to locally running bottle instance."""
        route('/city/<city_id:int>')(self.city_info)
        route('/city/<city_id:int>/')(self.city_info)
        route('/city/<city_id:int>/neighbors')(self.city_neighbors)
        route('/city/<city_id:int>/neighbors/')(self.city_neighbors)

if __name__ == "__main__":
    bottle_app = Application(GeoDatabase())  # pylint: disable=C0103

    run(host='localhost', port=8080, reload=True)
