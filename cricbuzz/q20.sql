WITH player_stats AS (
    SELECT 
        o.playerid,
        o.player AS player_name,

        COALESCE(tm.matches::int, 0) AS test_matches,
        COALESCE(o.matches::int, 0) AS odi_matches,
        COALESCE(t2.matches::int, 0) AS t20_matches,

        tm.avg::numeric AS test_avg,
        o.avg::numeric AS odi_avg,
        t2.avg::numeric AS t20_avg

    FROM public.odi o
    LEFT JOIN public.test_mat tm 
        ON o.playerid = tm.playerid
    LEFT JOIN public.t20_mat t2
        ON o.playerid = t2.playerid
)
public.q20_diff_match
SELECT *,
       (test_matches + odi_matches + t20_matches) AS total_matches
FROM player_stats
WHERE (test_matches + odi_matches + t20_matches) >= 20;