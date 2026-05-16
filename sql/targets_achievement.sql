--- Updated region column from sales office master

-- Heritage Samarth · Target Achievement
-- File: sql/targets_achievement.sql
--
-- Achievement % = ACTUALQTY_LPD / BUDGETQTY_LPD × 100
-- Both sides are daily run-rates so partial-month comparisons
-- are always apples-to-apples.
-- ============================================================

WITH Targetandbudget AS (
    SELECT
        PLANT                   AS SalesOffice,
        REGIONNAME              AS Region,
        DIVISION                AS Category,
        EMPLOYEEID,
        EMPLOYEENAME,
        PLANMONTH,
        MATERIALGRP             AS Productgroup,
        MATERIALGRPDESC         AS PH6Desc,
        BUDGETQTY,
        BUDGETAMT,
        ACTUALQTY,
        SALEAMT,
        SOSHORTNAME,
        MANAGERID,
        MANAGERNAME
    FROM [HeritageBI].[STG].[SEBudgets_V2]
    WHERE PLANMONTH =
        CONVERT(VARCHAR(6), DATEADD(DAY, -1, GETDATE()), 112)
),

SO AS (
SELECT PLANT,
    PLANT_NAME,
    Short_Name, 
    REGION_NAME 
    FROM [HeritageBI].[DW].[dsalesofficemaster] 
),

PH7 AS (
    SELECT DISTINCT PH6, PH7Desc
    FROM [HeritageBI].[DW].[ph7]
),
CE_MBL AS (
    SELECT DISTINCT Employee_ID, Employee_Name, Employee_Mobile
    FROM [HeritageIT].[S&D].[Cust_SE_Mapping]
    WHERE Employee_ID   IS NOT NULL
      AND Employee_Name IS NOT NULL
      AND Employee_Mobile IS NOT NULL
)
SELECT
    --B.Region,
    S.REGION_NAME AS Region,
    B.SalesOffice,
    --B.SOSHORTNAME,
    S.PLANT_NAME AS SO_Full,
    S.Short_Name AS SOSHORTNAME,
    B.Category,
    B.EMPLOYEEID,
    B.EMPLOYEENAME,
    M.Employee_Mobile,
    B.MANAGERNAME,
    P.PH7Desc       AS ProductGroup,
    B.PH6Desc,
    B.PLANMONTH,

    -- Raw quantities
    B.BUDGETQTY,
    B.ACTUALQTY,
    --B.BUDGETAMT,
    --B.SALEAMT,

--    -- Budget LPD  = budget ÷ total days in the month
--    CAST(
--        TRY_CAST(B.BUDGETQTY AS FLOAT) * 1.0
--        / NULLIF(DAY(EOMONTH(DATEADD(DAY, -1, GETDATE()))), 0)
--        AS DECIMAL(18, 2)
--    ) AS BUDGETQTY_LPD,

    -- Actual LPD  = actual ÷ days elapsed so far this month
    CAST(
        TRY_CAST(B.ACTUALQTY AS FLOAT) * 1.0
        / NULLIF(DAY(DATEADD(DAY, -1, GETDATE())), 0)
        AS DECIMAL(18, 2)
    ) AS ACTUALQTY_LPD,

        -- Achievement % = ActualQty / BudgetQty × 100
    -- Achievement %
    CAST(
        (
            (
                NULLIF(TRY_CAST(B.ACTUALQTY AS FLOAT), 0) * 1.0
                / NULLIF(DAY(DATEADD(DAY, -1, GETDATE())), 0)
            )
            / NULLIF(TRY_CAST(B.BUDGETQTY AS FLOAT), 0)
        ) * 100
        AS DECIMAL(18,2)
    ) AS Achievement_Percentage,

    -- Days meta (carried along so the API never has to recompute)
    DAY(DATEADD(DAY, -1, GETDATE()))                        AS DaysElapsed,
    DAY(EOMONTH(DATEADD(DAY, -1, GETDATE()))   )            AS DaysInMonth

FROM Targetandbudget B
INNER JOIN PH7 P
    ON B.Productgroup = P.PH6
LEFT JOIN CE_MBL M
    ON CAST(B.EMPLOYEEID AS INT) = CAST(M.Employee_ID AS INT)
LEFT JOIN SO S
    ON S.PLANT = B.SalesOffice