SELECT result_short, COUNT(*) AS number_of_wins
FROM public.q22_test
GROUP BY result_short;