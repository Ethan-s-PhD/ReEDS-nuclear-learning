# External reference values for paper AG

An agent collected these values on 2026-10-28. Each value traces to a source in `sources.csv`. The agent opened every source marked `opened = yes` in that session. No value comes from memory. No value is interpolated or converted.

## Files

| File | Content |
|---|---|
| `sources.csv` | One row per source (S01-S28). The row gives the title, the agency or authors, the year, the URL, the open status, and the table or page that holds the value. |
| `sc_ghg_epa2023.csv` | EPA 2023 SC-CO2, SC-CH4 and SC-N2O for each emission year 2020-2080 at near-term rates of 1.5%, 2.0% and 2.5%. The file holds 549 rows. The values are the unrounded values of Table A.5.1, in 2020 dollars per metric ton of each gas. |
| `sc_co2_domestic.csv` | Domestic (US-only) SC-CO2 estimates. The rows cover the 2019 EPA interim domestic values (2016$, 3% and 7%, 2015-2050) and the partial US values in the EPA 2023 report (2020$, 2.0%). |
| `discount_rates.csv` | The rates that Circular A-4 (2003 and 2023), Circular A-94 (1992), the 2026 A-94 Appendix C and the EPA SC-GHG report prescribe. Each row also gives its status in 2026. |
| `mcpf.csv` | Two marginal-cost-of-public-funds values for US federal taxation. |
| `foreign_ownership.csv` | Partial evidence on foreign ownership. All five rows are economy-wide or dated proxies (see Gaps). |
| `aeo_gas_nonpower.csv` | AEO2026 natural gas consumption by sector, 2025-2050, in trillion cubic feet. |
| `aeo_gas_delivered_prices.csv` | AEO2026 delivered natural gas prices by sector and the Henry Hub spot price, 2025-2050, in 2025 dollars. |
| `aeo2026_cb2026_aeotab13.xlsx` | The unmodified EIA file for AEO2026 Table 13, kept as provenance. |
| `aeo_gas_nonpower_quads.csv` | AEO2026 natural gas consumption by sector, 2025-2050, in quadrillion Btu (Table 2). |
| `gas_heat_content.csv` | The heat content implied by AEO2026 (Btu per cubic foot, by sector, 2025-2050) and the MER Table A4 historical values (2019-2026). |
| `aeo2026_cb2026_aeotab2.xlsx` | The unmodified EIA file for AEO2026 Table 2. |
| `gdp_deflator_bea.csv` | The BEA GDP implicit price deflator (2017 = 100) for 2016, 2017, 2020 and 2023-2025. It is included for dollar-year conversion. |

## Item 1: Social cost of greenhouse gases (EPA 2023)

**Values.** EPA reports SC-CO2 for 2025 emissions as $130, $212 and $360 per metric ton at near-term rates of 2.5%, 2.0% and 1.5% (2020 dollars). For 2050 emissions the values are $205, $308 and $482. EPA's central rate is 2.0%. A near-term Ramsey rate is the starting rate of a discount path that declines over time; it is not a constant rate.

**Dollar year.** All EPA 2023 values are in 2020 dollars. The analysis needs 2025 dollars. The BEA deflator ratio 2025/2020 is 128.893 / 105.377 = 1.2232. The CSV values are not converted.

**Policy status in 2026.** EPA's 2023 estimates are no longer federal policy.
- Executive Order 14154 (Jan 20, 2025), Sec. 6(b), disbands the Interagency Working Group (IWG) on the SC-GHG. It withdraws the IWG's February 2021 technical support document. It also withdraws "estimates of the social cost of greenhouse gases ... based, in whole or in part, on the IWG's work". EPA's 2023 estimates fall under that wording, but the EO does not name the 2023 EPA report. (S02)
- EO 14154 Sec. 6(d) tells agencies to follow the 2003 Circular A-4 on domestic versus international effects and on discount rates. (S02)
- OMB memorandum M-25-27 (May 5, 2025) says it is "no longer Federal government policy to maintain a uniform estimate" of monetized GHG impacts. It says agencies will need monetized GHG analysis in "few to none" cases. It limits any GHG consideration to domestic effects. Item 7 tells agencies not to monetize GHG impacts at all. (S03)
- EPA's SC-GHG web page returned HTTP 404 on 2026-10-28. The PDF of the 2023 report remains downloadable. (S05, S01)
- The Harvard EELP tracker (updated Jan 30, 2026) lists no replacement estimate. It lists EPA's Mar 12, 2025 announcement that it would revisit the estimates. It also lists the DOE Climate Working Group report (Jul 29, 2025) and a Jan 30, 2026 court ruling that this group violated FACA, the federal advisory-committee law. (S04)
- EPA rescinded the 2009 endangerment finding in a final rule (91 FR 7686, Feb 18, 2026). This is context only. The agent read a law-firm summary, not the Federal Register text. (S07)

**What federal agencies use now.** The agent found no federal SC-GHG value in current use. Current guidance tells agencies not to monetize GHG effects (M-25-27). Where a statute requires analysis, the guidance limits it to domestic effects under the 2003 A-4.

## Item 2: Domestic-only SC-CO2

- **No 2025-2026 federal domestic value exists.** Neither EO 14154 nor M-25-27 publishes a number, and the agent found no later agency value.
- **The best-documented federal domestic series** is EPA's 2019 interim domestic SC-CO2, developed under E.O. 13783. Table 4-1 of the 2019 ACE/CPP-repeal RIA lists it. For 2025 emissions it is $7/tCO2 at 3% and $1/tCO2 at 7%. For 2050 it is $11 and $2. All values are in 2016 dollars and rounded to the nearest dollar. The series uses the 2010-era IWG model ensemble (DICE, FUND, PAGE). E.O. 13990 superseded it in 2021. (S08)
- **EPA 2023 partial US values** cover only damages that occur physically inside the US. All use the 2.0% near-term rate and 2020 dollars. DSCIM gives $14 (2030) and $27 (2080). GIVE gives $16 (2030) and $24 (2080). FrEDI gives $37 (2030, contiguous US only). EPA states that these values are not equivalent to US benefits. They omit many damage categories, the US territories and spillovers from abroad. (S01, pp. 95-97)
- **Ricke et al. (2018)** report a US country-level SCC of $48/tCO2 (SSP2-RCP6.0, Ramsey ρ = 2%, η = 1.5). This value comes from EPA's summary (S01 p. 98). The agent did not open the paper, and EPA's text gives neither its emission year nor its dollar year. (S09)

## Item 3: Social discount rate

- **2003 Circular A-4** prescribes net-benefit estimates at both 3% and 7% real. The 3% rate is the consumption rate of interest. The 7% rate is the average before-tax return to private capital. For intergenerational effects, A-4 cites 1990s estimates of 1-3% and suggests an added sensitivity analysis with a lower rate. (S10, pp. 33-36)
- **2023 Circular A-4** prescribes a default of 2.0% real. OMB derived 2.0% as the 30-year average real 10-year Treasury yield (1.7%) plus a 0.3% adjustment from CPI to PCE inflation. The 2023 A-4 handles capital effects with a shadow price of capital, not with a 7% rate. It took effect Mar 1, 2024 for proposed rules and Jan 1, 2025 for other final rules. (S11, pp. 76-77, 93)
- **Status.** OMB memorandum M-25-15 (Feb 12, 2025), issued under E.O. 14192, revokes the 2023 A-4 and reinstates the 2003 A-4. (S12) The OMB circulars page lists only the 2003 A-4 on 2026-10-28. (S26) **The 3%/7% pair is therefore current federal guidance.**
- **Circular A-94.** M-25-23 (Apr 8, 2025) revokes the 2023 A-94 and reinstates the 1992 A-94. (S15) The 1992 A-94 sets a 7% real base-case rate for public investment and regulatory benefit-cost analysis. (S13, p. 9) The 2026 Appendix C rates (real 10-year 1.6%, real 30-year 2.0%) apply only to cost-effectiveness and lease-purchase analysis. They are not regulatory discount rates. (S14)

## Item 4: Marginal cost of public funds (MCPF)

The MCPF is the social cost of raising one more dollar of tax revenue: one dollar plus the excess burden, the welfare loss that tax distortions cause.
- **OMB Circular A-94 (1992), Sec. 11:** excess burden of 25 cents per dollar, so MCPF = 1.25. A-94 requires a supplementary NPV with public expenditure multiplied by 1.25 for public investments not justified by cost savings. The 1992 A-94 is in force again (M-25-23). (S13)
- **Ballard, Shoven and Whalley (1985):** marginal excess burden centered around 33 cents per dollar (MCPF ≈ 1.33), with a range of 17-56 cents (1.17-1.56). The range depends on labor-supply and saving elasticities. The value comes from the summary in Fullerton and Henderson (1987, NBER WP 2353, p. 2). The agent saw only the AER article's abstract. (S16, S17)
- The 2023 A-4 (now revoked) told agencies generally not to apply an MCPF to analyses of individual regulations. (S11, pp. 60-61)
- **Dahlby (2008) was not opened.** The MIT Press page returned HTTP 403, so the file uses no Dahlby value. (S23)

## Item 5: Foreign ownership shares

The agent found **no sourced share specific to US electricity generating assets, utility equity or natural-gas production.** The file records only proxies:
- Foreign investors held 42% of total US corporate equity at the end of 2022. They held 32% of publicly traded US stock. Both shares are economy-wide. (S18, p. 94)
- Majority-owned US affiliates of foreign multinational enterprises produced 6.7% of US business-sector value added in 2024. They held 6.1% of private-industry employment. Both shares are economy-wide. (S19)
- Foreign joint ventures made up 20% of the $133.7 billion in shale-play deal investment in 2008-2012. This share measures an investment flow, not ownership of production, and it is dated. (S20)

**Limits.** BEA publishes affiliate data by industry, including utilities and oil and gas extraction, only in its interactive tables. Those tables need a browser session or an API key, and the agent opened neither. BEA's 2025 direct-investment release (S28) has no utilities line. EIA Form 860 lists plant owners but not their nationality.

## Item 6: AEO2026 natural gas

- **AEO2026 is published** (released Apr 8, 2026). EIA renamed the Reference case: AEO2026 calls it the **Counterfactual Baseline** case (scenario `cb2026`, NEMS run `cb2026.d021826b`). The case reflects laws and regulations as of December 2025. (S24, p. 3) The tables come from Table 13, "Natural Gas Supply, Disposition, and Prices". (S21)
- **Consumption (trillion cubic feet).** The non-power total (residential + commercial + industrial + transportation) is 20.29 in 2025, 20.11 in 2030, 21.26 in 2040 and 22.58 in 2050. The CSV gives each sector and component for every year.
- **Row structure.** "Industrial" (row_code 3) is a subtotal of three components: other industrial (3a), lease and plant fuel (3b) and hydrogen-production feedstock (3c). "Transportation" (row_code 4) is a subtotal of motor vehicles, trains and ships (4a), pipeline and distribution fuel (4b) and fuel to liquefy gas for export (4c). Add sector rows 1, 2, 3 and 4 only, never subtotals and components together. The derived row `NP` equals that sum. The build script checks that total consumption minus electric power equals `NP` in every year (tolerance 0.01 Tcf). Electric power (5) and total consumption (T) are included for reference.
- **Delivered prices (2025 dollars per thousand cubic feet).** In 2025: residential 15.23, commercial 10.75, industrial 4.68, transportation 17.82. In 2050: 16.02, 13.25, 5.61 and 15.78. Henry Hub is in 2025 dollars per MMBtu: 3.47 in 2025 and 4.64 in 2050. The industrial price excludes lease and plant fuel and liquefaction fuel. The transportation price covers vehicle fuel only and includes fuel taxes and dispensing costs. EIA gives no delivered price for lease and plant fuel or for pipeline fuel.
- **2025 column.** EIA's table footer cites STEO November 2025 as a data source. The 2025 values are therefore estimates, not projections.

## Item 6b: Natural gas in energy units (added 2026-10-28)

- **`aeo_gas_nonpower_quads.csv`** gives AEO2026 Table 2 natural gas consumption by sector in quadrillion Btu, 2025-2050, for the Counterfactual Baseline case. (S29) The raw file is saved as `aeo2026_cb2026_aeotab2.xlsx`.
- **Non-power total** (rows 1+2+3a+3b+3c+4a+4b+4c) is 21.06 quads in 2025, 20.87 in 2030 and 23.43 in 2050. The build script checks that Table 2's delivered natural gas subtotal plus the hydrogen-production gas row equals this sum in every year (tolerance 0.01 quad).
- **Row scope differs between the two tables.** Table 2 reports the gas used in hydrogen production in a separate section, "Industrial: Hydrogen Production". In Table 2 the industrial "natural gas" row excludes that gas. Table 13 splits the same gas differently: its "other industrial" row includes the gas used for heat and power in hydrogen production, and its hydrogen row holds only the feedstock. Rows 3a and 3c therefore do not match one to one across the tables. Their sum does match.
- **`gas_heat_content.csv`** gives the heat content implied by Table 2 quads divided by Table 13 Tcf, by sector and year. The implied values are constant over 2025-2050:
  - 1,038 Btu/cf for residential, commercial, industrial (other industrial plus hydrogen production, combined) and vehicle use;
  - 1,036 Btu/cf for lease and plant fuel, pipeline fuel and liquefaction fuel;
  - 1,033 Btu/cf for electric power;
  - 1,037.7 Btu/cf for the non-power total in 2025 (1,037.6 in 2050).
- The same file also gives EIA's historical heat content from Monthly Energy Review Table A4 (S30). Total consumption is 1,036 Btu/cf in 2025, the end-use sectors 1,037 and electric power 1,034. The MER 2026 annual entry may be preliminary.
- **Use.** The quads can be used directly, so no conversion factor is needed. To convert Tcf instead, multiply each sector's Tcf by its implied factor. This reproduces the Table 2 quads.

## Gaps and caveats

1. No federal SC-GHG value is in current use, and the agent found no 2025-2026 federal domestic SC-CO2 value.
2. The domestic estimates are not comparable to each other. They differ in models, damage coverage, discounting and dollar year. EPA calls its 2023 US values partial lower bounds on US benefits.
3. The Ricke et al. (2018) value is secondary (taken from S01). Its emission year and dollar year are unknown.
4. The MCPF has no recent US review value. The Ballard-Shoven-Whalley range is secondary (via S17), and Dahlby (2008) was not opened.
5. No industry-specific foreign-ownership share was found for US power assets, utility equity or gas production. The economy-wide equity share (42%) is the closest proxy. Using it for utilities or gas producers is an assumption.
6. AEO2026 renamed the Reference case to "Counterfactual Baseline". The CSVs label the source accordingly.
7. All SC-GHG values stay in their source dollar years (2020$ or 2016$). The analysis must convert them to 2025 dollars. `gdp_deflator_bea.csv` gives the BEA deflator vintage as posted on 2026-10-28. The EPA report used an earlier deflator vintage, with a 2012 base year.
8. The agent could not open the BEA interactive tables or FRED: the FRED request timed out.
