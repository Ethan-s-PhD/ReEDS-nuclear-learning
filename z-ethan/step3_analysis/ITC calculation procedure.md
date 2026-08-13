Scope. This procedure calculates the required ITC rate for each year of one sequential ReEDS run. All values come from the run inputs and the run outputs. The solve is sequential. Each year's LP prices its own builds fully. Because of this, the procedure does not discount across years.

Step 1 — Check the baseline.

- Open inputs_case/itc_frac_monetized.csv. Make sure that the file has no rows for Nuclear or Nuclear-SMR.
- Make sure that inv_itc_payments_negative is zero for nuclear in all years.
- Make sure that cost_cap_fin_mult is equal to cost_cap_fin_mult_noITC for nuclear in all years.
- If all checks pass, the dual is the total required support.
- If a check fails, the run already contains a credit. Then the dual is only the additional required support, and you must change Step 6: solve for the difference between two fin_mult values.

Step 2 — Read the duals.

- For each solve year, read the raw dual and the converted dual of the floor constraint from the h5 file.
- If a dual parameter is not in the h5 file, its value is zero. It is not missing data.
- For the equality case, also read the ceiling dual. Use the net value: floor dual minus ceiling dual.

Step 3 — Select the years.

- Include a year in the ITC schedule only if three conditions are true: the dual is positive, the mandate increases in that year, and cap_new_ann of the mandated technology is positive in that year.
- The third condition is necessary. The model can hold the floor with old units that it keeps in service. Then the dual prices the loss of the marginal old unit, not the gap of a new build. An ITC on new builds is the wrong instrument for that dual. This condition applies to the early years of the large100 cases.
- If the floor constraint is slack, the dual is zero. The required ITC is zero. Report this as a result.
- If the mandate does not increase in a year, and existing capacity satisfies the floor, no build receives a credit. Remove that year from the schedule.

Step 4 — Calculate the subsidy S_t.

- Calculate S_t with two methods:
- S_t = raw dual / cost_scale.
- S_t = converted dual × pvf_onm. Use the pvf_onm value from the run. pvf_onm = 1/crf.
- Make sure that the two results are equal. If they are not equal, there is a units error.
- Note: the two methods obey one identity that the QA notebook already verified. Thus this check finds units errors only. It does not test the logic of S_t.
- S_t is in 2004 dollars per MW. S_t is the capitalized cost of the marginal build in year t, minus the capitalized market value of that build. S_t includes capital cost, fixed O&M, and variable costs.

Step 5 — Select the capex base.

- The ITC must supply S_t to the marginal build.
- The capex base of a build is OCC × reg_cap_cost_diff for its region and year.
- The run output does not identify the marginal region, because many regions have almost equal costs (result P7).
- Because of this, calculate one implied rate for each region that builds in year t. Report the range of rates.
- If you must report one rate, use the maximum of the range. The maximum rate is enough for the last mandated MW.

Step 6 — Calculate the ITC rate.

- Solve this equation for the monetized fraction m_t: OCC × [fin_mult_noITC − fin_mult(m_t)] = S_t.
- Use the replicated fin_mult function from the notebook. This function includes the monetization loss, the reduction of the depreciation basis, and the construction financing multiplier (ccmult).
- The code source is reeds/financials.py, lines 683-694: fin_mult(m) = CCmult / (1 − tax) × [1 − tax × (1 − m/2) × PV_dep − m] × Degradation_Adj.
- fin_mult is a linear function of m. So the solution is: m_t = S_t / (OCC × |d fin_mult / d m|), with |d fin_mult / d m| = CCmult / (1 − tax) × (1 − tax × PV_dep / 2) × Degradation_Adj.
- Note: |d fin_mult / d m| is larger than fin_mult_noITC. One dollar of credit gives more than one dollar of support, because of the tax grossup. The depreciation basis decreases by half of the credit, and this decreases the support a little.
- The rate m_t is the monetized fraction. The statutory rate is i_t = m_t / (1 − itc_tax_equity_penalty). Read the penalty from the incentives input file.
- Report the statutory rate i_t. Compare only statutory rates with the law (48E, OBBBA).
- Use the same dollar year for S_t and OCC. The rate has no units, so the dollar year cancels.
- If i_t is more than 100%, an ITC alone cannot supply S_t in that year. An operating subsidy must supply the remainder. Report this as a result.

Step 7 — Assign solve years to build years.

- ReEDS solves at discrete solve years. Each solve year represents a group of calendar years.
- Apply the rate i_t to all builds in the group of years for solve year t.
- Write this assignment rule one time. Use the same rule in all fiscal calculations.

Step 8 — Calculate the fiscal outputs.

- This procedure makes two different fiscal quantities. Keep the two names separate in all outputs.
- ITC outlay: B_t = i_t × (sum of the capex bases of all nuclear builds in year t). All builds receive the credit, not only the marginal build. B_t is the cost of the ITC instrument.
- Rental transfer: R_t = dual × mandated capacity in year t. R_t is the implicit transfer of the mandate itself. R_t pays all mandated capacity across vintages. B_t and R_t measure different objects, and their values differ.
- Transfer inside one year: for each build, calculate the payment minus the required support of that build. Get the required support from the replicated regional cost data. A build with required support less than S_t is inframarginal. The transfer share is the sum of the excess payments divided by B_t.
- Note: the required support per build uses regional cost data only. It does not include regional differences in market value. Result P7 shows that these value differences are small in the regions that build. State this approximation in the output.
- Multiply dollar values by 1.6590 to convert 2004 dollars to 2024 dollars. Do not convert the rates.

Step 9 — Do the checks.

- Make sure that the two S_t methods agree (Step 4).
- Make sure that the range of implied rates is narrow (Step 5).
- Examine the shape of the rate schedule. If learning decreases the costs of later builds, the rates must decrease across years.
- Compare the statutory rates with real credit values (48E, OBBBA).
- Final test: run the model with the ITC schedule and without the mandate. Compare the deployment with the mandated deployment. Two cautions apply. First, at exactly i_t the model is indifferent between build and no build. Add a small amount to i_t to make the builds strictly optimal. Second, with endogenous learning on, the problem is not convex. The ITC can then fail to reproduce the deployment. This possible failure is a pre-registered finding, not an error.

Companion value. For each build year, also calculate the discounted sum of the converted duals over the build's full evaluation window (30 years). This value is the support that an investor with full foresight requires. This value does not control the sequential model. Report both values. The difference between the two values is an effect of the myopic solve, and it is a result for the paper.

The model stops at 2050, but the window of a late build extends past 2050. A cut at 2050 makes the companion value fall toward zero near 2050. That fall is an effect of the horizon, not of the costs. Because of this, extend the dual path past 2050 in two ways, and report both results:

- Cut: the dual is zero after 2050. This is the lower boundary.
- Hold: the dual after 2050 keeps its 2050 value through the window. This follows the bokehpivot convention, which continues operational values past the horizon.

The two results bracket the post-2050 assumption. Read only conclusions that hold across the band. Check one identity: with the hold path, the companion value at a 2050 build must come near S_2050, because both hold 30 years of the 2050 dual.
