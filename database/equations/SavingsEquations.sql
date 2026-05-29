-- Savings 

-- inputs
Field Name|Description
--|--
EUL_Yrs|estimated useful life in years
RUL_Yrs|remaining useful life in years
NumUnit|the unadjusted number of units installed
-- Fuel specific fields (kWh, kW, Therm)
Field Name|Description
--|--
NTGR|net to gross ratio
RR|realization rate
IR|installation rate
Unit_1stBaseline|first baseline unit energy savings
Unit_2ndBaseline|second baseline unit energy savings
-- kWh only 
Field Name|Description
--|--
Unit_Water1stBaseline|first baseline unit energy savings from water conservation
Unit_Water2ndBaseline|second baseline unit energy savings from water conservation

-- intermediary fields
Field Name|Description
--|--
life_1B|first baseline years 
life_2B|second baseline years = EUL - RUL
quantity|the number of units installed, adjusted by the installation and realization rates

-- intermediary equations
quantity 	= NumUnit * RR * IR
life_1B 	= case when RUL = 0 then EUL else RUL 
life_2B		= case when RUL = 0 then 0 else EUL - RUL

-- Savings calculations
-- Output for kWh, kW, Therms
first_year_gross = (((Unit_1stBaseline + Unit_Water1stBaseline) * min(life_1B, 1)) 
				 + ((Unit_2ndBaseline + Unit_Water2ndBaseline) * max((1-life_1B), 0)) 	-- resolves to zero for single baseline and for dual baseline where RUL > 1
				 * quantity
first_year_net 	 = first_year_gross * NTGR
-- Output for kWh and Therms
lifecycle_gross  = (((Unit_1stBaseline + Unit_Water1stBaseline) * life_1B) 
				  + ((Unit_2ndBaseline + Unit_Water2ndBaseline) * life_2B)) 	-- resolves to zero for single baseline
				  * quantity
lifecycle_net 	 = lifecycle_gross * NTGR

first_year_gross_kWj = (((UnitkWh1stBaseline + UnitkWhIOUWater1stBaseline) * min(life_1B, 1)) 
 + ((UnitkWh2ndBaseline + UnitkWhWater2ndBaseline) * max((1-life_1B), 0)) 
 * NumUnits * RealizationRatekWh * InstallationRatekWh 


/*
case when (RUL > 0 and RUL < 1) and EUL < 1 	then ((UES_1B + UES_Water_1B) * life_1B) + ((UES_2B + UES_Water_2B) * life_2B)	* quantity
case when (RUL > 0 and RUL < 1) and EUL > 1 	then ((UES_1B + UES_Water_1B) * life_1B) + ((UES_2B + UES_Water_2B) * (1-RUL))	* quantity
*/


/*
scratch pad

case ... 		then first_year_gross = one_year_gross_1B * min(RUL, 1)
								      + one_year_gross_2B * (min(EUL, 1) - RUL)

-- Dual Baseline

-- case when RUL > 1 and EUL > 1
first_year_gross = (unit_energy_savings_1B + unit_energy_savings_from_water_1B) * quantity * installation_rate * realization_rate
lifecycle_gross = first_year_gross * estimated_useful_life -- same as single baseline
-- case when RUL < 1 and EUL > 1
first_year_gross = ((unit_energy_savings_1B + unit_energy_savings_from_water_1B) * quantity * installation_rate * realization_rate * (remaining_useful_life)) 
				 + ((unit_energy_savings_2B + unit_energy_savings_from_water_2B) * quantity * installation_rate * realization_rate * (1 - remaining_useful_life))
-- case when RUL < 1 and EUL < 1
-- ... is this scenario needed?


-- All baseline scenarios
first_year_net = first_year_gross * net_to_gross_ratio
lifecycle_gross = first_year_gross * estimated_useful_life


lifecycle_gross = first_year_gross * estimated_useful_life
lifecycle_net = first_year_net * estimated_useful_life

lifecycle_gross = first_year_gross * estimated_useful_life
lifecycle_net = first_year_net * estimated_useful_life


first_year_gross_dual = case when RUL > 1 then (unit_energy_savings_1B + unit_energy_savings_from_water_1B) * quantity * installation_rate * realization_rate
						else ((unit_energy_savings_1B + unit_energy_savings_from_water_1B) * quantity * installation_rate * realization_rate * (remaining_useful_life)) 
						+ ((unit_energy_savings_2B + unit_energy_savings_from_water_2B) * quantity * installation_rate * realization_rate * (1 - remaining_useful_life))

lifecycle_gross_dual = first_year_gross_dual * remaining_useful_life + ((unit_energy_savings_2B + unit_energy_savings_from_water_2B) * quantity * installation_rate * realization_rate) * (estimated_useful_life - remaining_useful_life))


/*
--- Lifecycle Gross ------------------------------------------------------------
		,SUM(
		   CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * EUL * IRkWh * RRkWh * (kWh1 + kWhWater1)
				ELSE Qty * IRkWh * RRkWh * ((kWh1 + kWhWater1) * RUL + (kWh2 + kWhWater2) * (EUL - RUL))
			END
		) AS LifecycleGrosskWh
*/

-- note to self, that code ^^ looks like the IR and RR are only applied to the first baseline savings, check with some test data
*/
