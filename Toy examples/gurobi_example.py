# Toy example given by gurobi

from gurobipy import *

try:
    # create a new model
    m = Model("mip1")

    # create variables
    x = m.addVar(vtype=GRB.BINARY, name="x")
    y = m.addVar(vtype=GRB.BINARY, name="y")
    z = m.addVar(vtype=GRB.BINARY, name="z")

    # Establish objective

    m.setObjective(x+y+2*z, GRB.MAXIMIZE)

    # Add constraint 1
    m.addConstr(x+2*y+3*z<=4,"c0")
    # Add constraint 2
    m.addConstr(x+y>=1,"c1")
    m.optimize()
    for v in m.getVars():
        print(v.varName,v.x)
    print('Obj:', m.objVal)
    
except GurobiError:
    print('Error reported')