INSERT INTO public.program_cost(
	pa, prgid, claimyearquarter, prgyear, 
	admincostother, admincostsoverheadandga, costsrecoveredfromothersources, 
	-- di = Direct implementation
	diactivity, dihardwareandmaterials, diinstallation, direbateandinspection, 
	emv, marketingoutreach, onbillfinancing, userinputincentive)
	VALUES ('PGE', 'ProgramOne', '2026Q3', 2026, 100, 100, 0, 10, 10, 10, 10, 100, 100, 0, 100);