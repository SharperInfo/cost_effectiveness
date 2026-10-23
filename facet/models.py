"""Pydantic model for CET measure input records."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class Measure(BaseModel):
    """One row of the measure input file.

    Attributes are snake_case; each field's alias is the exact CSV header,
    so rows from csv.DictReader validate directly and
    ``model_dump(by_alias=True)`` round-trips back to the file's columns.
    Blank cells are treated as missing (None).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    # --- Identification / program ---
    ce_input_id: str = Field(alias="CEInputID")
    prg_id: str = Field(alias="PrgID")
    claim_year_quarter: str = Field(alias="ClaimYearQuarter", pattern=r"^\d{4}Q[1-4]$")
    sector: str | None = Field(default=None, alias="Sector")
    delivery_type: str | None = Field(default=None, alias="DeliveryType")
    bldg_type: str | None = Field(default=None, alias="BldgType")

    # --- E3 avoided-cost mapping ---
    e3_climate_zone: str | None = Field(default=None, alias="E3ClimateZone")
    e3_gas_sav_profile: str | None = Field(default=None, alias="E3GasSavProfile")
    e3_gas_sector: str | None = Field(default=None, alias="E3GasSector")
    e3_mea_elec_end_use_shape: str | None = Field(
        default=None, alias="E3MeaElecEndUseShape"
    )
    e3_target_sector: str | None = Field(default=None, alias="E3TargetSector")

    # --- Measure description ---
    meas_app_type: str | None = Field(default=None, alias="MeasAppType")
    meas_code: str | None = Field(default=None, alias="MeasCode")
    meas_description: str | None = Field(default=None, alias="MeasDescription")
    meas_impact_type: str | None = Field(default=None, alias="MeasImpactType")
    fuel_id: str | None = Field(default=None, alias="FuelID")
    measure_id: str | None = Field(default=None, alias="MeasureID")
    tech_group: str | None = Field(default=None, alias="TechGroup")
    tech_type: str | None = Field(default=None, alias="TechType")
    use_category: str | None = Field(default=None, alias="UseCategory")
    use_sub_category: str | None = Field(default=None, alias="UseSubCategory")
    water_use: str | None = Field(default=None, alias="WaterUse")
    pre_desc: str | None = Field(default=None, alias="PreDesc")
    std_desc: str | None = Field(default=None, alias="StdDesc")
    source_desc: str | None = Field(default=None, alias="SourceDesc")
    version: str | None = Field(default=None, alias="Version")
    norm_unit: str | None = Field(default=None, alias="NormUnit")
    num_units: float | None = Field(default=None, alias="NumUnits")

    # --- Unit savings (1st / 2nd baseline) ---
    unit_kw_1st_baseline: float | None = Field(default=None, alias="UnitkW1stBaseline")
    unit_kwh_1st_baseline: float | None = Field(
        default=None, alias="UnitkWh1stBaseline"
    )
    unit_therm_1st_baseline: float | None = Field(
        default=None, alias="UnitTherm1stBaseline"
    )
    unit_kw_2nd_baseline: float | None = Field(default=None, alias="UnitkW2ndBaseline")
    unit_kwh_2nd_baseline: float | None = Field(
        default=None, alias="UnitkWh2ndBaseline"
    )
    unit_therm_2nd_baseline: float | None = Field(
        default=None, alias="UnitTherm2ndBaseline"
    )
    unit_kwh_iou_water_1st_baseline: float | None = Field(
        default=None, alias="UnitkWhIOUWater1stBaseline"
    )
    unit_kwh_iou_water_2nd_baseline: float | None = Field(
        default=None, alias="UnitkWhIOUWater2ndBaseline"
    )

    # --- Unit costs / incentives ---
    unit_mea_cost_1st_baseline: float | None = Field(
        default=None, alias="UnitMeaCost1stBaseline"
    )
    unit_mea_cost_2nd_baseline: float | None = Field(
        default=None, alias="UnitMeaCost2ndBaseline"
    )
    unit_direct_install_lab: float | None = Field(
        default=None, alias="UnitDirectInstallLab"
    )
    unit_direct_install_mat: float | None = Field(
        default=None, alias="UnitDirectInstallMat"
    )
    unit_end_user_rebate: float | None = Field(default=None, alias="UnitEndUserRebate")
    unit_incentive_to_others: float | None = Field(
        default=None, alias="UnitIncentiveToOthers"
    )

    # --- Net-to-gross ---
    ntg_id: str | None = Field(default=None, alias="NTG_ID")
    ntgr_kw: float | None = Field(default=None, alias="NTGRkW")
    ntgr_kwh: float | None = Field(default=None, alias="NTGRkWh")
    ntgr_therm: float | None = Field(default=None, alias="NTGRTherm")
    ntgr_cost: float | None = Field(default=None, alias="NTGRCost")

    # --- Useful life ---
    eul_id: str | None = Field(default=None, alias="EUL_ID")
    eul_yrs: float | None = Field(default=None, alias="EUL_Yrs")
    rul_id: str | None = Field(default=None, alias="RUL_ID")
    rul_yrs: float | None = Field(default=None, alias="RUL_Yrs")

    # --- Realization / installation rates ---
    gsia_id: str | None = Field(default=None, alias="GSIA_ID")
    realization_rate_kw: float | None = Field(default=None, alias="RealizationRatekW")
    realization_rate_kwh: float | None = Field(default=None, alias="RealizationRatekWh")
    realization_rate_therm: float | None = Field(
        default=None, alias="RealizationRateTherm"
    )
    installation_rate_kw: float | None = Field(default=None, alias="InstallationRatekW")
    installation_rate_kwh: float | None = Field(
        default=None, alias="InstallationRatekWh"
    )
    installation_rate_therm: float | None = Field(
        default=None, alias="InstallationRateTherm"
    )

    # --- Flags / administrator ---
    residential_flag: bool | None = Field(default=None, alias="Residential_Flag")
    upstream_flag: bool | None = Field(default=None, alias="Upstream_Flag")
    pa: str | None = Field(default=None, alias="PA")

    # --- Other costs and benefits ---
    unit_gas_infra_bens: float | None = Field(default=None, alias="UnitGasInfraBens")
    unit_refrig_costs: float | None = Field(default=None, alias="UnitRefrigCosts")
    unit_refrig_bens: float | None = Field(default=None, alias="UnitRefrigBens")
    unit_misc_costs: float | None = Field(default=None, alias="UnitMiscCosts")
    misc_costs_desc: str | None = Field(default=None, alias="MiscCostsDesc")
    unit_misc_bens: float | None = Field(default=None, alias="UnitMiscBens")
    misc_bens_desc: str | None = Field(default=None, alias="MiscBensDesc")
    unit_tax_credits: float | None = Field(default=None, alias="UnitTaxCredits")

    # --- Rates / misc ---
    rate_schedule_elec: str | None = Field(default=None, alias="RateScheduleElec")
    rate_schedule_gas: str | None = Field(default=None, alias="RateScheduleGas")
    combustion_type: str | None = Field(default=None, alias="CombustionType")
    meas_inflation: float | None = Field(default=None, alias="MeasInflation")
    comments: str | None = Field(default=None, alias="Comments")

    @model_validator(mode="before")
    @classmethod
    def _blank_to_none(cls, data: Any) -> Any:
        """Treat empty / whitespace-only CSV cells as missing values."""
        if isinstance(data, dict):
            return {
                k: (None if isinstance(v, str) and not v.strip() else v)
                for k, v in data.items()
            }
        return data
