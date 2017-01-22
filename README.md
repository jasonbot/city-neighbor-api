Primer Challenge
================

This is the coding challenge for Primer.

Because of time constraints, I chose to use bottle as the HTTP framework
and avoid any other third-party libraries.

To run, simply clone this repo and execute `python app.py` from the command line.

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
* Finish the spelling suggestion endpoint. I was going to use
  [`get_close_matches`](https://docs.python.org/2.7/library/difflib.html?highlight=difflib#difflib.get_close_matches)
  to avoid a third party lib but I'd prefer to use some edit distance function
  in the database or maybe use NLTK.
* Look into a smarter datastore, likely starting with an ORM.
* Look into spatial indexing (though the dataset is pretty small). I'd likely
  go with an R-Tree _or_ put the data into PostGIS and set up a spatial index
  on the data there.
* If this app needs more flexibility, a more extensible framework would make
  sense. Bottle gives routing and JSON more or less for free which makes it
  easy to get up and running but even something nicer like Flask would make it
  more maintainable long term.
* Test suite. I incrementally built this app up using superfluous prints, to
  make it "trustable" I'd build up at least one small unit test suite.
* Build/tooling scripts to spin up a virtualenv based on a `requirements.txt`,
  scripts that get called from git hooks to auto-lint the codebase.