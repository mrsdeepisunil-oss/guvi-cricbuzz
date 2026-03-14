SELECT result_short AS team, COUNT(*) AS wins
FROM public.q22_test
GROUP BY result_short;