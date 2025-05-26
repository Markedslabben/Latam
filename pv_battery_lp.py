# pv_battery_lp.py
import pandas as pd
from pyomo.environ import (ConcreteModel, Set, Param, Var,
                           NonNegativeReals, maximize, Constraint, Objective,
                           SolverFactory)

# --------------------------------------------------------------------
# 1  Data -------------------------------------------------------------
# --------------------------------------------------------------------
df = pd.read_csv("timeseries.csv")       # production [MWh], price [NOK/MWh]
T_list = df.index.tolist()               # [0 … 8759]  (0-basert fra pandas)

param_prod  = df["production"].to_dict() # P[t]
param_price = df["price"].to_dict()      # π[t]

# Batteriparametre
C      = 0.5 * 120.0     # [MWh] = 60 MWh
eta_c  = 1.0             # lading  (hold 1,0 for LP uten tap)
eta_d  = 1.0             # uttak
P_cmax = 60            # [MW] sett tall om du vil ha effektgrense
P_dmax = 60            # [MW] "
S0     = 0.0             # start-SoC [MWh]
fix_final_soc = True     # True → S[8760] = S0

# --------------------------------------------------------------------
# 2  Modell -----------------------------------------------------------
# --------------------------------------------------------------------
m = ConcreteModel()

m.T = Set(initialize=T_list, ordered=True)

# ---- Parametre -----------------------------------------------------
m.P      = Param(m.T, initialize=param_prod,  within=NonNegativeReals)  # PV-produksjon
m.price  = Param(m.T, initialize=param_price)                           # Spotpris

# ---- Variabler -----------------------------------------------------
m.c = Var(m.T, within=NonNegativeReals)               # lading  [MWh]
m.d = Var(m.T, within=NonNegativeReals)               # uttak   [MWh]
m.S = Var(m.T, within=NonNegativeReals, bounds=(0, C))# SoC     [MWh]

# ---- Hjelpefunksjon ------------------------------------------------
def prev_t(t):
    """Finner forrige element i den ordnede tidsmengden."""
    idx = m.T.ord(t)
    if idx == 1:          # første element har indeks 1
        return None
    return m.T[idx - 1]

# ---- Restriksjon 1: PV-balanse ------------------------------------
def pv_balance_rule(m, t):
    return m.c[t] <= m.P[t]          # c[t] ≤ P[t]  (resten selges direkte)
m.pv_balance = Constraint(m.T, rule=pv_balance_rule)

# ---- Restriksjon 2: Batteridynamikk -------------------------------
def soc_rule(m, t):
    t_prev = prev_t(t)
    if t_prev is None:               # time 0
        return m.S[t] == S0 + eta_c * m.c[t] - (1/eta_d) * m.d[t]
    return m.S[t] == m.S[t_prev] + eta_c * m.c[t] - (1/eta_d) * m.d[t]
m.soc = Constraint(m.T, rule=soc_rule)

# ---- Objektfunksjon: Maksimer eksportinntekt ----------------------
def obj_rule(m):
    return sum(m.price[t] * (m.P[t] - m.c[t] + m.d[t]) for t in m.T)
m.obj = Objective(rule=obj_rule, sense=maximize)
