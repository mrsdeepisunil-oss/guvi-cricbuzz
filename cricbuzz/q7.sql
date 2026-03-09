SELECT 'ODI' AS format, MAX(runs) AS highest_score
FROM odi

UNION ALL

SELECT 'Test' AS format, MAX(runs) AS highest_score
FROM test_mat

UNION ALL

SELECT 'T20I' AS format, MAX(runs) AS highest_score
FROM t20_mat;