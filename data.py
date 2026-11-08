"""Download, cache, and prepare country data for Around the Globe Quiz."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
COUNTRIES_URL = "https://raw.githubusercontent.com/mledoze/countries/master/countries.json"
WORLD_BANK_URL = "https://api.worldbank.org/v2/country/all/indicator/{indicator}"
INDICATORS = {
    "population": "SP.POP.TOTL",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
}


def _download_json(url: str, params: dict[str, Any] | None = None) -> Any:
    """Request JSON from a public endpoint and raise a useful error on failure."""
    response = requests.get(url, params=params, timeout=25)
    response.raise_for_status()
    return response.json()


def load_raw_countries(refresh: bool = False) -> list[dict[str, Any]]:
    """Load the countries dataset, using a local cache when possible.

    Parameters
    ----------
    refresh : bool
        If True, try to download a fresh copy instead of using the cache.

    Returns
    -------
    list[dict]
        Raw country records from the mledoze/countries dataset.
    """
    DATA_DIR.mkdir(exist_ok=True)
    cache_file = DATA_DIR / "countries_cache.json"
    if cache_file.exists() and not refresh:
        with cache_file.open(encoding="utf-8") as file:
            return json.load(file)

    records = _download_json(COUNTRIES_URL)
    with cache_file.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False)
    return records


def load_world_bank_indicator(indicator: str) -> pd.DataFrame:
    """Download the latest available World Bank value for each country.

    Returns a two-column dataframe containing ISO-3 code and indicator value.
    Missing or unavailable API data is represented by an empty dataframe.
    """
    url = WORLD_BANK_URL.format(indicator=indicator)
    try:
        payload = _download_json(url, params={"format": "json", "per_page": 20000})
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            return pd.DataFrame(columns=["cca3", indicator])
        rows = [row for row in payload[1] if row.get("value") is not None]
        frame = pd.DataFrame(
            [{"cca3": row["countryiso3code"], indicator: row["value"], "year": row["date"]}
             for row in rows if row.get("countryiso3code")]
        )
        if frame.empty:
            return pd.DataFrame(columns=["cca3", indicator])
        frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
        frame = frame.sort_values("year", ascending=False).drop_duplicates("cca3")
        return frame[["cca3", indicator]]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return pd.DataFrame(columns=["cca3", indicator])


def prepare_countries(raw_records: list[dict[str, Any]]) -> pd.DataFrame:
    """Normalize raw country records into a clean analysis-ready dataframe."""
    rows = []
    for item in raw_records:
        name = item.get("name", {}).get("common")
        cca3 = item.get("cca3")
        if not name or not cca3 or not item.get("unMember", False):
            continue
        capitals = item.get("capital") or []
        languages = sorted(set((item.get("languages") or {}).values()))
        currencies = item.get("currencies") or {}
        currency_names = sorted({value.get("name", code) for code, value in currencies.items()})
        borders = item.get("borders") or []
        rows.append({
            "country": name,
            "cca3": cca3,
            "capital": capitals[0] if capitals else None,
            "languages": ", ".join(languages) if languages else None,
            "currency": ", ".join(currency_names) if currency_names else None,
            "region": item.get("region") or None,
            "subregion": item.get("subregion") or None,
            "flag": item.get("flag", "🌍"),
            "borders": borders,
            "area_km2": item.get("area"),
        })
    frame = pd.DataFrame(rows)
    frame = frame.drop_duplicates(subset="cca3").reset_index(drop=True)
    return frame


def load_country_data(refresh: bool = False, include_world_bank: bool = True) -> pd.DataFrame:
    """Load and combine country facts with optional World Bank indicators."""
    countries = prepare_countries(load_raw_countries(refresh=refresh))

    if include_world_bank:
        for field, indicator in INDICATORS.items():
            extra = load_world_bank_indicator(indicator)
            extra = extra.rename(columns={indicator: field})

            if not extra.empty:
                countries = countries.merge(extra, on="cca3", how="left")
            else:
                countries[field] = pd.NA
    else:
        countries["population"] = pd.NA
        countries["gdp_per_capita"] = pd.NA

    for column in ["population", "gdp_per_capita", "area_km2"]:
        countries[column] = pd.to_numeric(countries[column], errors="coerce")

    return countries