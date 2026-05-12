"""
providers.py — Seed Data Loaders
Student Financial Intelligence Dashboard
"""
import os
import pandas as pd
from typing import List, Optional
from data_model import MetroBenchmark, UniversityProfile


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _data_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


# ─────────────────────────────────────────────────────────────────────────────
# METRO BENCHMARKS
# ─────────────────────────────────────────────────────────────────────────────

def load_metro_benchmarks() -> pd.DataFrame:
    return pd.read_csv(_data_path("metro_benchmarks.csv"))


def get_metro(metro_name: str) -> Optional[MetroBenchmark]:
    df = load_metro_benchmarks()
    row = df[df["metro"] == metro_name]
    if row.empty:
        return None
    r = row.iloc[0]
    return MetroBenchmark(
        metro=r["metro"],
        state=r["state"],
        rent_studio=r["rent_studio"],
        rent_1br=r["rent_1br"],
        rent_shared=r["rent_shared"],
        groceries=r["groceries"],
        utilities=r["utilities"],
        transport_monthly=r["transport_monthly"],
        internet=r["internet"],
        misc_basic=r["misc_basic"],
        discretionary=r["discretionary"],
        cost_tier=r["cost_tier"],
        transit_score=int(r["transit_score"]),
        car_dependency=r["car_dependency"],
    )


def metro_names() -> List[str]:
    df = load_metro_benchmarks()
    return sorted(df["metro"].tolist())


# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSITY PROFILES
# ─────────────────────────────────────────────────────────────────────────────

def load_university_profiles() -> pd.DataFrame:
    return pd.read_csv(_data_path("university_profiles.csv"))


def get_university(name: str) -> Optional[UniversityProfile]:
    df = load_university_profiles()
    row = df[df["university"] == name]
    if row.empty:
        row = df[df["short_name"] == name]
    if row.empty:
        return None
    r = row.iloc[0]
    return UniversityProfile(
        university=r["university"],
        short_name=r["short_name"],
        metro=r["metro"],
        state=r["state"],
        tuition_annual=float(r["tuition_annual"]),
        fees_annual=float(r["fees_annual"]),
        health_insurance_annual=float(r["health_insurance_annual"]),
        on_campus_room_board=float(r["on_campus_room_board"]),
        assistantship_stipend_annual=float(r["assistantship_stipend_annual"]),
        assistantship_probability=float(r["assistantship_probability"]),
        assistantship_covers_tuition=bool(r["assistantship_covers_tuition"]),
        program_type=r["program_type"],
        i20_cost_estimate=float(r["i20_cost_estimate"]),
        notes=r["notes"],
    )


def university_names() -> List[str]:
    df = load_university_profiles()
    return sorted(df["university"].tolist())


def universities_by_metro(metro: str) -> List[str]:
    df = load_university_profiles()
    return sorted(df[df["metro"] == metro]["university"].tolist())


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY: student_costs.csv (used by original pages)
# ─────────────────────────────────────────────────────────────────────────────

def load_student_costs() -> pd.DataFrame:
    df = pd.read_csv(_data_path("student_costs.csv"))
    df["date"] = pd.to_datetime(df["date"])
    return df
