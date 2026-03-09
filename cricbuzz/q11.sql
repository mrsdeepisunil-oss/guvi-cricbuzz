/*COALESCE returns the first non-null value from a list of arguments*/

SELECT 
    COALESCE(t.player, o.player, t20.player) AS "Player Name",
    COALESCE(t.runs::integer, 0) AS "Test Runs",
    COALESCE(o.runs::integer, 0) AS "ODI Runs",
    COALESCE(t20.runs::integer, 0) AS "T20 Runs",
    -- Calculation logic
    ROUND(
        (COALESCE(t.runs::integer, 0) + COALESCE(o.runs::integer, 0) + COALESCE(t20.runs::integer, 0))::numeric / 
        NULLIF((COALESCE(t.innings::integer, 0) + COALESCE(o.innings::integer, 0) + COALESCE(t20.innings::integer, 0)), 0), 
    2) AS "Overall Average"
FROM test_mat t
FULL OUTER JOIN odi o ON t.playerid = o.playerid
-- Match the alias 't20' here so the SELECT clause above can find it
FULL OUTER JOIN t20_mat t20 ON COALESCE(t.playerid, o.playerid) = t20.playerid
WHERE 
    (CASE WHEN t.playerid IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN o.playerid IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN t20.playerid IS NOT NULL THEN 1 ELSE 0 END) >= 2
ORDER BY "Overall Average" DESC;