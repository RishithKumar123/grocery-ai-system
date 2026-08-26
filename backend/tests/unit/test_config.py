from app.core.config import settings


def test_config_loader():
    """Verifies that config environments load default application metadata correctly."""
    assert settings.APP_NAME is not None
    assert settings.DATABASE_URL is not None
    assert settings.CORS_ORIGINS is not None
