"""Integration tests for scraping endpoints."""

# ruff: noqa: PLR2004


def test_crawl_search_with_query(client):
    """Test crawl_search endpoint with query parameter."""
    payload = {
        'search_url': 'https://example.com/search?q=gabinete',
        'query': 'gabinete',
        'max_pages': 1,
        'max_urls': 10,
    }
    response = client.post('/crawl/search', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'total_urls' in data
    assert 'urls' in data
    assert isinstance(data['total_urls'], int)
    assert isinstance(data['urls'], list)


def test_crawl_search_without_query(client):
    """Test crawl_search endpoint without query parameter."""
    payload = {
        'search_url': 'https://example.com/search?q=gabinete',
        'max_pages': 1,
        'max_urls': 10,
    }
    response = client.post('/crawl/search', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'total_urls' in data
    assert 'urls' in data
    assert isinstance(data['total_urls'], int)
    assert isinstance(data['urls'], list)


def test_crawl_search_with_concurrency(client):
    """Test crawl_search with custom max_concurrency."""
    payload = {
        'search_url': 'https://example.com/search?q=gabinete',
        'query': 'gabinete',
        'max_pages': 1,
        'max_urls': 10,
        'max_concurrency': 3,
    }
    response = client.post('/crawl/search', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'total_urls' in data
    assert 'urls' in data


def test_crawl_search_with_patterns(client):
    """Test crawl_search with include/exclude patterns."""
    payload = {
        'search_url': 'https://example.com/search?q=gabinete',
        'query': 'gabinete',
        'max_pages': 1,
        'max_urls': 10,
        'include_patterns': ['/produto/'],
        'exclude_patterns': ['/descontinuado/'],
    }
    response = client.post('/crawl/search', json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 'total_urls' in data
    assert 'urls' in data


def test_crawl_search_preserves_url_format(client):
    """Test that crawl_search returns URLs as strings or HttpUrl format."""
    payload = {
        'search_url': 'https://example.com/search?q=monitor',
        'query': 'monitor',
        'max_pages': 1,
        'max_urls': 5,
    }
    response = client.post('/crawl/search', json=payload)
    assert response.status_code == 200
    data = response.json()
    urls = data['urls']
    if urls:
        # Each URL should be a valid URL string
        for url in urls:
            assert isinstance(url, str)
            assert url.startswith('http')
