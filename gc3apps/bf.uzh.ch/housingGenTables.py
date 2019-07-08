import os
import re
import shutil
import sys

import numpy as np

import gc3libs.application.apppot
import gc3libs.debug
import logbook
from gc3libs import Application, Run
from paraLoop import paraLoop
from plotAggregate import makeAggregatePlot
from plotSimulation import plotSimulation
from pymods.classes.tableDict import tableDict
from pymods.support.support import getParameter
from supportGc3 import (
    extractVal,
    flatten,
    format_newVal,
    getIndex,
    getParameter,
    lower,
    mat2str,
    safe_eval,
    str2mat,
    str2tuple,
    str2vals,
    update_parameter_in_file,
    wrapLogger,
)

# import personal libraries
path2SrcPy = os.path.join("../src")
if not sys.path.count(path2SrcPy):
    sys.path.append(path2SrcPy)

path2Pymods = os.path.join("../")
if not sys.path.count(path2Pymods):
    sys.path.append(path2Pymods)


output_dir = "/home/jonen/workspace/housingproj/model/results/newMchain/finePsi/DE/para_ctry=de_psi=0.0380000000_R_UL=1.0600000000_updateCtryParametersFile=1/output"
aggregateOut = os.path.join(output_dir, "aggregate.out")
empOwnershipFile = os.path.join(os.path.split(output_dir)[0], "input", "SOEP" + "OwnershipProfilealleduc.out")
ownershipTableFile = os.path.join(output_dir, "ownershipTable.out")
if os.path.exists(aggregateOut):
    # make plot of predicted vs empirical ownership profile
    aggregateOutTable = tableDict.fromTextFile(aggregateOut, width=20, prec=10)
    aggregateOutTable.keep(["age", "owner"])
    aggregateOutTable.rename("owner", "thOwnership")
    empOwnershipTable = tableDict.fromTextFile(empOwnershipFile, width=20, prec=10)
    empOwnershipTable.rename("PrOwnership", "empOwnership")
    print(empOwnershipTable)
    #    print(empOwnershipTable.cellFormat)

    ownershipTable = aggregateOutTable.merged(empOwnershipTable, "age")
    print(ownershipTable)
    #    print(ownershipTable.cellFormat)

    yVars = ["thOwnership", "empOwnership"]
    # add the individual simulations
    for profile in ["1", "2", "3"]:
        profileOwnershipFile = os.path.join(output_dir, "simulation_" + profile + ".out")
        if not os.path.exists(profileOwnershipFile):
            continue
        profileOwnershipTable = tableDict.fromTextFile(profileOwnershipFile, width=20, prec=10)
        profileOwnershipTable.keep(["age", "owner"])
        profileOwnershipTable.rename("owner", "thOwnership_" + profile)
        ownershipTable.merge(profileOwnershipTable, "age")
        ownershipTable.drop("_merge")
print(ownershipTable)
f = open(ownershipTableFile, "w")
print(ownershipTable, file=f)
f.close()
plotSimulation(
    table=ownershipTableFile,
    xVar="age",
    yVars=yVars,
    yVarRange=(0.0, 1.0),
    figureFile=os.path.join(output_dir, "ownership.png"),
    verb="CRITICAL",
)
# make plot of life-cycle simulation (all variables)
makeAggregatePlot(output_dir)
