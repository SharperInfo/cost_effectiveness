CREATE PROCEDURE [dbo].[CalcSavings]
@JobID INT = -1,
@MEBens FLOAT=NULL

AS

SET NOCOUNT ON

DECLARE @ThermConv float
SET @ThermConv = 29.307111111

IF @MEBens Is Null
	BEGIN
		SET @MEBens = IsNull((SELECT MarketEffectBens from CETJobs WHERE ID = @JobID),0)
	END 

PRINT 'Inserting savings...'

CREATE TABLE [#OutputSavings](
	JobID INT NULL,
	PA NVARCHAR(8) NULL,
	PrgID NVARCHAR(255) NULL,
	CET_ID NVARCHAR(255) NOT NULL,
	AnnualGrosskWh FLOAT NULL,
	AnnualGrosskWhSite FLOAT NULL,
	AnnualGrosskWhWater FLOAT NULL,
	AnnualGrosskW FLOAT NULL,
	AnnualGrossThm FLOAT NULL,
	AnnualNetkWh FLOAT NULL,
	AnnualNetkWhSite FLOAT NULL,
	AnnualNetkWhWater FLOAT NULL,
	AnnualNetkW FLOAT NULL,
	AnnualNetThm FLOAT NULL,
	LifecycleGrosskWh FLOAT NULL,
	LifecycleGrosskWhSite FLOAT NULL,
	LifecycleGrosskWhWater FLOAT NULL,
	LifecycleGrossThm FLOAT NULL,
	LifecycleNetkWh FLOAT NULL,
	LifecycleNetkWhSite FLOAT NULL,
	LifecycleNetkWhWater FLOAT NULL,
	LifecycleNetThm FLOAT NULL,
	FirstYearGrosskWh FLOAT NULL,
	FirstYearGrosskWhSite FLOAT NULL,
	FirstYearGrosskWhWater FLOAT NULL,
	FirstYearGrosskW FLOAT NULL,
	FirstYearGrossThm FLOAT NULL,
	FirstYearNetkWh FLOAT NULL,
	FirstYearNetkWhSite FLOAT NULL,
	FirstYearNetkWhWater FLOAT NULL,
	FirstYearNetkW FLOAT NULL,
	FirstYearNetThm FLOAT NULL,
	WeightedSavings FLOAT NULL
) ON [PRIMARY]


BEGIN
	-- Insert into OutputSavings
	INSERT INTO #OutputSavings (
		JobID,
		PA,
		PrgID,
		CET_ID,
		AnnualGrosskWh,
		AnnualGrosskWhSite,
		AnnualGrosskWhWater,
		AnnualGrosskW,
		AnnualGrossThm,
		AnnualNetkWh,
		AnnualNetkWhSite,
		AnnualNetkWhWater,
		AnnualNetkW,
		AnnualNetThm,
		LifecycleGrosskWh,
		LifecycleGrosskWhSite,
		LifecycleGrosskWhWater,
		LifecycleGrossThm,
		LifecycleNetkWh,
		LifecycleNetkWhSite,
		LifecycleNetkWhWater,
		LifecycleNetThm,
		FirstYearGrosskWh,
		FirstYearGrosskWhSite,
		FirstYearGrosskWhWater,
		FirstYearGrosskW,
		FirstYearGrossThm,
		FirstYearNetkWh,
		FirstYearNetkWhSite,
		FirstYearNetkWhWater,
		FirstYearNetkW,
		FirstYearNetThm
	)
	SELECT @JobID
		,e.PA
		,e.PrgID
		,e.CET_ID

--------------------------------------------------------------------------------
--- Average Annual Gross -------------------------------------------------------
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * IRkWh * RRkWh * (kWh1 + kWhWater1)
				ELSE Qty * IRkWh * RRkWh * ((kWh1 + kWhWater1) * RUL + (kWh2 + kWhWater2) * (EUL - RUL)) / EUL
			END
		) AS AnnualGrosskWh
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * IRkWh * RRkWh * kWh1
				ELSE Qty * IRkWh * RRkWh * (kWh1 * RUL + kWh2 * (EUL - RUL)) / EUL
			END
		) AS AnnualGrosskWhSite
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * IRkWh * RRkWh * kWhWater1
				ELSE Qty * IRkWh * RRkWh * (kWhWater1 * RUL + kWhWater2 * (EUL - RUL)) / EUL
			END
		) AS AnnualGrosskWhWater
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * IRkW * RRkW * kW1
				ELSE Qty * IRkW * RRkW * (kW1 * RUL + kW2 * (EUL - RUL)) / EUL
			END
		) AS AnnualGrosskW
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * IRThm * RRThm * Thm1
				ELSE Qty * IRThm * RRThm * (Thm1 * RUL + Thm2 * (EUL - RUL)) / EUL
			END
		) AS AnnualGrossTherms

--------------------------------------------------------------------------------
--- Average Annual Net ---------------------------------------------------------
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * (kWh1 + kWhWater1)
				ELSE Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * ((kWh1 + kWhWater1) * RUL + (kWh2 + kWhWater2) * (EUL - RUL)) / EUL
			END
		) AS AnnualNetkWh
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * kWh1
				ELSE Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * (kWh1 * RUL + kWh2 * (EUL - RUL)) / EUL
			END
		) AS AnnualNetkWhSite
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * kWhWater1
				ELSE Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * (kWhWater1 * RUL + kWhWater2 * (EUL - RUL)) / EUL
			END
		) AS AnnualNetkWhWater
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkW + @MEBens) * IRkW * RRkW * kW1
				ELSE Qty * (NTGRkW + @MEBens) * IRkW * RRkW * (kW1 * RUL + kW2 * (EUL - RUL)) / EUL
			END
		) AS AnnualNetkW
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRThm + @MEBens) * IRThm * RRThm * Thm1
				ELSE Qty * (NTGRThm + @MEBens) * IRThm * RRThm * (Thm1 * RUL + Thm2 * (EUL - RUL)) / EUL
			END
		) AS AnnualNetTherms

--------------------------------------------------------------------------------
--- Lifecycle Gross ------------------------------------------------------------
		,SUM(
		   CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * EUL * IRkWh * RRkWh * (kWh1 + kWhWater1)
				ELSE Qty * IRkWh * RRkWh * ((kWh1 + kWhWater1) * RUL + (kWh2 + kWhWater2) * (EUL - RUL))
			END
		) AS LifecycleGrosskWh
		,SUM(
		   CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * EUL * IRkWh * RRkWh * kWh1
				ELSE Qty * IRkWh * RRkWh * (kWh1 * RUL + kWh2 * (EUL - RUL))
			END
		) AS LifecycleGrosskWhSite
		,SUM(
		   CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * EUL * IRkWh * RRkWh * kWhWater1
				ELSE Qty * IRkWh * RRkWh * (kWhWater1 * RUL + kWhWater2 * (EUL - RUL))
			END
		) AS LifecycleGrosskWhWater
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * EUL * IRThm * RRThm * Thm1
				ELSE Qty * IRThm * RRThm * (Thm1 * RUL + Thm2 * (EUL - RUL))
			END
		) AS LifecycleGrossTherms

--------------------------------------------------------------------------------
--- Lifecycle Net --------------------------------------------------------------
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkWh + @MEBens) * EUL * IRkWh * RRkWh * (kWh1 + kWhWater1)
				ELSE Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * ((kWh1 + kWhWater1) * RUL + (kWh2 + kWhWater2) * (EUL - RUL))
			END
		) AS LifecycleNetkWh
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkWh + @MEBens) * EUL * IRkWh * RRkWh * kWh1
				ELSE Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * (kWh1 * RUL + kWh2 * (EUL - RUL))
			END
		) AS LifecycleNetkWhSite
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRkWh + @MEBens) * EUL * IRkWh * RRkWh * kWhWater1
				ELSE Qty * (NTGRkWh + @MEBens) * IRkWh * RRkWh * (kWhWater1 * RUL + kWhWater2 * (EUL - RUL))
			END
		) AS LifecycleNetkWhWater
		,SUM(
			CASE
				WHEN IsNull(RUL,0) = 0
				THEN Qty * (NTGRThm + @MEBens) * EUL * IRThm * RRThm * Thm1
				ELSE Qty * (NTGRThm + @MEBens) * IRThm * RRThm * (Thm1 * RUL + Thm2* (EUL - RUL))
			END
		) AS LifecycleNetTherms

--------------------------------------------------------------------------------
--- First Year Gross -----------------------------------------------------------
	,SUM(
		CASE
			WHEN RUL >= 1
			THEN 1
			WHEN RUL > 0 AND RUL <= 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * IRkWh * RRkWh * (kWh1 + kWhWater1)
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * IRkWh * RRkWh * (kWh2 + kWhWater2)
	) AS FirstYearGrosskWh
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * IRkWh * RRkWh * kWh1
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * IRkWh * RRkWh * kWh2
	) AS FirstYearGrosskWhSite
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * IRkWh * RRkWh * kWhWater1
		+ CASE
			WHEN RUL > 0 AND RUL <= 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * IRkWh * RRkWh * kWhWater2
	) AS FirstYearGrosskWhWater
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * IRkW * RRkW * kW1 
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * IRkW * RRkW * kW2
	) AS FirstYearGrosskW
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * IRThm * RRThm * Thm1 
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * IRThm * RRThm * Thm2
	) AS FirstYearGrossThm

--------------------------------------------------------------------------------
--- First Year Net -------------------------------------------------------------
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * (NTGRkWh+@MEBens) * IRkWh * RRkWh * (kWh1 + kWhWater1)
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * (NTGRkWh+@MEBens) * IRkWh * RRkWh * (kWh2 + kWhWater2)
	) AS FirstYearNetkWh
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * (NTGRkWh+@MEBens) * IRkWh * RRkWh * kWh1 
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * (NTGRkWh+@MEBens) * IRkWh * RRkWh * kWh2
	) AS FirstYearNetkWhSite
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * (NTGRkWh+@MEBens) * IRkWh * RRkWh * kWhWater1 
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * (NTGRkWh+@MEBens) * IRkWh * RRkWh * kWhWater2
	) AS FirstYearNetkWhWater
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * (NTGRkW+@MEBens) * IRkW * RRkW * kW1 
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * (NTGRkW+@MEBens) * IRkW * RRkW * kW2
	) AS FirstYearNetkW
	,SUM(
		CASE
			WHEN RUL > 1
			THEN 1
			WHEN RUL > 0 AND RUL < 1
			THEN RUL
			WHEN RUL = 0 AND EUL < 1
			THEN EUL
			ELSE 1
		END * Qty * (NTGRThm+@MEBens) * IRThm * RRThm * Thm1 
		+ CASE
			WHEN RUL > 0 AND RUL < 1 AND EUL < 1
			THEN EUL - RUL
			WHEN RUL > 0 AND RUL < 1 AND EUL >= 1
			THEN 1 - RUL
			ELSE 0
		END * Qty * (NTGRThm+@MEBens) * IRThm * RRThm * Thm2
	) AS FirstYearNetThm
	FROM InputMeasurevw e
	GROUP BY e.PA
		,e.PrgID
		,e.CET_ID
	ORDER BY e.PA
		,e.PrgID
		,e.CET_ID
END

--------------------------------------------------------------------------------
--- Calculate WeightedSavings --------------------------------------------------
BEGIN
WITH SavingsSUM (
	  PrgID
	, SUMkWh
	, SUMThm
)
AS (
	SELECT PrgID
		,SUM(
			CASE 
				WHEN FirstYearGrosskWh > 0
				THEN FirstYearGrosskWh
				ELSE 0
			END
		) AS SUMkWh
		,SUM(
			CASE 
				WHEN FirstYearGrossThm > 0
				THEN @ThermConv * FirstYearGrossThm
				ELSE 0
			END
		) AS SUMThm
	FROM #OutputSavings
	GROUP BY PrgID
)
, RecordCount (
	  PrgID
	, RecordCount
)
AS 
(
	SELECT PrgID
		,COUNT(CET_ID) AS RecordCount
	FROM #OutputSavings
	GROUP BY PrgID
)
, WeightedSavings (
	  CET_ID
	, WeightedSavings
)
AS 
(
	SELECT  CET_ID
		,CASE 
			WHEN (ss.SUMkWh <> 0 OR ss.SUMThm <> 0)
			THEN (
				CASE 
					WHEN FirstYearGrosskWh > 0
					THEN FirstYearGrosskWh
					ELSE 0
				END + CASE
					WHEN FirstYearGrossThm > 0
					THEN @ThermConv * FirstYearGrossThm
					ELSE 0
				END
			) / (ss.SUMkWh + ss.SUMThm)
			ELSE 
				1.000 / cc.RecordCount -- If no benefits then divide program costs evenly among claims
		END AS WeightedSavings
	FROM  #OutputSavings s
	LEFT JOIN SavingsSUM ss ON s.PrgID = ss.PrgID
	LEFT JOIN RecordCount cc ON  s.PrgID = cc.PrgID
) 

UPDATE s SET s.WeightedSavings = ws.WeightedSavings
FROM WeightedSavings ws
LEFT JOIN #OutPutSavings s ON ws.CET_ID = s.CET_ID

END

DELETE FROM OutputSavings
DELETE FROM SavedSavings

--Insert final output
INSERT INTO OutputSavings
SELECT
	JobID
	,PA
	,PrgID
	,CET_ID
	,AnnualGrosskWh
	,AnnualGrosskWhSite
	,AnnualGrosskWhWater
	,AnnualGrosskW
	,AnnualGrossThm
	,AnnualNetkWh
	,AnnualNetkWhSite
	,AnnualNetkWhWater
	,AnnualNetkW
	,AnnualNetThm
	,LifecycleGrosskWh
	,LifecycleGrosskWhSite
	,LifecycleGrosskWhWater
	,LifecycleGrossThm
	,LifecycleNetkWh
	,LifecycleNetkWhSite
	,LifecycleNetkWhWater
	,LifecycleNetThm
	,FirstYearGrosskWh
	,FirstYearGrosskWhSite
	,FirstYearGrosskWhWater
	,FirstYearGrosskW
	,FirstYearGrossThm
	,FirstYearNetkWh
	,FirstYearNetkWhSite
	,FirstYearNetkWhWater
	,FirstYearNetkW
	,FirstYearNetThm
	,WeightedSavings
FROM #OutputSavings
ORDER BY JobID, CET_ID ASC

--PRINT 'Done!'

GO
