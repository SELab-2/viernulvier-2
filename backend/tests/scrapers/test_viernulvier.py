"""
Tests for Viernulvier API Scraper

Tests cover:
- API request handling
- Data transformation
- Error handling
- Session management
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests

from apps.imports.scrapers.viernulvier import (
    ViernulvierScraper,
    ViernulvierScraperError,
    ViernulvierAPIError,
    ViernulvierPersistenceError,
)


@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    return ViernulvierScraper()


@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    return {
        'events': [
            {
                'id': '123',
                'title': 'Test Event',
                'description': 'Test Description',
                'start_date': '2024-01-15T20:00:00Z',
                'end_date': '2024-01-15T23:00:00Z',
                'location': 'Test Location',
                'url': 'https://example.com/event',
                'price': 10.0,
                'category': 'music',
            }
        ]
    }


@pytest.fixture
def mock_raw_event():
    """Mock raw event data."""
    return {
        'id': '123',
        'title': 'Test Event',
        'description': 'Test Description',
        'start_date': '2024-01-15T20:00:00Z',
        'end_date': '2024-01-15T23:00:00Z',
        'location': 'Test Location',
        'url': 'https://example.com/event',
    }


class TestViernulvierScraperInit:
    """Test scraper initialization."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        scraper = ViernulvierScraper()
        assert scraper.api_key is None
        assert scraper.session is not None

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        api_key = 'test-key-123'
        scraper = ViernulvierScraper(api_key=api_key)
        assert scraper.api_key == api_key
        assert 'Authorization' in scraper.session.headers
        assert scraper.session.headers['Authorization'] == f'Token {api_key}'

    @patch('apps.imports.scrapers.viernulvier.settings')
    def test_init_with_settings_api_key(self, mock_settings):
        """Test initialization with API key from settings."""
        mock_settings.VIERNULVIER_API_KEY = 'settings-key'
        scraper = ViernulvierScraper()
        assert scraper.api_key == 'settings-key'


class TestMakeRequest:
    """Test _make_request method."""

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_successful_request(self, mock_get, scraper):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': 'test'}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = scraper._make_request('events')

        assert result == {'data': 'test'}
        mock_get.assert_called_once()

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_request_timeout(self, mock_get, scraper):
        """Test request timeout handling."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(ViernulvierAPIError, match='Request timeout'):
            scraper._make_request('events')

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_http_error(self, mock_get, scraper):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        with pytest.raises(ViernulvierAPIError, match='HTTP 404'):
            scraper._make_request('events')

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_invalid_json(self, mock_get, scraper):
        """Test invalid JSON response handling."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.side_effect = ValueError('Invalid JSON')
        mock_get.return_value = mock_response

        with pytest.raises(ViernulvierAPIError, match='Invalid JSON'):
            scraper._make_request('events')

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_request_exception(self, mock_get, scraper):
        """Test general request exception handling."""
        mock_get.side_effect = requests.exceptions.RequestException('Connection error')

        with pytest.raises(ViernulvierAPIError, match='API request failed'):
            scraper._make_request('events')

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_request_retries_then_success(self, mock_get, scraper):
        """Test retry logic on transient timeout."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': 'ok'}
        mock_response.raise_for_status = Mock()
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            mock_response,
        ]

        result = scraper._make_request('events')

        assert result == {'data': 'ok'}
        assert mock_get.call_count == 2

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_request_retries_exhausted(self, mock_get, scraper):
        """Test retry exhaustion on repeated timeouts."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(ViernulvierAPIError, match='Request timeout'):
            scraper._make_request('events')

        assert mock_get.call_count == scraper.MAX_RETRIES


class TestFetchEvents:
    """Test fetch_events method."""

    @patch.object(ViernulvierScraper, '_make_request')
    def test_fetch_events_success(self, mock_request, scraper, mock_api_response):
        """Test successful event fetching."""
        mock_request.return_value = mock_api_response

        events = scraper.fetch_events()

        assert len(events) == 1
        assert events[0]['id'] == '123'
        mock_request.assert_called_once_with('events', params={})

    @patch.object(ViernulvierScraper, '_make_request')
    def test_fetch_events_with_limit(self, mock_request, scraper, mock_api_response):
        """Test fetching events with limit parameter."""
        mock_request.return_value = mock_api_response

        events = scraper.fetch_events(limit=10)

        mock_request.assert_called_once_with('events', params={'limit': 10})

    @patch.object(ViernulvierScraper, '_make_request')
    def test_fetch_events_with_kwargs(self, mock_request, scraper, mock_api_response):
        """Test fetching events with additional parameters."""
        mock_request.return_value = mock_api_response

        events = scraper.fetch_events(category='music', date='2024-01-15')

        expected_params = {'category': 'music', 'date': '2024-01-15'}
        mock_request.assert_called_once_with('events', params=expected_params)

    @patch.object(ViernulvierScraper, '_make_request')
    def test_fetch_events_list_response(self, mock_request, scraper):
        """Test handling direct list response."""
        mock_request.return_value = [{'id': '1'}, {'id': '2'}]

        events = scraper.fetch_events()

        assert len(events) == 2

    @patch.object(ViernulvierScraper, '_make_request')
    def test_fetch_events_unexpected_format(self, mock_request, scraper):
        """Test handling unexpected response format."""
        mock_request.return_value = {'unexpected': 'format'}

        events = scraper.fetch_events()

        assert events == []

    @patch.object(ViernulvierScraper, '_make_request')
    def test_fetch_events_api_error(self, mock_request, scraper):
        """Test error propagation from API."""
        mock_request.side_effect = ViernulvierAPIError('API Error')

        with pytest.raises(ViernulvierAPIError):
            scraper.fetch_events()


class TestTransformEvent:
    """Test transform_event method."""

    def test_transform_event_success(self, scraper, mock_raw_event):
        """Test successful event transformation."""
        result = scraper.transform_event(mock_raw_event)

        assert result['external_id'] == '123'
        assert result['title'] == 'Test Event'
        assert result['description'] == 'Test Description'
        assert result['location'] == 'Test Location'
        assert result['url'] == 'https://example.com/event'
        assert result['source'] == 'viernulvier'
        assert isinstance(result['start_date'], datetime)
        assert isinstance(result['end_date'], datetime)
        assert result['raw_data'] == mock_raw_event

    def test_transform_event_with_optional_fields(self, scraper):
        """Test transformation with optional fields."""
        raw_event = {
            'id': '123',
            'title': 'Test',
            'description': 'Desc',
            'start_date': '2024-01-15T20:00:00Z',
            'price': 15.5,
            'category': 'art',
            'image_url': 'https://example.com/image.jpg',
        }

        result = scraper.transform_event(raw_event)

        assert result['price'] == 15.5
        assert result['category'] == 'art'
        assert result['image_url'] == 'https://example.com/image.jpg'

    def test_transform_event_strips_whitespace(self, scraper):
        """Test that transformation strips whitespace."""
        raw_event = {
            'id': '123',
            'title': '  Test Event  ',
            'description': '  Test Description  ',
            'location': '  Test Location  ',
            'start_date': '2024-01-15T20:00:00Z',
        }

        result = scraper.transform_event(raw_event)

        assert result['title'] == 'Test Event'
        assert result['description'] == 'Test Description'
        assert result['location'] == 'Test Location'

    def test_transform_event_missing_fields(self, scraper):
        """Test transformation with missing fields."""
        raw_event = {'id': '123'}

        result = scraper.transform_event(raw_event)

        assert result['title'] == ''
        assert result['description'] == ''
        assert result['location'] == ''
        assert result['start_date'] is None

    def test_transform_event_error(self, scraper):
        """Test transformation error handling."""
        invalid_event = None

        with pytest.raises(ViernulvierScraperError, match='Failed to transform event'):
            scraper.transform_event(invalid_event)


class TestParseDatetime:
    """Test _parse_datetime method."""

    def test_parse_valid_datetime_with_z(self, scraper):
        """Test parsing ISO datetime with Z timezone."""
        result = scraper._parse_datetime('2024-01-15T20:00:00Z')

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 20

    def test_parse_valid_datetime_with_offset(self, scraper):
        """Test parsing ISO datetime with timezone offset."""
        result = scraper._parse_datetime('2024-01-15T20:00:00+01:00')

        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_none(self, scraper):
        """Test parsing None value."""
        result = scraper._parse_datetime(None)
        assert result is None

    def test_parse_empty_string(self, scraper):
        """Test parsing empty string."""
        result = scraper._parse_datetime('')
        assert result is None

    def test_parse_invalid_format(self, scraper):
        """Test parsing invalid datetime format."""
        result = scraper._parse_datetime('invalid-date')
        assert result is None


class TestFetchAndTransformEvents:
    """Test fetch_and_transform_events method."""

    @patch.object(ViernulvierScraper, 'fetch_events')
    @patch.object(ViernulvierScraper, 'transform_event')
    def test_fetch_and_transform_success(self, mock_transform, mock_fetch, scraper, mock_raw_event):
        """Test successful fetch and transform."""
        mock_fetch.return_value = [mock_raw_event]
        mock_transform.return_value = {'external_id': '123', 'title': 'Test'}

        result = scraper.fetch_and_transform_events()

        assert len(result) == 1
        assert result[0]['external_id'] == '123'
        mock_fetch.assert_called_once_with(limit=None)
        mock_transform.assert_called_once_with(mock_raw_event)

    @patch.object(ViernulvierScraper, 'fetch_events')
    @patch.object(ViernulvierScraper, 'transform_event')
    def test_fetch_and_transform_with_limit(self, mock_transform, mock_fetch, scraper):
        """Test fetch and transform with limit."""
        mock_fetch.return_value = []

        scraper.fetch_and_transform_events(limit=50)

        mock_fetch.assert_called_once_with(limit=50)

    @patch.object(ViernulvierScraper, 'fetch_events')
    @patch.object(ViernulvierScraper, 'transform_event')
    def test_fetch_and_transform_partial_failure(self, mock_transform, mock_fetch, scraper):
        """Test fetch and transform with some transformation failures."""
        mock_fetch.return_value = [
            {'id': '1'},
            {'id': '2'},
            {'id': '3'},
        ]
        mock_transform.side_effect = [
            {'external_id': '1'},
            ViernulvierScraperError('Transform failed'),
            {'external_id': '3'},
        ]

        result = scraper.fetch_and_transform_events()

        assert len(result) == 2
        assert result[0]['external_id'] == '1'
        assert result[1]['external_id'] == '3'

    @patch.object(ViernulvierScraper, 'fetch_events')
    @patch.object(ViernulvierScraper, 'transform_event')
    def test_fetch_and_transform_kwargs(self, mock_transform, mock_fetch, scraper):
        """Test fetch and transform with additional kwargs."""
        mock_fetch.return_value = []

        scraper.fetch_and_transform_events(category='music', limit=10)

        mock_fetch.assert_called_once_with(limit=10, category='music')


class TestPersistEvents:
    """Test persist_events method."""

    def test_persist_events_success(self, scraper):
        saved = []

        def saver(event):
            saved.append(event)

        events = [{'external_id': '1'}, {'external_id': '2'}]
        result = scraper.persist_events(events, saver=saver)

        assert result == 2
        assert len(saved) == 2

    def test_persist_events_partial_failure(self, scraper):
        calls = []

        def saver(event):
            calls.append(event['external_id'])
            if event['external_id'] == '2':
                raise ValueError("fail")

        events = [{'external_id': '1'}, {'external_id': '2'}, {'external_id': '3'}]
        result = scraper.persist_events(events, saver=saver)

        assert result == 2
        assert calls == ['1', '2', '3']

    def test_persist_events_invalid_saver(self, scraper):
        with pytest.raises(ViernulvierPersistenceError):
            scraper.persist_events([], saver=None)


class TestFetchTransformPersist:
    """Test fetch_transform_and_persist method."""

    @patch.object(ViernulvierScraper, 'fetch_and_transform_events')
    def test_fetch_transform_and_persist_success(self, mock_fetch, scraper):
        mock_fetch.return_value = [{'external_id': '1'}, {'external_id': '2'}]
        saved = []

        def saver(event):
            saved.append(event)

        result = scraper.fetch_transform_and_persist(saver=saver)

        assert result == 2
        assert len(saved) == 2

    def test_fetch_transform_and_persist_missing_saver(self, scraper):
        with pytest.raises(ViernulvierPersistenceError):
            scraper.fetch_transform_and_persist()


class TestContextManager:
    """Test context manager functionality."""

    @patch('apps.imports.scrapers.viernulvier.requests.Session.close')
    def test_context_manager_enter_exit(self, mock_close):
        """Test context manager properly closes session."""
        with ViernulvierScraper() as scraper:
            assert scraper.session is not None

        # Session's close method should be called after exiting context
        mock_close.assert_called_once()

    @patch('apps.imports.scrapers.viernulvier.requests.Session.close')
    def test_close_method(self, mock_close, scraper):
        """Test close method."""
        scraper.close()

        # Verify close was called
        mock_close.assert_called_once()


class TestIntegration:
    """Integration tests with mocked responses."""

    @patch('apps.imports.scrapers.viernulvier.requests.Session.get')
    def test_full_scraper_workflow(self, mock_get):
        """Test complete scraper workflow from fetch to transform."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'events': [
                {
                    'id': '1',
                    'title': 'Event 1',
                    'description': 'Description 1',
                    'start_date': '2024-01-15T20:00:00Z',
                    'end_date': '2024-01-15T23:00:00Z',
                    'location': 'Location 1',
                    'url': 'https://example.com/1',
                },
                {
                    'id': '2',
                    'title': 'Event 2',
                    'description': 'Description 2',
                    'start_date': '2024-01-16T20:00:00Z',
                    'location': 'Location 2',
                    'url': 'https://example.com/2',
                },
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with ViernulvierScraper() as scraper:
            events = scraper.fetch_and_transform_events()

        assert len(events) == 2
        assert events[0]['external_id'] == '1'
        assert events[0]['title'] == 'Event 1'
        assert events[1]['external_id'] == '2'
        assert events[1]['title'] == 'Event 2'
