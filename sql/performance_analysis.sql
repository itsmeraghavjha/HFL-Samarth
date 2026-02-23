-- ;WITH Base_Sales AS (
--     SELECT
--         BillingDate,
--         CustomerID,
--         CustomerGroup,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SalesQuantity
--     FROM [HeritageBI].[DW].[fSales] (NOLOCK)
--     WHERE BillingDate >= '2023-01-01' 
--       AND CustomerID NOT LIKE '%O%'
--       AND ProductHeirachy1 IN ('Milk','Curd','ButterMilk')
--       AND CustomerGroup is not null --NOT IN ('E-Commerce', 'Modern Formats', 'Institutions')
-- ),

-- -- ===================== LAST MONTH (FULL) =====================
-- Last_Month AS (
--     SELECT
--         CustomerID,
--         CustomerGroup,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         DAY(EOMONTH(DATEADD(MONTH, -1, GETDATE())))
--         AS Avg_Daily_Sales_Last_Month
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
--       AND BillingDate <  DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
--     GROUP BY CustomerID, CustomerGroup, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST MONTH TILL DATE =====================
-- LMTD_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         DAY(DATEADD(DAY, -1, GETDATE()))
--         AS Avg_Daily_Sales_LMTD
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
--       AND BillingDate <  DATEADD(
--             DAY,
--             DAY(DATEADD(DAY, -1, GETDATE())),
--             DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
--         )
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== CURRENT MONTH MTD =====================
-- CM_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         DAY(DATEADD(DAY, -1, GETDATE()))
--         AS MTD_Avg_Daily_Sales
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
--       AND BillingDate <= DATEADD(DAY, -1, GETDATE())
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== SAME MONTH LAST YEAR =====================
-- LY_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         DAY(EOMONTH(DATEADD(YEAR, -1, GETDATE())))
--         AS Avg_Daily_Sales_Same_Month_Last_Year
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0))
--       AND BillingDate <  DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) + 1, 0))
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== SAME MONTH LAST YEAR TILL DATE =====================
-- LYMTD_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         DAY(DATEADD(DAY, -1, GETDATE()))
--         AS LYMTD_Avg_Daily_Sales
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(
--             YEAR, -1,
--             DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0)
--         )
--       AND BillingDate <= DATEADD(
--             YEAR, -1,
--             DATEADD(DAY, -1, GETDATE())
--         )
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST QUARTER =====================
-- LQ_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         DATEDIFF(
--             DAY,
--             DATEADD(QUARTER, DATEDIFF(QUARTER, 0, GETDATE()) - 1, 0),
--             DATEADD(QUARTER, DATEDIFF(QUARTER, 0, GETDATE()), 0)
--         )
--         AS Avg_Daily_Sales_Last_Quarter
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(QUARTER, DATEDIFF(QUARTER, 0, GETDATE()) - 1, 0)
--       AND BillingDate <  DATEADD(QUARTER, DATEDIFF(QUARTER, 0, GETDATE()), 0)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST WEEK =====================
-- LW_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / 7
--         AS Avg_Daily_Sales_Last_Week
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()) - 1, 0)
--       AND BillingDate <  DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== CURRENT WEEK =====================
-- TW_Sales AS (
--     SELECT
--         CustomerID,
--         SalesOfficeID,
--         ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 /
--         (DATEDIFF(
--             DAY,
--             DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0),
--             DATEADD(DAY, -1, GETDATE())
--         ) + 1)
--         AS Avg_Daily_Sales_Current_Week
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(WEEK, DATEDIFF(WEEK, 0, GETDATE()), 0)
--       AND BillingDate <= DATEADD(DAY, -1, GETDATE())
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- Last_Order_Date AS (
--     SELECT
--         CustomerID,
--         MAX(BillingDate) AS Last_Order_Date
--     FROM Base_Sales
--     GROUP BY CustomerID
-- )

-- -- ===================== FINAL SELECT =====================
-- SELECT
--     SO.STATE AS State,
--     SO.REGION_NAME AS Region,
--     SO.PLANT_NAME,
--     SO.Short_Name AS SO_Name,
-- 	LM.SalesOfficeID AS SO,
--     LM.CustomerID,
-- 	C.CustomerName,
--     LM.CustomerGroup,
-- 	M.[Employee_ID] AS SE_EmpID,
--     M.[Employee_Name] AS SE_Name,
--     M.[Employee_Mobile] AS SE_Mobile,
--     LM.ProductHeirachy1 AS Product,
--     LY.Avg_Daily_Sales_Same_Month_Last_Year AS LYSM,
-- 	LYMTD.LYMTD_Avg_Daily_Sales AS LYMTD,
-- 	LQ.Avg_Daily_Sales_Last_Quarter      AS LQ,
--     LM.Avg_Daily_Sales_Last_Month        AS LM,
--     LMTD.Avg_Daily_Sales_LMTD            AS LMTD,
--     CM.MTD_Avg_Daily_Sales               AS MTD,
--     LW.Avg_Daily_Sales_Last_Week         AS LW,
--     TW.Avg_Daily_Sales_Current_Week      AS CW,
-- 	    -- ================= ABSOLUTE LPD DIFFERENCES =================

--     ROUND(
--         LM.Avg_Daily_Sales_Last_Month 
--         - LY.Avg_Daily_Sales_Same_Month_Last_Year,
--         2
--     ) AS YoY_Abs_LPD_Diff,

--     ROUND(
--         CM.MTD_Avg_Daily_Sales 
--         - LMTD.Avg_Daily_Sales_LMTD,
--         2
--     ) AS MTD_vs_LMTD_Abs_LPD_Diff,

--     ROUND(
--         CM.MTD_Avg_Daily_Sales 
--         - LYMTD.LYMTD_Avg_Daily_Sales,
--         2
--     ) AS MTD_vs_LYMTD_Abs_LPD_Diff,

--     --CASE
--     --    WHEN LY.Avg_Daily_Sales_Same_Month_Last_Year IS NULL
--     --      OR LY.Avg_Daily_Sales_Same_Month_Last_Year = 0 THEN 'Growth'
--     --    WHEN LM.Avg_Daily_Sales_Last_Month > LY.Avg_Daily_Sales_Same_Month_Last_Year THEN 'Growth'
--     --    WHEN LM.Avg_Daily_Sales_Last_Month < LY.Avg_Daily_Sales_Same_Month_Last_Year THEN 'Degrow'
--     --    ELSE 'Stagnant'
--     --END AS Last_Month_YoY_Trend,

-- 	CASE
--     WHEN (LYMTD.LYMTD_Avg_Daily_Sales IS NULL 
--           OR LYMTD.LYMTD_Avg_Daily_Sales = 0)
--          AND CM.MTD_Avg_Daily_Sales > 0
--         THEN 'New Customer'

--     WHEN CM.MTD_Avg_Daily_Sales = 0
--          AND LYMTD.LYMTD_Avg_Daily_Sales > 0
--         THEN 'Decline'

--     WHEN CM.MTD_Avg_Daily_Sales > LYMTD.LYMTD_Avg_Daily_Sales
--         THEN 'Growth'

--     WHEN CM.MTD_Avg_Daily_Sales < LYMTD.LYMTD_Avg_Daily_Sales
--         THEN 'Decline'

--     ELSE 'Stagnant'
-- END AS Sales_Trend,

-- 	-----CASE
--     -----    WHEN LYMTD.LYMTD_Avg_Daily_Sales IS NULL 
--     -----         OR LYMTD.LYMTD_Avg_Daily_Sales = 0 THEN 'Growth'
--     -----    WHEN CM.MTD_Avg_Daily_Sales > LYMTD.LYMTD_Avg_Daily_Sales THEN 'Growth'
--     -----    WHEN CM.MTD_Avg_Daily_Sales < LYMTD.LYMTD_Avg_Daily_Sales THEN 'Degrow'
--     -----    ELSE 'Stagnant'
--     -----END AS Sales_Trend, --Current_Month_YoY_Trend,


--     ROUND(
--         (LM.Avg_Daily_Sales_Last_Month - LY.Avg_Daily_Sales_Same_Month_Last_Year) /
--         NULLIF(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0), 4
--     ) AS YoY_Growth_Percentage,

--     ROUND(
--         (CM.MTD_Avg_Daily_Sales - LMTD.Avg_Daily_Sales_LMTD) /
--         NULLIF(LMTD.Avg_Daily_Sales_LMTD, 0), 4
--     ) AS MTD_vs_LMTD_Growth_Percentage,

-- 	ROUND(
--     (CM.MTD_Avg_Daily_Sales - LYMTD.LYMTD_Avg_Daily_Sales) /
--     NULLIF(LYMTD.LYMTD_Avg_Daily_Sales, 0),
--     4
-- ) AS MTD_vs_LYMTD_Growth_Percentage,

--     --CASE
--     --    WHEN LMTD.Avg_Daily_Sales_LMTD IS NULL
--     --      OR LMTD.Avg_Daily_Sales_LMTD = 0 THEN 'No Base'
--     --    WHEN CM.MTD_Avg_Daily_Sales > LMTD.Avg_Daily_Sales_LMTD THEN 'Positive'
--     --    WHEN CM.MTD_Avg_Daily_Sales < LMTD.Avg_Daily_Sales_LMTD THEN 'Negative'
--     --    ELSE 'Stable'
--     --END AS MTD_Momentum,

--     D.Last_Order_Date

-- FROM Last_Month LM
-- LEFT JOIN LYMTD_Sales LYMTD
--     ON LYMTD.CustomerID = LM.CustomerID
--    AND LYMTD.SalesOfficeID = LM.SalesOfficeID
--    AND LYMTD.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN LMTD_Sales LMTD
--     ON LMTD.CustomerID = LM.CustomerID
--    AND LMTD.SalesOfficeID = LM.SalesOfficeID
--    AND LMTD.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN CM_Sales CM
--     ON CM.CustomerID = LM.CustomerID
--    AND CM.SalesOfficeID = LM.SalesOfficeID
--    AND CM.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN LY_Sales LY
--     ON LY.CustomerID = LM.CustomerID
--    AND LY.SalesOfficeID = LM.SalesOfficeID
--    AND LY.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN LQ_Sales LQ
--     ON LQ.CustomerID = LM.CustomerID
--    AND LQ.SalesOfficeID = LM.SalesOfficeID
--    AND LQ.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN LW_Sales LW
--     ON LW.CustomerID = LM.CustomerID
--    AND LW.SalesOfficeID = LM.SalesOfficeID
--    AND LW.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN TW_Sales TW
--     ON TW.CustomerID = LM.CustomerID
--    AND TW.SalesOfficeID = LM.SalesOfficeID
--    AND TW.ProductHeirachy1 = LM.ProductHeirachy1
-- LEFT JOIN Last_Order_Date D
--     ON D.CustomerID = LM.CustomerID
-- LEFT JOIN [HeritageBI].[DW].[dsalesofficemaster] SO
--     ON SO.PLANT = LM.SalesOfficeID
-- LEFT JOIN (SELECT Distinct 
--        [CustomerID]
--       ,[Employee_ID]
--       ,[Employee_Name]
--       ,[Employee_Mobile]
--   FROM [HeritageIT].[S&D].[Cust_SE_Mapping])
--  M 
-- 	ON M.CustomerID=LM.CustomerID
-- LEFT JOIN (SELECT Distinct 
-- 			CustomerID,
-- 			CustomerName 
--   FROM [HeritageBI].[DW].[dCustomer])
--  C
-- 	ON C.CustomerID=LM.CustomerID
-- WHERE LM.Avg_Daily_Sales_Last_Month > 0.0001
-- ORDER BY MTD_vs_LYMTD_Abs_LPD_Diff ;

---------------------------------------------------------------------------------------------------------

-- ;WITH Base_Sales AS (
--     SELECT
--         BillingDate,
--         CustomerID,
--         CustomerGroup, 
--         SalesOfficeID,
--         ProductHeirachy1,
--         SalesQuantity
--     FROM [HeritageBI].[DW].[fSales] (NOLOCK)
--     WHERE BillingDate >= '2023-01-01' 
--       AND CustomerID NOT LIKE '%O%'
--       AND ProductHeirachy1 IN ('Milk','Curd','ButterMilk')
-- ),

-- -- ===================== LATEST CUSTOMER GROUP (DEDUPLICATION) =====================
-- Latest_Customer_Group AS (
--     SELECT CustomerID, CustomerGroup
--     FROM (
--         SELECT CustomerID, CustomerGroup,
--             ROW_NUMBER() OVER(PARTITION BY CustomerID ORDER BY BillingDate DESC) as rn
--         FROM Base_Sales
--         WHERE CustomerGroup IS NOT NULL 
--     ) t
--     WHERE rn = 1
-- ),

-- -- ===================== MASTER DIMENSIONS =====================
-- Master_Dimensions AS (
--     SELECT DISTINCT CustomerID, SalesOfficeID, ProductHeirachy1
--     FROM Base_Sales
-- ),

-- -- ===================== LAST MONTH (FULL) =====================
-- Last_Month AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / DAY(EOMONTH(DATEADD(MONTH, -1, CAST(GETDATE() AS DATE)))) AS Avg_Daily_Sales_Last_Month
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)) - 1, 0)
--       AND BillingDate <  DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST MONTH TILL DATE =====================
-- LMTD_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / NULLIF(DAY(DATEADD(DAY, -1, CAST(GETDATE() AS DATE))), 0) AS Avg_Daily_Sales_LMTD
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)) - 1, 0)
--       AND BillingDate <  DATEADD(MONTH, -1, CAST(GETDATE() AS DATE))
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== CURRENT MONTH MTD =====================
-- CM_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / NULLIF(DAY(DATEADD(DAY, -1, CAST(GETDATE() AS DATE))), 0) AS MTD_Avg_Daily_Sales
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0)
--       AND BillingDate <  CAST(GETDATE() AS DATE)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== SAME MONTH LAST YEAR =====================
-- LY_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / DAY(EOMONTH(DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)))) AS Avg_Daily_Sales_Same_Month_Last_Year
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0))
--       AND BillingDate <  DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)) + 1, 0))
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== SAME MONTH LAST YEAR TILL DATE =====================
-- LYMTD_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / NULLIF(DAY(DATEADD(DAY, -1, CAST(GETDATE() AS DATE))), 0) AS LYMTD_Avg_Daily_Sales
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0))
--       AND BillingDate <  DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST QUARTER =====================
-- LQ_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / DATEDIFF(DAY, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)) - 1, 0), DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)), 0)) AS Avg_Daily_Sales_Last_Quarter
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)) - 1, 0)
--       AND BillingDate <  DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)), 0)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST WEEK =====================
-- LW_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / 7 AS Avg_Daily_Sales_Last_Week
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)) - 1, 0)
--       AND BillingDate <  DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)), 0)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== CURRENT WEEK =====================
-- TW_Sales AS (
--     SELECT
--         CustomerID, SalesOfficeID, ProductHeirachy1,
--         SUM(SalesQuantity) * 1.0 / NULLIF(DATEDIFF(DAY, DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)), 0), CAST(GETDATE() AS DATE)), 0) AS Avg_Daily_Sales_Current_Week
--     FROM Base_Sales
--     WHERE BillingDate >= DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)), 0)
--       AND BillingDate <  CAST(GETDATE() AS DATE)
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== LAST ORDER DATE =====================
-- Last_Order_Date AS (
--     SELECT CustomerID, SalesOfficeID, ProductHeirachy1, MAX(BillingDate) AS Last_Order_Date
--     FROM Base_Sales
--     GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
-- ),

-- -- ===================== DEDUPLICATED DIMENSIONS =====================
-- SE_Mapping AS (
--     SELECT CustomerID, Employee_ID, Employee_Name, Employee_Mobile,
--         ROW_NUMBER() OVER(PARTITION BY CustomerID ORDER BY Employee_ID) as rn
--     FROM [HeritageIT].[S&D].[Cust_SE_Mapping]
--     WHERE Division != 4 
-- ),
-- Customer_Master_Dedup AS (
--     SELECT CustomerID, CustomerName
--     FROM (
--         SELECT CustomerID, CustomerName, ROW_NUMBER() OVER(PARTITION BY CustomerID ORDER BY CustomerName DESC) as rn
--         FROM [HeritageBI].[DW].[dCustomer]
--     ) c WHERE rn = 1
-- ),
-- SalesOffice_Master_Dedup AS (
--     SELECT PLANT, STATE, REGION_NAME, PLANT_NAME, Short_Name
--     FROM (
--         SELECT PLANT, STATE, REGION_NAME, PLANT_NAME, Short_Name, ROW_NUMBER() OVER(PARTITION BY PLANT ORDER BY PLANT_NAME DESC) as rn
--         FROM [HeritageBI].[DW].[dsalesofficemaster]
--     ) s WHERE rn = 1
-- )

-- -- ===================== FINAL SELECT =====================
-- SELECT
--     SO.STATE                                        AS State,
--     SO.REGION_NAME                                  AS Region,
--     SO.PLANT_NAME,
--     SO.Short_Name                                   AS SO_Name,
--     MD.SalesOfficeID                                AS SO,
--     MD.CustomerID,
--     C.CustomerName,
--     LCG.CustomerGroup,                              
--     M.Employee_ID                                   AS SE_EmpID,
--     M.Employee_Name                                 AS SE_Name,
--     M.Employee_Mobile                               AS SE_Mobile,
--     MD.ProductHeirachy1                             AS Product,
    
--     ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0) AS LYSM,
--     ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0)             AS LYMTD,
--     ISNULL(LQ.Avg_Daily_Sales_Last_Quarter, 0)         AS LQ,
--     ISNULL(LM.Avg_Daily_Sales_Last_Month, 0)           AS LM,
--     ISNULL(LMTD.Avg_Daily_Sales_LMTD, 0)               AS LMTD,
--     ISNULL(CM.MTD_Avg_Daily_Sales, 0)                  AS MTD,
--     ISNULL(LW.Avg_Daily_Sales_Last_Week, 0)            AS LW,
--     ISNULL(TW.Avg_Daily_Sales_Current_Week, 0)         AS CW,

--     ROUND(ISNULL(LM.Avg_Daily_Sales_Last_Month, 0) - ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0), 2) AS YoY_Abs_LPD_Diff,
--     ROUND(ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LMTD.Avg_Daily_Sales_LMTD, 0), 2) AS MTD_vs_LMTD_Abs_LPD_Diff,
--     ROUND(ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0), 2) AS MTD_vs_LYMTD_Abs_LPD_Diff,

--     CASE
--         WHEN ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) = 0 AND ISNULL(CM.MTD_Avg_Daily_Sales, 0) > 0 THEN 'New Customer'
--         WHEN ISNULL(CM.MTD_Avg_Daily_Sales, 0) = 0 AND ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) > 0 THEN 'Decline'
--         WHEN ISNULL(CM.MTD_Avg_Daily_Sales, 0) > ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) THEN 'Growth'
--         WHEN ISNULL(CM.MTD_Avg_Daily_Sales, 0) < ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) THEN 'Decline'
--         ELSE 'Stagnant'
--     END AS Sales_Trend,

--     ROUND((ISNULL(LM.Avg_Daily_Sales_Last_Month, 0) - ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0)) / NULLIF(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0), 4) AS YoY_Growth_Percentage,
--     ROUND((ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LMTD.Avg_Daily_Sales_LMTD, 0)) / NULLIF(LMTD.Avg_Daily_Sales_LMTD, 0), 4) AS MTD_vs_LMTD_Growth_Percentage,
--     ROUND((ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0)) / NULLIF(LYMTD.LYMTD_Avg_Daily_Sales, 0), 4) AS MTD_vs_LYMTD_Growth_Percentage,
--     D.Last_Order_Date

-- FROM Master_Dimensions MD
-- LEFT JOIN Latest_Customer_Group LCG ON LCG.CustomerID = MD.CustomerID
-- LEFT JOIN Last_Month LM ON LM.CustomerID = MD.CustomerID AND LM.SalesOfficeID = MD.SalesOfficeID AND LM.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN LYMTD_Sales LYMTD ON LYMTD.CustomerID = MD.CustomerID AND LYMTD.SalesOfficeID = MD.SalesOfficeID AND LYMTD.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN LMTD_Sales LMTD ON LMTD.CustomerID = MD.CustomerID AND LMTD.SalesOfficeID = MD.SalesOfficeID AND LMTD.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN CM_Sales CM ON CM.CustomerID = MD.CustomerID AND CM.SalesOfficeID = MD.SalesOfficeID AND CM.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN LY_Sales LY ON LY.CustomerID = MD.CustomerID AND LY.SalesOfficeID = MD.SalesOfficeID AND LY.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN LQ_Sales LQ ON LQ.CustomerID = MD.CustomerID AND LQ.SalesOfficeID = MD.SalesOfficeID AND LQ.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN LW_Sales LW ON LW.CustomerID = MD.CustomerID AND LW.SalesOfficeID = MD.SalesOfficeID AND LW.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN TW_Sales TW ON TW.CustomerID = MD.CustomerID AND TW.SalesOfficeID = MD.SalesOfficeID AND TW.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN Last_Order_Date D ON D.CustomerID = MD.CustomerID AND D.SalesOfficeID = MD.SalesOfficeID AND D.ProductHeirachy1 = MD.ProductHeirachy1
-- LEFT JOIN SalesOffice_Master_Dedup SO ON SO.PLANT = MD.SalesOfficeID
-- LEFT JOIN SE_Mapping M ON M.CustomerID = MD.CustomerID AND M.rn = 1
-- LEFT JOIN Customer_Master_Dedup C ON C.CustomerID = MD.CustomerID

-- -- Ensures lost volume from Last Year is included so YoY pulls into the negative correctly
-- WHERE ISNULL(LM.Avg_Daily_Sales_Last_Month, 0) > 0.0001 
--    OR ISNULL(CM.MTD_Avg_Daily_Sales, 0) > 0.0001
--    OR ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) > 0.0001
--    OR ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0) > 0.0001















;WITH Base_Sales AS (
    SELECT
        BillingDate,
        CustomerID,
        CustomerGroup, 
        SalesOfficeID,
        ProductHeirachy1,
        SalesQuantity
    FROM [HeritageBI].[DW].[fSales] (NOLOCK)
    WHERE BillingDate >= '2023-01-01' 
      AND CustomerID NOT LIKE '%O%'
      AND ProductHeirachy1 IN ('Milk','Curd','ButterMilk')
),

-- ===================== LATEST CUSTOMER GROUP (DEDUPLICATION) =====================
Latest_Customer_Group AS (
    SELECT CustomerID, CustomerGroup
    FROM (
        SELECT CustomerID, CustomerGroup,
            ROW_NUMBER() OVER(PARTITION BY CustomerID ORDER BY BillingDate DESC) as rn
        FROM Base_Sales
        WHERE CustomerGroup IS NOT NULL 
    ) t
    WHERE rn = 1
),

-- ===================== MASTER DIMENSIONS =====================
-- Anchor to ensure no customers are dropped if they didn't buy this exact month
Master_Dimensions AS (
    SELECT DISTINCT CustomerID, SalesOfficeID, ProductHeirachy1
    FROM Base_Sales
),

-- ===================== LAST MONTH (FULL) =====================
Last_Month AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / DAY(EOMONTH(DATEADD(MONTH, -1, CAST(GETDATE() AS DATE)))) AS Avg_Daily_Sales_Last_Month
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)) - 1, 0)
      AND BillingDate <  DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0)
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== LAST MONTH TILL DATE =====================
LMTD_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / NULLIF(DAY(DATEADD(DAY, -1, CAST(GETDATE() AS DATE))), 0) AS Avg_Daily_Sales_LMTD
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)) - 1, 0)
      AND BillingDate <  DATEADD(MONTH, -1, CAST(GETDATE() AS DATE))
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== CURRENT MONTH MTD =====================
CM_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / NULLIF(DAY(DATEADD(DAY, -1, CAST(GETDATE() AS DATE))), 0) AS MTD_Avg_Daily_Sales
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0)
      AND BillingDate <  CAST(GETDATE() AS DATE)
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== SAME MONTH LAST YEAR =====================
LY_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / DAY(EOMONTH(DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)))) AS Avg_Daily_Sales_Same_Month_Last_Year
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0))
      AND BillingDate <  DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)) + 1, 0))
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== SAME MONTH LAST YEAR TILL DATE =====================
LYMTD_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / NULLIF(DAY(DATEADD(DAY, -1, CAST(GETDATE() AS DATE))), 0) AS LYMTD_Avg_Daily_Sales
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(YEAR, -1, DATEADD(MONTH, DATEDIFF(MONTH, 0, CAST(GETDATE() AS DATE)), 0))
      AND BillingDate <  DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== LAST QUARTER =====================
LQ_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / DATEDIFF(DAY, DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)) - 1, 0), DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)), 0)) AS Avg_Daily_Sales_Last_Quarter
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)) - 1, 0)
      AND BillingDate <  DATEADD(QUARTER, DATEDIFF(QUARTER, 0, CAST(GETDATE() AS DATE)), 0)
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== LAST WEEK =====================
LW_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / 7 AS Avg_Daily_Sales_Last_Week
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)) - 1, 0)
      AND BillingDate <  DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)), 0)
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== CURRENT WEEK =====================
TW_Sales AS (
    SELECT
        CustomerID, SalesOfficeID, ProductHeirachy1,
        SUM(SalesQuantity) * 1.0 / NULLIF(DATEDIFF(DAY, DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)), 0), CAST(GETDATE() AS DATE)), 0) AS Avg_Daily_Sales_Current_Week
    FROM Base_Sales
    WHERE BillingDate >= DATEADD(WEEK, DATEDIFF(WEEK, 0, CAST(GETDATE() AS DATE)), 0)
      AND BillingDate <  CAST(GETDATE() AS DATE)
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== LAST ORDER DATE =====================
Last_Order_Date AS (
    SELECT CustomerID, SalesOfficeID, ProductHeirachy1, MAX(BillingDate) AS Last_Order_Date
    FROM Base_Sales
    GROUP BY CustomerID, SalesOfficeID, ProductHeirachy1
),

-- ===================== DEDUPLICATED DIMENSIONS =====================
SE_Mapping AS (
    SELECT DISTINCT CustomerID, Employee_ID, Employee_Name, Employee_Mobile
    FROM [HeritageIT].[S&D].[Cust_SE_Mapping]
    WHERE Division != 4 
),
Customer_Master_Dedup AS (
    SELECT CustomerID, CustomerName
    FROM (
        SELECT CustomerID, CustomerName, ROW_NUMBER() OVER(PARTITION BY CustomerID ORDER BY CustomerName DESC) as rn
        FROM [HeritageBI].[DW].[dCustomer]
    ) c WHERE rn = 1
),
SalesOffice_Master_Dedup AS (
    SELECT PLANT, STATE, REGION_NAME, PLANT_NAME, Short_Name
    FROM (
        SELECT PLANT, STATE, REGION_NAME, PLANT_NAME, Short_Name, ROW_NUMBER() OVER(PARTITION BY PLANT ORDER BY PLANT_NAME DESC) as rn
        FROM [HeritageBI].[DW].[dsalesofficemaster]
    ) s WHERE rn = 1
)

-- ===================== FINAL SELECT =====================
SELECT
    SO.STATE                                        AS State,
    SO.REGION_NAME                                  AS Region,
    SO.PLANT_NAME,
    SO.Short_Name                                   AS SO_Name,
    MD.SalesOfficeID                                AS SO,
    MD.CustomerID,
    C.CustomerName,
    LCG.CustomerGroup,                              
    M.Employee_ID                                   AS SE_EmpID,
    M.Employee_Name                                 AS SE_Name,
    M.Employee_Mobile                               AS SE_Mobile,
    MD.ProductHeirachy1                             AS Product,
    
    ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0) AS LYSM,
    ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0)             AS LYMTD,
    ISNULL(LQ.Avg_Daily_Sales_Last_Quarter, 0)         AS LQ,
    ISNULL(LM.Avg_Daily_Sales_Last_Month, 0)           AS LM,
    ISNULL(LMTD.Avg_Daily_Sales_LMTD, 0)               AS LMTD,
    ISNULL(CM.MTD_Avg_Daily_Sales, 0)                  AS MTD,
    ISNULL(LW.Avg_Daily_Sales_Last_Week, 0)            AS LW,
    ISNULL(TW.Avg_Daily_Sales_Current_Week, 0)         AS CW,

    ROUND(ISNULL(LM.Avg_Daily_Sales_Last_Month, 0) - ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0), 2) AS YoY_Abs_LPD_Diff,
    ROUND(ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LMTD.Avg_Daily_Sales_LMTD, 0), 2) AS MTD_vs_LMTD_Abs_LPD_Diff,
    ROUND(ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0), 2) AS MTD_vs_LYMTD_Abs_LPD_Diff,

    CASE
        WHEN ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) = 0 AND ISNULL(CM.MTD_Avg_Daily_Sales, 0) > 0 THEN 'New Customer'
        WHEN ISNULL(CM.MTD_Avg_Daily_Sales, 0) = 0 AND ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) > 0 THEN 'Decline'
        WHEN ISNULL(CM.MTD_Avg_Daily_Sales, 0) > ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) THEN 'Growth'
        WHEN ISNULL(CM.MTD_Avg_Daily_Sales, 0) < ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) THEN 'Decline'
        ELSE 'Stagnant'
    END AS Sales_Trend,

    ROUND((ISNULL(LM.Avg_Daily_Sales_Last_Month, 0) - ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0)) / NULLIF(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0), 4) AS YoY_Growth_Percentage,
    ROUND((ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LMTD.Avg_Daily_Sales_LMTD, 0)) / NULLIF(LMTD.Avg_Daily_Sales_LMTD, 0), 4) AS MTD_vs_LMTD_Growth_Percentage,
    ROUND((ISNULL(CM.MTD_Avg_Daily_Sales, 0) - ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0)) / NULLIF(LYMTD.LYMTD_Avg_Daily_Sales, 0), 4) AS MTD_vs_LYMTD_Growth_Percentage,
    D.Last_Order_Date

FROM Master_Dimensions MD
LEFT JOIN Latest_Customer_Group LCG ON LCG.CustomerID = MD.CustomerID
LEFT JOIN Last_Month LM ON LM.CustomerID = MD.CustomerID AND LM.SalesOfficeID = MD.SalesOfficeID AND LM.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN LYMTD_Sales LYMTD ON LYMTD.CustomerID = MD.CustomerID AND LYMTD.SalesOfficeID = MD.SalesOfficeID AND LYMTD.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN LMTD_Sales LMTD ON LMTD.CustomerID = MD.CustomerID AND LMTD.SalesOfficeID = MD.SalesOfficeID AND LMTD.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN CM_Sales CM ON CM.CustomerID = MD.CustomerID AND CM.SalesOfficeID = MD.SalesOfficeID AND CM.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN LY_Sales LY ON LY.CustomerID = MD.CustomerID AND LY.SalesOfficeID = MD.SalesOfficeID AND LY.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN LQ_Sales LQ ON LQ.CustomerID = MD.CustomerID AND LQ.SalesOfficeID = MD.SalesOfficeID AND LQ.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN LW_Sales LW ON LW.CustomerID = MD.CustomerID AND LW.SalesOfficeID = MD.SalesOfficeID AND LW.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN TW_Sales TW ON TW.CustomerID = MD.CustomerID AND TW.SalesOfficeID = MD.SalesOfficeID AND TW.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN Last_Order_Date D ON D.CustomerID = MD.CustomerID AND D.SalesOfficeID = MD.SalesOfficeID AND D.ProductHeirachy1 = MD.ProductHeirachy1
LEFT JOIN SalesOffice_Master_Dedup SO ON SO.PLANT = MD.SalesOfficeID
LEFT JOIN SE_Mapping M ON M.CustomerID = MD.CustomerID 
LEFT JOIN Customer_Master_Dedup C ON C.CustomerID = MD.CustomerID

-- Ensures lost volume from Last Year is included so YoY pulls into the negative correctly
WHERE ISNULL(LM.Avg_Daily_Sales_Last_Month, 0) > 0.0001 
   OR ISNULL(CM.MTD_Avg_Daily_Sales, 0) > 0.0001
   OR ISNULL(LYMTD.LYMTD_Avg_Daily_Sales, 0) > 0.0001
   OR ISNULL(LY.Avg_Daily_Sales_Same_Month_Last_Year, 0) > 0.0001
ORDER BY MTD_vs_LYMTD_Abs_LPD_Diff;