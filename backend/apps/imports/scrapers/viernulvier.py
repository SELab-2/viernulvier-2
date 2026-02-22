import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ViernulvierScraperError(Exception):
    """Base exception for Viernulvier scraper errors."""
    pass


class ViernulvierAPIError(ViernulvierScraperError):
    """Raised when the Viernulvier API returns an error."""
    pass


class ViernulvierPersistenceError(ViernulvierScraperError):
    """Raised when persisting data fails or is misconfigured."""
    pass


class ViernulvierScraper:
    """
    Scraper for fetching and transforming data from the Viernulvier API.

    This centralized scraper handles:
    - Fetching data from external Viernulvier API
    - Transforming API responses to internal data structures
    - Error handling and logging
    - Session management
    """

    BASE_URL = getattr(settings, 'VIERNULVIER_API_URL', 'https://viernulvier.gent/api')
    TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_BACKOFF_SECONDS = 1.0

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the scraper with optional API key."""
        self.api_key = api_key or getattr(settings, 'VIERNULVIER_API_KEY', None)
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({'Authorization': f'Token {self.api_key}'})

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a GET request to the Viernulvier API."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching data from: {url}")
                response = self.session.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout for {url} (attempt {attempt}/{self.MAX_RETRIES})")
                if attempt == self.MAX_RETRIES:
                    logger.error(f"Timeout for {url}")
                    raise ViernulvierAPIError(f"Request timeout for {url}")
                time.sleep(self.RETRY_BACKOFF_SECONDS * attempt)
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e.response.status_code}")
                raise ViernulvierAPIError(f"HTTP {e.response.status_code}: {str(e)}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error: {str(e)} (attempt {attempt}/{self.MAX_RETRIES})")
                if attempt == self.MAX_RETRIES:
                    logger.error(f"Request error: {str(e)}")
                    raise ViernulvierAPIError(f"API request failed: {str(e)}")
                time.sleep(self.RETRY_BACKOFF_SECONDS * attempt)
            except ValueError as e:
                logger.error(f"Invalid JSON: {str(e)}")
                raise ViernulvierAPIError(f"Invalid JSON response: {str(e)}")

    def fetch_events(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Fetch events from the Viernulvier API."""
        params = kwargs.copy()
        if limit:
            params['limit'] = limit

        try:
            data = self._make_request('events', params=params)
            events = data.get('events', []) if isinstance(data, dict) else data

            if not isinstance(events, list):
                events = []

            logger.info(f"Fetched {len(events)} events")
            return events
        except ViernulvierAPIError:
            logger.error("Failed to fetch events")
            raise

    def transform_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw API event to internal data structure."""
        try:
            transformed = {
                'external_id': str(raw_event.get('id', '')),
                'title': raw_event.get('title', '').strip(),
                'description': raw_event.get('description', '').strip(),
                'start_date': self._parse_datetime(raw_event.get('start_date')),
                'end_date': self._parse_datetime(raw_event.get('end_date')),
                'location': raw_event.get('location', '').strip(),
                'url': raw_event.get('url', ''),
                'source': 'viernulvier',
                'raw_data': raw_event,
            }

            if 'price' in raw_event:
                transformed['price'] = raw_event['price']
            if 'category' in raw_event:
                transformed['category'] = raw_event['category']
            if 'image_url' in raw_event:
                transformed['image_url'] = raw_event['image_url']

            return transformed
        except Exception as e:
            event_id = raw_event.get('id', 'unknown') if isinstance(raw_event, dict) else 'unknown'
            logger.warning(f"Error transforming event {event_id}: {str(e)}")
            raise ViernulvierScraperError(f"Failed to transform event: {str(e)}")

    def _parse_datetime(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from API."""
        if not date_string:
            return None
        try:
            clean_date = date_string.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_date)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse datetime '{date_string}': {str(e)}")
            return None

    def fetch_and_transform_events(self, limit: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """Fetch and transform events in one call."""
        raw_events = self.fetch_events(limit=limit, **kwargs)
        transformed_events = []
        error_count = 0

        for raw_event in raw_events:
            try:
                transformed = self.transform_event(raw_event)
                transformed_events.append(transformed)
            except ViernulvierScraperError:
                error_count += 1
                continue

        if error_count > 0:
            logger.warning(f"Failed to transform {error_count} events")

        logger.info(f"Transformed {len(transformed_events)}/{len(raw_events)} events")
        return transformed_events

    def persist_events(self, events: List[Dict[str, Any]], saver) -> int:
        """Persist transformed events using the provided saver callable."""
        if not callable(saver):
            raise ViernulvierPersistenceError("No valid saver callable provided")

        saved_count = 0
        error_count = 0

        for event in events:
            try:
                saver(event)
                saved_count += 1
            except Exception as e:
                error_count += 1
                logger.warning(f"Failed to persist event {event.get('external_id', 'unknown')}: {str(e)}")

        if error_count > 0:
            logger.warning(f"Failed to persist {error_count} events")

        logger.info(f"Persisted {saved_count}/{len(events)} events")
        return saved_count

    def fetch_transform_and_persist(self, limit: Optional[int] = None, saver=None, **kwargs) -> int:
        """Fetch, transform, and persist events in one call."""
        if saver is None:
            raise ViernulvierPersistenceError("Saver callable is required")

        transformed_events = self.fetch_and_transform_events(limit=limit, **kwargs)
        return self.persist_events(transformed_events, saver=saver)

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

