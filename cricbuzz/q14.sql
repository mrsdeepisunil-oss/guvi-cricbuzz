SELECT 
    venue,
    bowler_name,
    COUNT(DISTINCT match_id) AS matches_played,
    SUM(wickets) AS total_wickets_taken,
    -- We cast the division result to numeric so ROUND can process it
	-- Economy Rate = (Total Runs Conceded) / (Total Overs Bowled)
    ROUND((SUM(runs) / NULLIF(SUM(overs), 0))::numeric, 2) AS average_economy_rate
FROM public.q14_bowler_perf
WHERE overs >= 4  -- Focus on bowlers with at least 4 overs per match
GROUP BY venue, bowler_name
ORDER BY total_wickets_taken DESC, average_economy_rate ASC;