SELECT 
    player_name, 
    year, -- This is an INTEGER
    ROUND(AVG(runs), 2) AS avg_runs -- AVG returns DOUBLE PRECISION, ROUND makes it readable
FROM 
    public.q16_test
GROUP BY 
    player_name, year;