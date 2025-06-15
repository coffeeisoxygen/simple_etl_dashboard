"""MIM3 Profile data models untuk foundational data structure."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class CircleType(Enum):
    """Circle categories untuk MIM3."""

    JABODETABEK = "jabodetabek"
    JAWA_BARAT = "jawa_barat"
    JAWA_TENGAH = "jawa_tengah"
    JAWA_TIMUR = "jabodetabek"
    SUMATRA = "sumatra"
    KALIMANTAN = "kalimantan"
    SULAWESI = "sulawesi"
    INDONESIA_TIMUR = "indonesia_timur"


class MIM3Profile(BaseModel):
    """MIM3 Profile - Master data untuk business unit."""

    # Basic Info
    mim3_id: str = Field(..., description="MIM3 ID (unique identifier)")
    mim3_name: str = Field(..., description="MIM3 Name")
    mim3_pic: str = Field(..., description="Person in Charge")
    mim3_contact: str = Field(..., description="Contact number")
    mim3_email: EmailStr = Field(..., description="Email address")

    # Territory Info
    personal_territory: str = Field(..., description="Personal Territory")
    micro_cluster: str = Field(..., description="Micro Cluster")
    region: str = Field(..., description="Region")
    circle: CircleType = Field(..., description="Circle")

    # Optional Info
    mim3_logo: str | None = Field(None, description="Logo URL/path")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("mim3_contact")
    @classmethod
    def validate_contact(cls, v: Any) -> str:
        """Validate contact number format."""
        # Remove spaces and non-numeric characters except +
        cleaned = "".join(c for c in str(v) if c.isdigit() or c == "+")
        if len(cleaned) < 10:
            raise ValueError("Contact number must be at least 10 digits")
        return cleaned


class DSEInfo(BaseModel):
    """DSE (Sales Man) information."""

    dse_id: str = Field(..., description="DSE ID")
    nama: str = Field(..., description="Nama DSE")
    contact: str = Field(..., description="Contact number")
    list_area: str = Field(..., description="Area coverage (comma separated)")
    mim3_id: str = Field(..., description="MIM3 ID reference")

    # Status & Metadata
    status: str = Field(default="active", description="Status DSE")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: Any) -> str:
        """Validate contact number format."""
        cleaned = "".join(c for c in str(v) if c.isdigit() or c == "+")
        if len(cleaned) < 10:
            raise ValueError("Contact number must be at least 10 digits")
        return cleaned


class TerritoryStats(BaseModel):
    """Territory statistics untuk MIM3."""

    mim3_id: str = Field(..., description="MIM3 ID reference")

    # Population & Geographic
    jumlah_kecamatan: int = Field(..., ge=0, description="Jumlah Kecamatan")
    jumlah_desa: int = Field(..., ge=0, description="Jumlah Desa")
    jumlah_populasi: int = Field(..., ge=0, description="Jumlah Populasi")

    # Infrastructure
    jumlah_site: int = Field(..., ge=0, description="Jumlah Site/Tower")
    jumlah_retailer: int = Field(..., ge=0, description="Jumlah Retailer")

    # Metadata
    periode: str = Field(..., description="Periode data (YYYY-MM)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class MIM3Summary(BaseModel):
    """MIM3 Summary - Consolidated view."""

    profile: MIM3Profile
    jumlah_dse: int = Field(default=0, description="Total DSE count")
    territory_stats: TerritoryStats | None = None

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}
