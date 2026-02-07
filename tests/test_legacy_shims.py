from fastapi_zero import database, models, scraper, settings


def test_scraper_shim_exports():
    assert "Scraper" in scraper.__all__
    assert scraper.Scraper is not None
    assert "PRICE_PATTERNS" in scraper.__all__


def test_models_shim_exports():
    assert "Product" in models.__all__
    assert models.Product is not None
    assert "table_registry" in models.__all__


def test_database_shim_exports():
    assert "engine" in database.__all__
    assert database.engine is not None
    assert "get_session" in database.__all__


def test_settings_shim_exports():
    assert "Settings" in settings.__all__
    assert settings.Settings is not None
