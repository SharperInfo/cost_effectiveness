-- Dual baseline savings equations

------------------------------------
------------------------------------
-- Required inputs
------------------------------------
------------------------------------

------------------------------------
-- measure table
------------------------------------
-- unit_savings_1B (UnitkW1stBaseline, UnitkWh1stBaseline, UnitTherm1stBaseline, UnitkWhIOUWater1stBaseline)
-- unit_savings_2B (UnitkW1stBaseline, UnitkWh1stBaseline, UnitTherm1stBaseline, UnitkWhIOUWater1stBaseline)
-- quantity (NumUnit)
-- NTGR (NTGRkW, NTGRkWh, NTGRTherm)
-- GSIA (RealizationRatekW, RealizationRatekWh, RealizationRateTherm, InstallationRatekW, InstallationRatekWh, InstallationRateTherm)
-- EUL (EUL_Yrs)
-- RUL (RUL_Yrs)
------------------------------------
------------------------------------
-- Equations
-- This code presumes EUL and RUL and greater than one
------------------------------------
------------------------------------
-- Gross Savings
first_year_gross_savings = unit_savings_1B * quantity * GSIA
first_year_gross_saving_2B = unit_savings_2B * quantity * GSIA
lifecycle_gross_savings = first_year_gross_savings * RUL + first_year_gross_saving_2B * (RUL - EUL)
-- Net Savings
first_year_net_savings = first_year_gross_savings * NTGR
lifecycle_net_savings = lifecycle_gross_savings * NTGR
-- Savings Types: Therm, kW, kWh, and kWhWater