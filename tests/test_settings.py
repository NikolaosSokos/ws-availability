import os
import pytest
from apps.settings import Settings

class TestSettings:
    def test_default_settings(self):
        settings = Settings()
        assert settings.runmode == "test"
        assert settings.mongodb_host == "localhost"
        assert settings.cache_host == "localhost"

    def test_production_defaults(self):
        os.environ["RUNMODE"] = "production"
        # Clear other related env vars to ensure we test the default fallback logic
        if "MONGODB_HOST" in os.environ: del os.environ["MONGODB_HOST"]
        if "CACHE_HOST" in os.environ: del os.environ["CACHE_HOST"]
        
        settings = Settings()
        assert settings.runmode == "production"
        assert settings.mongodb_host == "host.docker.internal"
        assert settings.cache_host == "cache"
        
        del os.environ["RUNMODE"]

    def test_env_override(self):
        os.environ["RUNMODE"] = "production"
        os.environ["MONGODB_HOST"] = "my-mongo"
        
        settings = Settings()
        assert settings.runmode == "production"
        assert settings.mongodb_host == "my-mongo"
        
        del os.environ["RUNMODE"]
        del os.environ["MONGODB_HOST"]

    def test_auth_source_default(self):
        """Test that mongodb_auth_source defaults to mongodb_name"""
        # Clear env vars to avoid interference
        if "MONGODB_NAME" in os.environ: del os.environ["MONGODB_NAME"]
        if "MONGODB_AUTH_SOURCE" in os.environ: del os.environ["MONGODB_AUTH_SOURCE"]
        
        settings = Settings(MONGODB_NAME="custom_db", MONGODB_AUTH_SOURCE=None)
        assert settings.mongodb_name == "custom_db"
        assert settings.mongodb_auth_source == "custom_db"

    def test_auth_source_empty(self):
        """Test that mongodb_auth_source defaults even if set to empty string"""
        settings = Settings(MONGODB_NAME="custom_db", MONGODB_AUTH_SOURCE="")
        assert settings.mongodb_name == "custom_db"
        assert settings.mongodb_auth_source == "custom_db"

    def test_auth_source_missing(self):
        """Test that mongodb_auth_source defaults even if key is missing from constructor"""
        settings = Settings(MONGODB_NAME="custom_db")
        # Since it's not in os.environ or constructor, it will be None then fallback
        assert settings.mongodb_name == "custom_db"
        assert settings.mongodb_auth_source == "custom_db"

    def test_auth_source_override(self):
        """Test that mongodb_auth_source can be explicitly set"""
        # Clear env vars to avoid interference
        if "MONGODB_NAME" in os.environ: del os.environ["MONGODB_NAME"]
        
        os.environ["MONGODB_AUTH_SOURCE"] = "admin"
        settings = Settings(MONGODB_NAME="wfrepo")
        assert settings.mongodb_name == "wfrepo"
        assert settings.mongodb_auth_source == "admin"
        del os.environ["MONGODB_AUTH_SOURCE"]
