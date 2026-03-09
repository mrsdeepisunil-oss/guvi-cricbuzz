SELECT match_id,
    innings_id,
	p1.bat1_name AS Player_1,
    p1.bat2_name AS Player_2,
    (p1.bat1_runs + p1.bat2_runs) AS combined_partnership_runs,
    p1.innings_id
FROM public.scard_partner p1
WHERE (p1.bat1_runs + p1.bat2_runs) >= 100;