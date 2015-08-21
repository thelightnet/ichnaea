"""
Contains helper functions for various geo related calculations.
"""

import functools
import math
import os

from country_bounding_boxes import country_subunits_by_iso_code
from six import string_types

from ichnaea import constants

try:
    from ichnaea import _geocalc
except ImportError:  # pragma: no cover
    if not os.environ.get('READTHEDOCS', None) == 'True':
        raise

_radius_cache = {}


def add_meters_to_latitude(lat, distance):
    """
    Return a latitude in degrees which is shifted by
    distance in meters.

    The new latitude is bounded by our globally defined
    :data:`ichnaea.constants.MIN_LAT` and
    :data:`ichnaea.constants.MAX_LAT`.
    """
    # A suitable estimate for surface level calculations is
    # 111,111m = 1 degree latitude
    new_lat = lat + (distance / 111111.0)
    return bound(constants.MIN_LAT, new_lat, constants.MAX_LAT)


def add_meters_to_longitude(lat, lon, distance):
    """
    Return a longitude in degrees which is shifted by
    distance in meters.

    The new longitude is bounded by our globally defined
    :data:`ichnaea.constants.MIN_LON` and
    :data:`ichnaea.constants.MAX_LON`.
    """
    # A suitable estimate for surface level calculations is
    # 111,111m = 1 degree latitude
    new_lon = lon + (distance / (math.cos(lat) * 111111.0))
    return bound(constants.MIN_LON, new_lon, constants.MAX_LON)


def bound(low, value, high):
    """
    If value is between low and high, return value.
    If value is below low, return low.
    If value is above high, return high.
    If low is below high, raise an exception.
    """
    return max(low, min(value, high))


def centroid(points):
    """
    Compute the centroid (average lat and lon) from a set of points
    (two-dimensional lat/lon array).
    """
    avg_lat, avg_lon = _geocalc.centroid(points)
    return (float(avg_lat), float(avg_lon))


def circle_radius(lat, lon, max_lat, max_lon, min_lat, min_lon):
    """
    Compute the maximum distance, in meters, from a (lat, lon) point
    to any of the extreme points of a bounding box.
    """
    edges = [(min_lat, min_lon),
             (min_lat, max_lon),
             (max_lat, min_lon),
             (max_lat, max_lon)]

    center_distance = functools.partial(_geocalc.distance, lat, lon)
    radius = max([center_distance(edge[0], edge[1]) for edge in edges])
    return int(round(radius))


def distance(lat1, lon1, lat2, lon2):
    """
    Compute the distance between a pair of lat/longs in meters using
    the haversine calculation. The output distance is in meters.

    Error is up to 0.55%, which works out to 5m per 1km. This is
    still better than what GPS provides so it should be 'good enough'.

    References:
      * http://en.wikipedia.org/wiki/Haversine_formula
      * http://www.movable-type.co.uk/scripts/latlong.html

    Accuracy: since the earth is not quite a sphere, there are small
    errors in using spherical geometry; the earth is actually roughly
    ellipsoidal (or more precisely, oblate spheroidal) with a radius
    varying between about 6378km (equatorial) and 6357km (polar),
    and local radius of curvature varying from 6336km (equatorial
    meridian) to 6399km (polar). 6371 km is the generally accepted
    value for the Earth's mean radius. This means that errors from
    assuming spherical geometry might be up to 0.55% crossing the
    equator, though generally below 0.3%, depending on latitude and
    direction of travel. An accuracy of better than 3m in 1km is
    mostly good enough for me, but if you want greater accuracy, you
    could use the Vincenty formula for calculating geodesic distances
    on ellipsoids, which gives results accurate to within 1mm.
    """
    return _geocalc.distance(lat1, lon1, lat2, lon2)


def estimate_accuracy(lat, lon, points, minimum):
    """
    Return the maximum range between a position (lat/lon) and a
    list of secondary positions (points). But at least use the
    specified minimum value.
    """
    if len(points) == 1:
        accuracy = points[0].range
    else:
        # Terrible approximation, but hopefully better
        # than the old approximation, "worst-case range":
        # this one takes the maximum distance from position
        # to any of the provided points.
        accuracy = max([distance(lat, lon, p.lat, p.lon)
                        for p in points])
    if accuracy is not None:
        accuracy = float(accuracy)
    return max(accuracy, minimum)


def location_is_in_country(lat, lon, country_code, margin=0):
    """
    Return whether or not a given (lat, lon) pair is inside one of the
    country subunits associated with a given alpha2 country code.

    """
    for country in country_subunits_by_iso_code(country_code):
        (lon1, lat1, lon2, lat2) = country.bbox
        if lon1 - margin <= lon and lon <= lon2 + margin and \
           lat1 - margin <= lat and lat <= lat2 + margin:
            return True
    return False


def maximum_country_radius(country_code):
    """
    Return the maximum radius of a circle encompassing the largest
    country subunit in meters, rounded to 1 km increments.
    """
    if not isinstance(country_code, string_types):
        return None
    country_code = country_code.upper()
    if len(country_code) not in (2, 3):
        return None

    value = _radius_cache.get(country_code, None)
    if value:
        return value

    diagonals = []
    for country in country_subunits_by_iso_code(country_code):
        (lon1, lat1, lon2, lat2) = country.bbox
        diagonals.append(distance(lat1, lon1, lat2, lon2))
    if diagonals:
        # Divide by two to get radius, round to 1 km and convert to meters
        radius = max(diagonals) / 2.0 / 1000.0
        value = _radius_cache[country_code] = round(radius) * 1000.0

    return value
