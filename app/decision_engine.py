"""
decision_engine.py — V2 Decision & Recommendation Engine
CostCompass — Plan. Manage. Thrive.
"""
from typing import List, Optional
from data_model import (
    PlanningScenario, DecisionResult, RiskFlag,
    FundingInputs, LivingCosts, MoveInCosts
)


# ─────────────────────────────────────────────────────────────────────────────
# CORE CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def calc_monthly_income(f: FundingInputs) -> float:
    wage_income = f.hourly_wage * f.weekly_work_hours * 4.33
    fx_income = (f.home_currency_monthly / f.fx_rate) if f.fx_rate > 0 else 0
    return f.monthly_stipend + wage_income + f.family_support_monthly + fx_income


def calc_monthly_expenses(l: LivingCosts) -> float:
    return (l.rent + l.groceries + l.utilities + l.transport +
            l.internet + l.misc_basic + l.discretionary +
            l.health_insurance_monthly + l.tuition_monthly)


def calc_affordability_score(income: float, expenses: float, rent: float, tuition_monthly: float) -> float:
    """
    Composite 0-100 score.
    - Surplus ratio (40 pts): surplus / income
    - Rent burden (30 pts): rent / income < 30% is ideal
    - Tuition pressure (20 pts): tuition / income
    - Buffer (10 pts): any surplus at all
    """
    if income <= 0:
        return 0.0

    surplus = income - expenses
    surplus_ratio = max(0, surplus / income)
    rent_ratio = rent / income
    tuition_ratio = tuition_monthly / income if tuition_monthly > 0 else 0

    surplus_pts = min(40, surplus_ratio * 100)
    rent_pts = max(0, 30 - (rent_ratio - 0.30) * 100) if rent_ratio > 0.30 else 30
    tuition_pts = max(0, 20 - tuition_ratio * 60)
    buffer_pts = 10 if surplus > 0 else 0

    return round(min(100, surplus_pts + rent_pts + tuition_pts + buffer_pts), 1)


def calc_safe_rent_ceiling(income: float, tuition_monthly: float, other_expenses: float) -> float:
    """
    Safe rent = income * 0.30, but also capped so total expenses leave at least $150/mo surplus.
    """
    ratio_based = income * 0.30
    budget_based = income - tuition_monthly - other_expenses - 150
    return round(max(0, min(ratio_based, budget_based)), 0)


def calc_emergency_runway(starting_cash_after_movein: float, monthly_expenses: float) -> float:
    if monthly_expenses <= 0:
        return 0.0
    return round(starting_cash_after_movein / monthly_expenses, 1)


def calc_cash_negative_month(starting_cash: float, monthly_surplus: float, months: int = 24) -> Optional[int]:
    """Returns the month number when cumulative cash goes negative, or None if it stays positive."""
    cash = starting_cash
    for m in range(1, months + 1):
        cash += monthly_surplus
        if cash < 0:
            return m
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STRESS SCENARIOS
# ─────────────────────────────────────────────────────────────────────────────

def apply_moderate_stress(income: float, expenses: float, rent: float) -> float:
    """Moderate stress: rent +8%, stipend/wage -10%, groceries +5%"""
    stressed_income = income * 0.90
    stressed_expenses = expenses + (rent * 0.08) + (expenses * 0.03)
    return round(stressed_income - stressed_expenses, 2)


def apply_severe_stress(income: float, expenses: float, rent: float, tuition_monthly: float) -> float:
    """Severe stress: rent +15%, income -25%, emergency expense $500, FX -15%"""
    stressed_income = income * 0.75
    stressed_expenses = expenses + (rent * 0.15) + 500 + (expenses * 0.05)
    return round(stressed_income - stressed_expenses, 2)


# ─────────────────────────────────────────────────────────────────────────────
# RISK FLAGS
# ─────────────────────────────────────────────────────────────────────────────

def generate_risk_flags(
    income: float,
    expenses: float,
    surplus: float,
    rent: float,
    tuition_monthly: float,
    starting_cash_after_movein: float,
    has_assistantship: bool,
    has_car: bool,
    stress_moderate: float,
    stress_severe: float,
    f: FundingInputs,
) -> List[RiskFlag]:
    flags = []

    rent_ratio = rent / income if income > 0 else 1.0

    if rent_ratio > 0.45:
        flags.append(RiskFlag("danger", f"Rent is {rent_ratio*100:.0f}% of income — critically above the 30% safe threshold. This plan is financially fragile."))
    elif rent_ratio > 0.35:
        flags.append(RiskFlag("warning", f"Rent is {rent_ratio*100:.0f}% of income — above the 30% safe threshold. Consider a roommate or cheaper unit."))

    if surplus < 0:
        flags.append(RiskFlag("danger", f"Monthly cash flow is negative (${surplus:,.0f}). This plan is not self-sustaining without additional funding."))
    elif surplus < 150:
        flags.append(RiskFlag("warning", "Monthly surplus is below $150 — very thin margin. One unexpected expense could push you into deficit."))

    if starting_cash_after_movein < expenses * 2:
        flags.append(RiskFlag("danger", "Cash after move-in covers less than 2 months of expenses. You have almost no financial buffer on arrival."))
    elif starting_cash_after_movein < expenses * 3:
        flags.append(RiskFlag("warning", "Cash after move-in covers less than 3 months of expenses. Build a larger emergency reserve before arriving."))

    if not has_assistantship and tuition_monthly > 0:
        flags.append(RiskFlag("warning", "No assistantship. Tuition is fully out-of-pocket. This significantly increases financial pressure."))

    if f.weekly_work_hours > 20:
        flags.append(RiskFlag("warning", f"Work hours set to {f.weekly_work_hours:.0f}/week. F-1 visa limits on-campus work to 20 hours/week during the semester."))

    if stress_moderate < 0:
        flags.append(RiskFlag("warning", "Under moderate stress (rent +8%, income -10%), this plan becomes cash-negative. Low resilience."))

    if stress_severe < -500:
        flags.append(RiskFlag("danger", "Under severe stress (rent +15%, income -25%), this plan collapses. High financial risk."))

    if has_car and income < 2500:
        flags.append(RiskFlag("warning", "A car on this income level adds significant cost pressure. Consider transit-based alternatives."))

    if f.home_currency_monthly > 0 and f.fx_rate > 0:
        flags.append(RiskFlag("info", "Part of your funding is in a foreign currency. Exchange rate movements can reduce your effective income by 10-20%."))

    if income < expenses * 0.85:
        flags.append(RiskFlag("danger", "Income covers less than 85% of expenses. This plan requires either additional funding or significant cost reduction."))

    return flags


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATION TEXT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendation(
    surplus: float,
    affordability_score: float,
    rent: float,
    income: float,
    safe_rent_ceiling: float,
    emergency_runway: float,
    stress_moderate: float,
    stress_severe: float,
    has_assistantship: bool,
    has_roommate: bool,
    cash_negative_month: Optional[int],
) -> str:
    rent_ratio = rent / income if income > 0 else 1.0
    rent_gap = rent - safe_rent_ceiling

    if affordability_score >= 75:
        viability = "Your plan is financially solid."
    elif affordability_score >= 55:
        viability = "Your plan is viable but carries meaningful risk."
    elif affordability_score >= 35:
        viability = "Your plan is financially fragile and requires careful management."
    else:
        viability = "Your plan is not financially sustainable without significant changes."

    rent_note = ""
    if rent > safe_rent_ceiling and rent_gap > 0:
        rent_note = (f" Rent at ${rent:,.0f}/month exceeds your safe ceiling of ${safe_rent_ceiling:,.0f} "
                     f"by ${rent_gap:,.0f}. ")
        if not has_roommate:
            rent_note += "A roommate arrangement could bring rent within a safe range."
        else:
            rent_note += "Even with a roommate, this rent level is above the recommended threshold."
    elif rent <= safe_rent_ceiling:
        rent_note = f" Rent at ${rent:,.0f}/month is within your safe ceiling of ${safe_rent_ceiling:,.0f}."

    runway_note = ""
    if emergency_runway < 2:
        runway_note = " Your post-arrival cash runway is critically short — under 2 months. Arrive with more cash."
    elif emergency_runway < 3:
        runway_note = f" Your post-arrival cash runway is {emergency_runway:.1f} months — thin. Aim for at least 3."
    else:
        runway_note = f" Your post-arrival cash runway is {emergency_runway:.1f} months — adequate."

    stress_note = ""
    if stress_moderate < 0 and stress_severe < 0:
        stress_note = " This plan breaks under both moderate and severe stress. It has no resilience to income disruption."
    elif stress_moderate < 0:
        stress_note = " This plan breaks under moderate stress. A stipend delay or rent increase would push you into deficit."
    elif stress_severe < 0:
        stress_note = " The plan holds under moderate pressure but collapses under severe stress. Maintain a cash buffer."
    else:
        stress_note = " The plan holds under both moderate and severe stress scenarios."

    cash_note = ""
    if cash_negative_month:
        cash_note = f" At current burn rate, your cash balance goes negative around month {cash_negative_month} without additional funding."

    aid_note = ""
    if not has_assistantship:
        aid_note = " Without an assistantship, tuition is the largest financial risk. Explore TA/RA opportunities aggressively in year one."

    return f"{viability}{rent_note}{runway_note}{stress_note}{cash_note}{aid_note}"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENGINE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_scenario(scenario: PlanningScenario) -> DecisionResult:
    f = scenario.funding
    l = scenario.living
    m = scenario.move_in

    income = calc_monthly_income(f)
    expenses = calc_monthly_expenses(l)
    surplus = round(income - expenses, 2)

    other_non_rent = (l.groceries + l.utilities + l.transport + l.internet +
                      l.misc_basic + l.discretionary + l.health_insurance_monthly)
    safe_rent = calc_safe_rent_ceiling(income, l.tuition_monthly, other_non_rent)

    move_in_total = m.total
    cash_after_movein = scenario.starting_cash - move_in_total

    runway = calc_emergency_runway(cash_after_movein, expenses)
    aff_score = calc_affordability_score(income, expenses, l.rent, l.tuition_monthly)

    stress_mod = apply_moderate_stress(income, expenses, l.rent)
    stress_sev = apply_severe_stress(income, expenses, l.rent, l.tuition_monthly)

    cash_neg_month = calc_cash_negative_month(cash_after_movein, surplus, scenario.program_months)

    flags = generate_risk_flags(
        income, expenses, surplus, l.rent, l.tuition_monthly,
        cash_after_movein, f.has_assistantship, scenario.has_car,
        stress_mod, stress_sev, f
    )

    recommendation = generate_recommendation(
        surplus, aff_score, l.rent, income, safe_rent,
        runway, stress_mod, stress_sev,
        f.has_assistantship, scenario.has_roommate, cash_neg_month
    )

    return DecisionResult(
        scenario_label=scenario.label,
        monthly_income=round(income, 2),
        monthly_expenses=round(expenses, 2),
        monthly_surplus=surplus,
        affordability_score=aff_score,
        safe_rent_ceiling=safe_rent,
        move_in_cash_required=round(move_in_total, 2),
        starting_cash_after_movein=round(cash_after_movein, 2),
        emergency_runway_months=runway,
        recommendation=recommendation,
        risk_flags=flags,
        stress_moderate=stress_mod,
        stress_severe=stress_sev,
        plan_viable=(surplus >= 0 and cash_after_movein >= 0),
        cash_negative_month=cash_neg_month,
    )
