from run_simulation import main
a=[]
for year in range(2013,2025):
    main(year)
    a.append(sim_res-aep().sum().values)
    a.append(year)
    print(a)
