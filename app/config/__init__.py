"""Typed, validated application config (TCORE-114).

All settings are declared on `Settings` (pydantic-settings), so a missing required
variable fails fast at startup with a clear error instead of surfacing as an obscure
runtime failure. The module-level names below are kept as thin re-exports of
`settings.*` so existing `from app.config import X` imports keep working unchanged.

`load_dotenv()` still runs first, so anything reading `os.environ` directly (outside
this module) keeps seeing the same values it did before.
"""
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    # --- environment ---
    APP_ENV: str = "development"

    # --- required: the app cannot boot without these ---
    DATABASE_URL: str            # SQLAlchemy engine is built from it at import
    FERNET_KEY: str              # Fernet(FERNET_KEY) is built at import

    # --- auth / crypto ---
    PRIVATE_SECRET: Optional[str] = None
    ALGORITHM: Optional[str] = None

    # --- Azure ---
    AZURE_URL: Optional[str] = None
    AZURE_API_KEY: Optional[str] = None
    AZURE_DEFAULT_VOICE: Optional[str] = None

    # --- default voices ---
    AWS_DEFAULT_VOICE: Optional[str] = None
    GCP_DEFAULT_VOICE: Optional[str] = None

    # --- AWS (env var names differ from the Python names used across the app) ---
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, validation_alias="AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, validation_alias="AWS_SECRET_KEY")
    AWS_S3_BUCKET: Optional[str] = Field(default=None, validation_alias="AWS_BUCKET")
    AWS_REGION: Optional[str] = Field(default=None, validation_alias="AWS_BUCKET_REGION")

    # --- misc ---
    ID: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    SPELLCAST_VOICES_CACHE_TTL_SECONDS: Optional[str] = None
    ALLOWED_ORIGINS_DEV: str = "[]"

    @model_validator(mode="after")
    def _guard_env_matches_bucket(self):
        # Cheap protection against the worst cross-env mistake: a development run
        # writing to the production bucket (or vice versa). Buckets follow the
        # `<name>` / `<name>-dev` convention, so APP_ENV and the bucket must agree.
        # (The DB is not guarded here — Supabase refs aren't suffixed predictably;
        # prod/dev already live in separate projects.)
        bucket = self.AWS_S3_BUCKET or ""
        if not bucket:
            return self
        is_dev_bucket = bucket.endswith("-dev")
        if self.APP_ENV == "production" and is_dev_bucket:
            raise ValueError(
                f"APP_ENV=production but AWS_BUCKET='{bucket}' looks like a dev bucket"
            )
        if self.APP_ENV != "production" and not is_dev_bucket:
            raise ValueError(
                f"APP_ENV={self.APP_ENV} but AWS_BUCKET='{bucket}' is not a *-dev bucket "
                f"(a dev run must not touch production storage)"
            )
        return self


settings = Settings()  # raises at import if a required var is missing or the guard trips

# --- backward-compatible module-level names (do not remove: imported across the app) ---
DATABASE_URL = settings.DATABASE_URL
PRIVATE_SECRET = settings.PRIVATE_SECRET
ALGORITHM = settings.ALGORITHM
FERNET_KEY = settings.FERNET_KEY
AZURE_URL = settings.AZURE_URL
AZURE_API_KEY = settings.AZURE_API_KEY
APP_ENV = settings.APP_ENV
ID = settings.ID
AZURE_DEFAULT_VOICE = settings.AZURE_DEFAULT_VOICE
AWS_DEFAULT_VOICE = settings.AWS_DEFAULT_VOICE
GCP_DEFAULT_VOICE = settings.GCP_DEFAULT_VOICE
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_S3_BUCKET = settings.AWS_S3_BUCKET
AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_REGION = settings.AWS_REGION
REDIS_PASSWORD = settings.REDIS_PASSWORD
SPELLCAST_VOICES_CACHE_TTL_SECONDS = settings.SPELLCAST_VOICES_CACHE_TTL_SECONDS
ALLOWED_ORIGINS_DEV = settings.ALLOWED_ORIGINS_DEV
