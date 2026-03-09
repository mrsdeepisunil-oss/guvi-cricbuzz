CREATE TABLE q_player_roles AS
SELECT 
    CASE 
        WHEN playingrole ILIKE '%Batsman%' THEN 'Batsman'
        WHEN playingrole ILIKE '%Bowler%' THEN 'Bowler'
        WHEN playingrole ILIKE '%Wicket keeper%' THEN 'Wicket keeper'
        ELSE 'All rounder' 
    END AS simplified_role,
    COUNT(*) AS player_count
FROM players_india
GROUP BY simplified_role
ORDER BY player_count DESC;