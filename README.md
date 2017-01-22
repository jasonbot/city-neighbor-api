Primer Challenge
================

This is the coding challenge for Primer.

Because of time constraints, I chose to use bottle as the HTTP framework
and avoid any other third-party libraries.

To run, simply execute `python app.py` from the command line.

Endpoints
---------

Two endpoints exist:

    /city/<city_id>
    /city/<city_id>/neighbors

The `neighbors` endpoint accepts two optional `GET` parameters:

* `limit=n`, where n is a positive integer, will limit the number of results to `n`
* `in_country={true,false}`, where the value is a string literal `true` or `false`,
  will limit results to only be within the same country as the initial city.

Things I Would Have Done With More Time
---------------------------------------
* Look into a smarter datastore, likely starting with an ORM.
* Look into spatial indexing (though the dataset is pretty small). I'd likely
  go with an R-Tree _or_ put the data into PostGIS and set up a spatial index
  on the data there.
* If this app needs more flexibility, a more extensible framework would make
  sense. Bottle gives routing and JSON more or less for free which makes it
  easy to get up and running