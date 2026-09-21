from datetime import date

import pythaidate

PHASE_WAXING = "ข้างขึ้น"
PHASE_WANING = "ข้างแรม"
PHASES = {PHASE_WAXING, PHASE_WANING}
RULESET = "thai-traditional-birth-and-conception-elements-v2"
LUNAR_CALENDAR_SOURCE = "pythaidate-0.2.0 CsDate"

BIRTH_ELEMENT_TABLE = {
    (1, PHASE_WAXING): ("ธาตุน้ำ", "เตโชพิการ", "กำเดาระคน"),
    (1, PHASE_WANING): ("ธาตุดิน", "ปถวีพิการ", "กรีสะระคน"),
    (2, PHASE_WAXING): ("ธาตุดิน", "ปถวีพิการ", "กรีสะระคน"),
    (2, PHASE_WANING): ("ธาตุดิน", "วาโยพิการ", "สุมนาวาตะระคน"),
    (3, PHASE_WAXING): ("ธาตุดิน", "วาโยพิการ", "สุมนาวาตะระคน"),
    (3, PHASE_WANING): ("ธาตุดิน", "อาโปพิการ", "คูถเสมหะระคน"),
    (4, PHASE_WAXING): ("ธาตุดิน", "อาโปพิการ", "คูถเสมหะระคน"),
    (4, PHASE_WANING): ("ธาตุไฟ", "เตโชกำเริบ", "พัทธะระคน"),
    (5, PHASE_WAXING): ("ธาตุไฟ", "เตโชกำเริบ", "พัทธะระคน"),
    (5, PHASE_WANING): ("ธาตุไฟ", "ปถวีกำเริบ", "หทัยวัตถุระคน"),
    (6, PHASE_WAXING): ("ธาตุไฟ", "ปถวีกำเริบ", "หทัยวัตถุระคน"),
    (6, PHASE_WANING): ("ธาตุไฟ", "วาโยกำเริบ", "หทัยวาตะระคน"),
    (7, PHASE_WAXING): ("ธาตุไฟ", "วาโยกำเริบ", "หทัยวาตะระคน"),
    (7, PHASE_WANING): ("ธาตุลม", "อาโปกำเริบ", "คอเสมหะระคน"),
    (8, PHASE_WAXING): ("ธาตุลม", "อาโปกำเริบ", "คอเสมหะระคน"),
    (8, PHASE_WANING): ("ธาตุลม", "เตโชหย่อน", "อพัทธะระคน"),
    (9, PHASE_WAXING): ("ธาตุลม", "เตโชหย่อน", "อพัทธะระคน"),
    (9, PHASE_WANING): ("ธาตุลม", "ปถวีหย่อน", "อุทริยะระคน"),
    (10, PHASE_WAXING): ("ธาตุลม", "ปถวีหย่อน", "อุทริยะระคน"),
    (10, PHASE_WANING): ("ธาตุน้ำ", "วาโยหย่อน", "สัตถกวาตะระคน"),
    (11, PHASE_WAXING): ("ธาตุน้ำ", "วาโยหย่อน", "สัตถกวาตะระคน"),
    (11, PHASE_WANING): ("ธาตุน้ำ", "อาโปหย่อน", "อุระเสมหะระคน"),
    (12, PHASE_WAXING): ("ธาตุน้ำ", "อาโปหย่อน", "อุระเสมหะระคน"),
    (12, PHASE_WANING): ("ธาตุน้ำ", "เตโชพิการ", "กำเดาระคน"),
}


def lookup(month: int, phase: str) -> dict:
    element, condition, mixed_with = BIRTH_ELEMENT_TABLE[(month, phase)]
    return {"element": element, "condition": condition, "mixed_with": mixed_with}


def lunar_from_solar(birth_date: date | None) -> dict | None:
    if not birth_date:
        return None
    thai_date = pythaidate.date(birth_date.year, birth_date.month, birth_date.day)
    lunar = pythaidate.CsDate.from_julianday(thai_date.julianday)
    phase = PHASE_WANING if lunar.tithi > 15 else PHASE_WAXING
    lunar_day = lunar.tithi - 15 if phase == PHASE_WANING else lunar.tithi
    month = 8 if lunar.month == 88 else lunar.month
    return {
        "month": month,
        "month_raw": lunar.month,
        "phase": phase,
        "lunar_day": lunar_day,
        "tithi": lunar.tithi,
        "year": lunar.year,
        "year_naksat": lunar.yearnaksatr,
        "leap_month": lunar.leap_month,
        "leap_day": lunar.leap_day,
        "days_in_year": lunar.days_in_year,
        "source": LUNAR_CALENDAR_SOURCE,
    }


def fill_lunar_inputs(values: dict) -> dict:
    next_values = dict(values)
    if next_values.get("birth_lunar_month") and next_values.get("birth_lunar_phase"):
        return next_values
    lunar = lunar_from_solar(next_values.get("birth_date"))
    if not lunar:
        return next_values
    if not next_values.get("birth_lunar_month"):
        next_values["birth_lunar_month"] = lunar["month"]
    if not next_values.get("birth_lunar_phase"):
        next_values["birth_lunar_phase"] = lunar["phase"]
    return next_values


def calculate(
    birth_month: int | None,
    birth_phase: str | None,
    gestation_months: int | None,
    birth_date: date | None = None,
):
    auto_lunar = lunar_from_solar(birth_date)
    month = birth_month or (auto_lunar or {}).get("month")
    phase = birth_phase or (auto_lunar or {}).get("phase")
    if month is None or phase is None:
        return {
            "status": "incomplete",
            "reason": "ต้องมีวันเกิดหรือเดือนจันทรคติพร้อมช่วงข้างขึ้น/ข้างแรม",
            "ruleset": RULESET,
        }
    if month < 1 or month > 12:
        return {"status": "invalid", "reason": "เดือนต้องอยู่ระหว่าง 1–12", "ruleset": RULESET}
    if phase not in PHASES:
        return {"status": "invalid", "reason": "ช่วงเกิดต้องเป็นข้างขึ้นหรือข้างแรม", "ruleset": RULESET}
    lunar_source = (
        LUNAR_CALENDAR_SOURCE
        if auto_lunar and auto_lunar["month"] == month and auto_lunar["phase"] == phase
        else "manual"
    )
    result = {
        "status": "calculated" if gestation_months else "partial",
        "ruleset": RULESET,
        "lunar_source": lunar_source,
        "auto_lunar": auto_lunar,
        "birth_month": month,
        "birth_phase": phase,
        "gestation_months": gestation_months,
        "birth_element": lookup(month, phase),
    }
    if gestation_months is None:
        result["reason"] = "ยังไม่มีจำนวนเดือนในครรภ์ จึงแสดงเฉพาะธาตุเมื่อแรกคลอด"
        return result
    if gestation_months < 1 or gestation_months > 12:
        return {"status": "invalid", "reason": "เดือนในครรภ์ต้องอยู่ระหว่าง 1–12", "ruleset": RULESET}
    conception_month = ((month - gestation_months - 1) % 12) + 1
    result.update(
        {
            "conception_month": conception_month,
            "conception_element": {
                "waxing": lookup(conception_month, PHASE_WAXING),
                "waning": lookup(conception_month, PHASE_WANING),
            },
        }
    )
    return result
