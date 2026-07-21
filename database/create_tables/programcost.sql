create table program_cost (
PA text,
PrgID text,
ClaimYearQuarter text,
PrgYear integer,
AdminCostOther numeric,
AdmincCostsOverheadAndGA numeric,
CostsRecoveredFromOtherSources numeric,
DIActivity numeric,
DIHardwareAndMaterials numeric,
DIInstallation numeric,
DIRebateAndInspection numeric,
EMV numeric,
MarketingOutreach numeric,
OnBillFinancing numeric,
UserInputIncentive numeric,
primary key (PrgID, PrgYear)
);