"""
data_model.py — V2 Planning Data Structures
CostCompass — Plan. Manage. Thrive.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class MetroBenchmark:
    metro: str
    state: str
    rent_studio: float
    rent_1br: float
    rent_shared: float
    groceries: float
    utilities: float
    transport_monthly: float
    internet: float
    misc_basic: float
    discretionary: float
    cost_tier: str          # Very Low / Low / Medium / High / Very High
    transit_score: int      # 1-10
    car_dependency: str     # Low / Medium / High / Very High


@dataclass
class UniversityProfile:
    university: str
    short_name: str
    metro: str
    state: str
    tuition_annual: float
    fees_annual: float
    health_insurance_annual: float
    on_campus_room_board: float
    assistantship_stipend_annual: float
    assistantship_probability: float
    assistantship_covers_tuition: bool
    program_type: str
    i20_cost_estimate: float
    notes: str


@dataclass
class FundingInputs:
    monthly_stipend: float = 0.0
    monthly_wage: float = 0.0
    weekly_work_hours: float = 0.0
    hourly_wage: float = 0.0
    family_support_monthly: float = 0.0
    home_currency_monthly: float = 0.0
    home_currency_code: str = "USD"
    fx_rate: float = 1.0
    has_assistantship: bool = False
    tuition_covered_by_aid: bool = False


@dataclass
class LivingCosts:
    rent: float = 0.0
    groceries: float = 0.0
    utilities: float = 0.0
    transport: float = 0.0
    internet: float = 0.0
    misc_basic: float = 0.0
    discretionary: float = 0.0
    health_insurance_monthly: float = 0.0
    tuition_monthly: float = 0.0


@dataclass
class MoveInCosts:
    visa_fee: float = 185.0
    sevis_fee: float = 350.0
    flight: float = 800.0
    housing_deposit: float = 0.0       # typically 1-2 months rent
    first_last_rent: float = 0.0       # first + last month
    furniture_setup: float = 800.0
    winter_clothing: float = 300.0
    phone_setup: float = 150.0
    transport_setup: float = 100.0
    laptop_supplies: float = 0.0
    misc_arrival: float = 200.0

    @property
    def total(self) -> float:
        return (self.visa_fee + self.sevis_fee + self.flight +
                self.housing_deposit + self.first_last_rent +
                self.furniture_setup + self.winter_clothing +
                self.phone_setup + self.transport_setup +
                self.laptop_supplies + self.misc_arrival)


@dataclass
class PlanningScenario:
    label: str
    university: Optional[str]
    metro: str
    state: str
    funding: FundingInputs
    living: LivingCosts
    move_in: MoveInCosts
    starting_cash: float = 0.0
    program_months: int = 24
    has_roommate: bool = False
    has_car: bool = False
    notes: str = ""


@dataclass
class RiskFlag:
    severity: str   # "warning" | "danger" | "info"
    message: str


@dataclass
class DecisionResult:
    scenario_label: str
    monthly_income: float
    monthly_expenses: float
    monthly_surplus: float
    affordability_score: float          # 0-100
    safe_rent_ceiling: float
    move_in_cash_required: float
    starting_cash_after_movein: float
    emergency_runway_months: float
    recommendation: str
    risk_flags: List[RiskFlag] = field(default_factory=list)
    stress_moderate: Optional[float] = None   # surplus under moderate stress
    stress_severe: Optional[float] = None     # surplus under severe stress
    plan_viable: bool = True
    cash_negative_month: Optional[int] = None  # month number when cash goes negative
