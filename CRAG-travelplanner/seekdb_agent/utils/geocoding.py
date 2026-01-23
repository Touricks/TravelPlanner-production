"""
Google Places Geocoding Utility
================================
Enrich POIs with latitude/longitude using Google Places API

Use Cases:
- Fallback POIs from Gemini (no coordinates in LLM response)
- POIs with missing or invalid coordinates
- Coordinate validation before Java export

API Used:
- Google Places Text Search API (finds place by name + location context)
- Returns geometry.location with lat/lng

Cost: ~$32 per 1,000 Text Search requests
"""

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Google Places API Configuration
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1/places:searchText"

# Request timeout
GEOCODING_TIMEOUT = 10.0

# Rate limiting: max concurrent requests
MAX_CONCURRENT_REQUESTS = 5


class GeocodingError(Exception):
    """Exception raised when geocoding fails"""

    pass


async def geocode_place(
    place_name: str,
    city: str | None = None,
    state: str | None = None,
    country: str = "USA",
) -> dict[str, float] | None:
    """
    Get coordinates for a place using Google Places Text Search API

    Args:
        place_name: Name of the place (e.g., "Empire State Building")
        city: City name for context (e.g., "New York")
        state: State name for context (e.g., "NY")
        country: Country for context (default: "USA")

    Returns:
        Dict with 'latitude' and 'longitude' keys, or None if not found

    Example:
        >>> coords = await geocode_place("Central Park", city="New York")
        >>> print(coords)
        {'latitude': 40.7828, 'longitude': -73.9654}
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.warning("[Geocoding] GOOGLE_PLACES_API_KEY not configured")
        return None

    # Build search query with location context
    query_parts = [place_name]
    if city:
        query_parts.append(city)
    if state:
        query_parts.append(state)
    query_parts.append(country)

    text_query = ", ".join(query_parts)

    logger.debug(f"[Geocoding] Searching for: {text_query}")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.location,places.displayName,places.formattedAddress",
    }

    payload = {
        "textQuery": text_query,
        "maxResultCount": 1,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_PLACES_BASE_URL,
                json=payload,
                headers=headers,
                timeout=GEOCODING_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            places = data.get("places", [])
            if not places:
                logger.warning(f"[Geocoding] No results for: {text_query}")
                return None

            location = places[0].get("location", {})
            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is not None and longitude is not None:
                logger.info(
                    f"[Geocoding] Found coordinates for '{place_name}': "
                    f"lat={latitude}, lng={longitude}"
                )
                return {"latitude": latitude, "longitude": longitude}

            logger.warning(f"[Geocoding] No location data in response for: {text_query}")
            return None

    except httpx.HTTPStatusError as e:
        logger.error(f"[Geocoding] HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"[Geocoding] Request error: {e}")
        return None
    except Exception as e:
        logger.error(f"[Geocoding] Unexpected error: {e}")
        return None


async def enrich_poi_with_coordinates(
    poi: dict[str, Any],
    destination: str | None = None,
) -> dict[str, Any]:
    """
    Enrich a single POI with coordinates if missing

    Args:
        poi: POI dictionary (must have 'name' field)
        destination: Fallback city/destination if poi doesn't have city

    Returns:
        POI dictionary with latitude/longitude filled in (if found)
    """
    # Check if coordinates already exist and are valid
    lat = poi.get("latitude")
    lng = poi.get("longitude")

    if lat is not None and lng is not None:
        # Validate coordinates are not default/invalid values
        if lat != 0.0 or lng != 0.0:
            logger.debug(f"[Geocoding] POI '{poi.get('name')}' already has valid coordinates")
            return poi

    # Need to geocode
    place_name = poi.get("name")
    if not place_name:
        logger.warning("[Geocoding] POI has no name, cannot geocode")
        return poi

    city = poi.get("city") or destination
    state = poi.get("state")

    coords = await geocode_place(place_name, city=city, state=state)

    if coords:
        poi["latitude"] = coords["latitude"]
        poi["longitude"] = coords["longitude"]
        logger.info(f"[Geocoding] Enriched POI '{place_name}' with coordinates")
    else:
        logger.warning(f"[Geocoding] Could not find coordinates for POI '{place_name}'")

    return poi


async def enrich_pois_with_coordinates(
    pois: list[dict[str, Any]],
    destination: str | None = None,
) -> list[dict[str, Any]]:
    """
    Enrich multiple POIs with coordinates (with rate limiting)

    Args:
        pois: List of POI dictionaries
        destination: Default destination for geocoding context

    Returns:
        List of POIs with coordinates filled in where possible

    Note:
        Uses semaphore to limit concurrent API requests
    """
    if not pois:
        return pois

    if not GOOGLE_PLACES_API_KEY:
        logger.warning("[Geocoding] GOOGLE_PLACES_API_KEY not configured, skipping enrichment")
        return pois

    # Count POIs needing geocoding
    pois_needing_coords = [
        p
        for p in pois
        if p.get("latitude") is None
        or p.get("longitude") is None
        or (p.get("latitude") == 0.0 and p.get("longitude") == 0.0)
    ]

    if not pois_needing_coords:
        logger.info("[Geocoding] All POIs already have valid coordinates")
        return pois

    logger.info(
        f"[Geocoding] Enriching {len(pois_needing_coords)}/{len(pois)} POIs with coordinates"
    )

    # Use semaphore for rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def enrich_with_limit(poi: dict[str, Any]) -> dict[str, Any]:
        async with semaphore:
            return await enrich_poi_with_coordinates(poi, destination)

    # Process all POIs (those with coords will be returned unchanged)
    tasks = [enrich_with_limit(poi) for poi in pois]
    enriched_pois = await asyncio.gather(*tasks)

    # Log summary
    enriched_count = sum(
        1 for p in enriched_pois if p.get("latitude") is not None and p.get("longitude") is not None
    )
    logger.info(
        f"[Geocoding] Enrichment complete: {enriched_count}/{len(pois)} POIs have coordinates"
    )

    return list(enriched_pois)


def enrich_pois_sync(
    pois: list[dict[str, Any]],
    destination: str | None = None,
) -> list[dict[str, Any]]:
    """
    Synchronous wrapper for enrich_pois_with_coordinates

    Use this when calling from synchronous code (e.g., middleware)

    Args:
        pois: List of POI dictionaries
        destination: Default destination for geocoding context

    Returns:
        List of POIs with coordinates filled in where possible
    """
    try:
        # Always use asyncio.run() which creates a new event loop
        # This works correctly in any context (main thread, thread pool, etc.)
        return asyncio.run(enrich_pois_with_coordinates(pois, destination))
    except RuntimeError as e:
        # Handle case where asyncio.run() cannot be called
        # (e.g., already in an async context in the main thread)
        if "cannot be called from a running event loop" in str(e):
            logger.warning("[Geocoding] Already in async context, using nest_asyncio fallback")
            try:
                import nest_asyncio

                nest_asyncio.apply()
                return asyncio.run(enrich_pois_with_coordinates(pois, destination))
            except ImportError:
                logger.warning("[Geocoding] nest_asyncio not available, skipping enrichment")
                return pois
        else:
            logger.error(f"[Geocoding] Sync wrapper error: {e}")
            return pois
    except Exception as e:
        logger.error(f"[Geocoding] Sync wrapper error: {e}")
        return pois


# ===== POI Search Functions (for supplementing missing POIs) =====


async def search_poi_by_name(
    poi_name: str,
    destination: str,
) -> dict[str, Any] | None:
    """
    Search for a POI using Google Places Text Search API.
    Returns full POI data (name, coordinates, address, rating, etc.)

    Args:
        poi_name: Name of the POI to search for
        destination: City/destination for context

    Returns:
        POI dict in CRAG format, or None if not found

    Example:
        >>> poi = await search_poi_by_name("Golden Gate Bridge", "San Francisco")
        >>> print(poi["name"], poi["latitude"])
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.warning("[POISearch] GOOGLE_PLACES_API_KEY not configured")
        return None

    # Build search query
    text_query = f"{poi_name}, {destination}"

    logger.info(f"[POISearch] Searching for: {text_query}")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.location,places.rating,places.userRatingCount,"
            "places.priceLevel,places.primaryType,places.editorialSummary,"
            "places.photos"
        ),
    }

    payload = {
        "textQuery": text_query,
        "maxResultCount": 1,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_PLACES_BASE_URL,
                json=payload,
                headers=headers,
                timeout=GEOCODING_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()

            places = data.get("places", [])
            if not places:
                logger.warning(f"[POISearch] No results for: {text_query}")
                return None

            place = places[0]
            location = place.get("location", {})
            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is None or longitude is None:
                logger.warning(f"[POISearch] No coordinates for: {poi_name}")
                return None

            # Extract display name
            display_name = place.get("displayName", {})
            name = display_name.get("text", poi_name)

            # Map Google price level to numeric
            price_level_map = {
                "PRICE_LEVEL_FREE": 0,
                "PRICE_LEVEL_INEXPENSIVE": 1,
                "PRICE_LEVEL_MODERATE": 2,
                "PRICE_LEVEL_EXPENSIVE": 3,
                "PRICE_LEVEL_VERY_EXPENSIVE": 4,
            }
            google_price = place.get("priceLevel")
            price_level = price_level_map.get(google_price)

            # Build POI in CRAG format
            poi = {
                "id": f"google_{place.get('id', poi_name.replace(' ', '_').lower())}",
                "name": name,
                "city": destination,
                "state": None,
                "latitude": latitude,
                "longitude": longitude,
                "rating": place.get("rating"),
                "reviews_count": place.get("userRatingCount"),
                "price_level": price_level,
                "primary_category": place.get("primaryType", "attraction"),
                "editorial_summary": (
                    place.get("editorialSummary", {}).get("text", "")
                    if place.get("editorialSummary")
                    else ""
                ),
                "address": place.get("formattedAddress", destination),
                "image_url": None,  # Would require additional API call for photos
                "opening_hours": None,
                "score": 0.75,  # Google supplemented POIs get slightly lower score
                "source": "google_places",  # Mark as supplemented
            }

            logger.info(f"[POISearch] Found POI '{name}' at ({latitude:.4f}, {longitude:.4f})")
            return poi

    except httpx.HTTPStatusError as e:
        logger.error(f"[POISearch] HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"[POISearch] Request error: {e}")
        return None
    except Exception as e:
        logger.error(f"[POISearch] Unexpected error: {e}")
        return None


async def search_pois_by_names(
    poi_names: list[str],
    destination: str,
) -> list[dict[str, Any]]:
    """
    Search for multiple POIs using Google Places API (with rate limiting).

    Args:
        poi_names: List of POI names to search for
        destination: City/destination for context

    Returns:
        List of found POIs (excludes None results)
    """
    if not poi_names:
        return []

    if not GOOGLE_PLACES_API_KEY:
        logger.warning("[POISearch] GOOGLE_PLACES_API_KEY not configured, skipping search")
        return []

    logger.info(f"[POISearch] Searching for {len(poi_names)} POIs in {destination}")

    # Use semaphore for rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def search_with_limit(name: str) -> dict[str, Any] | None:
        async with semaphore:
            return await search_poi_by_name(name, destination)

    # Search all POIs concurrently
    tasks = [search_with_limit(name) for name in poi_names]
    results = await asyncio.gather(*tasks)

    # Filter out None results
    found_pois = [poi for poi in results if poi is not None]

    logger.info(f"[POISearch] Found {len(found_pois)}/{len(poi_names)} POIs")
    return found_pois


def search_pois_sync(
    poi_names: list[str],
    destination: str,
) -> list[dict[str, Any]]:
    """
    Synchronous wrapper for search_pois_by_names.

    Use this when calling from synchronous code (e.g., generator node).

    Args:
        poi_names: List of POI names to search for
        destination: City/destination for context

    Returns:
        List of found POIs in CRAG format
    """
    if not poi_names:
        return []

    try:
        return asyncio.run(search_pois_by_names(poi_names, destination))
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            logger.warning("[POISearch] Already in async context, using nest_asyncio fallback")
            try:
                import nest_asyncio

                nest_asyncio.apply()
                return asyncio.run(search_pois_by_names(poi_names, destination))
            except ImportError:
                logger.warning("[POISearch] nest_asyncio not available, skipping search")
                return []
        else:
            logger.error(f"[POISearch] Sync wrapper error: {e}")
            return []
    except Exception as e:
        logger.error(f"[POISearch] Sync wrapper error: {e}")
        return []
