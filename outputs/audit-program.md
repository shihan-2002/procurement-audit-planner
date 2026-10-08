# Audit program

*Generated 2026-10-08 by `build_pack.py` from `audit-plan.json`, `risk-register.md` (revision 2), `auditor-comments.md` by Shihan Wang dated 2026-10-08, `rules.json` and `analytics.json`. Status: DRAFT for challenge, QA review and auditor sign-off.*

**Indicators, not findings.** Every test below checks a control against a pattern in public data. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

9 risks in scope, 15 controls, 16 tests, 261 sampled transactions. Samples are drawn by the builder from `analytics-full/` by the recipe stated under each test, and every transaction is listed with its workbook row.


## R-01: Quotes or tenders not evidenced for spend at or above the quote threshold [12 (High; Medium - High)]

**Audit objective.** Conclude whether purchases at or above the quote threshold were competed as the Rules require, or covered by an approved waiver.

**C-01.1. Expected control.** Spend at or above the quote threshold is competed through the Procurement Portal with at least three invitations to quote, evaluated against criteria notified in advance. [CPR-56, CPR-57, CPR-19, CPR-20] Owner: Budget holder and relevant Service Director.

**T-01.1. Test.** For each sampled supplier, obtain the Portal record of the quotation exercise: the invitations sent, the quotes received, the evaluation criteria and the award decision. A pass is three invitations issued through the Portal and an award on the notified criteria. Also confirm the supplier's suitability, capability, legal status and financial standing were checked before award. [CPR-56, CPR-19, CPR-10, metric:$.tests.high_value_suppliers.headline_general_procurement.suppliers]  
**Evidence to inspect:** Procurement Portal exercise record, quotes, evaluation sheet, award decision, supplier due-diligence checks  
**Sample:** 10 items from `high-value-suppliers.csv`, where dominant_tag = general_procurement, largest annualised_estimate first, 2 payments per supplier; 19 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:793` | 2026-07-13 | VolkerHighways Ltd | £998,987.64 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:603` | 2026-07-28 | VolkerHighways Ltd | £855,750.25 | Environment |
| 2 | `Over500_2026_P02_-_published.xlsx:2196` | 2026-05-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,201,856.40 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:2146` | 2026-06-29 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,180,425.32 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:2144` | 2026-06-25 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:2216` | 2026-06-03 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:665` | 2026-05-15 | The Better Group Ltd | £64,500.00 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:666` | 2026-05-15 | The Better Group Ltd | £58,833.00 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:473` | 2026-05-27 | SoftwareONE UK Ltd | £375,697.68 | Transformation, Customer & ICT |
| 5 | `Over500_2026_P02_-_published.xlsx:474` | 2026-05-27 | SoftwareONE UK Ltd | £85,871.04 | Transformation, Customer & ICT |
| 6 | `Over500_2026_P02_-_published.xlsx:2200` | 2026-05-13 | Livity Life Ltd | £135,591.03 | Finance, Property & Procurement |
| 6 | `Over500_2026_P03_-_published.xlsx:3087` | 2026-06-17 | Livity Life Ltd | £127,886.78 | Finance, Property & Procurement |
| 7 | `Over500_2026_P02_-_published.xlsx:437` | 2026-05-20 | Newbury & District Ltd | £60,797.19 | Environment |
| 7 | `Over500_2026_P03_-_published.xlsx:267` | 2026-06-01 | Newbury & District Ltd | £59,626.76 | Environment |
| 8 | `Over500_2026_P04_-_published.xlsx:784` | 2026-07-10 | E W BEARD LTD | £64,202.50 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:674` | 2026-05-20 | E W BEARD LTD | £60,039.70 | Education & SEND |
| 9 | `Over500_2026_P02_-_published.xlsx:669` | 2026-05-26 | ASCIA CONSTRUCTION LIMITED | £332,579.29 | Education & SEND |
| 10 | `Over500_2026_P04_-_published.xlsx:905` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £129,125.00 | Finance, Property & Procurement |
| 10 | `Over500_2026_P04_-_published.xlsx:492` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £91,629.15 | Finance, Property & Procurement |

**C-01.2. Expected control.** Every purchase has written evidence and a written contract in a form approved by the Monitoring Officer. [CPR-33, CPR-34] Owner: Relevant Service Director.

**T-01.2. Test.** For the same suppliers as T-01.1, obtain the purchase orders behind the two sampled payments and the signed contract; confirm the contract form was approved by the Monitoring Officer. [CPR-33, CPR-34]  
**Evidence to inspect:** Purchase orders, signed contract, Legal Services approval of the form  
**Sample:** uses the suppliers and payments drawn in T-01.1

**C-01.3. Expected control.** Any departure from competition is a waiver or exception approved in advance by the S151 Officer or Monitoring Officer, with a written exception report to the relevant board. [CPR-21, CPR-22, CPR-23, CPR-24, CPR-25, CPR-26, CPR-27, CPR-28, CPR-60] Owner: S151 Officer / Monitoring Officer.

**T-01.3. Test.** Obtain the waiver and exception log for the window. Where a T-01.1 supplier has no competition record, trace it to a waiver approved in advance by the S151 Officer and an exception report to the board; confirm the approver matches the value band. [CPR-22, CPR-23, CPR-24, CPR-25, CPR-28, CPR-60]  
**Evidence to inspect:** Waiver and exception register, exception reports, S151 approvals  
**Sample:** enquiry and register test; applies to T-01.1 suppliers with no competition record


## R-02: Requirements split so each payment stays below the quote threshold [12 (High; Medium - High)]

**Audit objective.** Conclude whether payments that together reach the quote threshold within thirty days were one requirement that should have been competed.

**C-02.1. Expected control.** Requirements are aggregated over their full value before the procurement route is chosen; no contract is split to stay below a threshold. [CPR-14, CPR-56] Owner: Budget holder.

**T-02.1. Test.** For each sampled window, obtain the orders and invoices for the sampled payments and any quotes. Decide whether the payments were one requirement; if so, confirm three quotes were sought through the Portal or a waiver was approved. [CPR-14, metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.windows]  
**Evidence to inspect:** Purchase orders, invoices, quotes, requisition history for the supplier in the window  
**Sample:** 10 items from `split-purchases-windows.csv`, where dominant_tag = general_procurement, threshold = 25000, largest window_total first, largest 5 payments per item, one item per supplier_norm; 49 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:2185` | 2026-05-20 | VolkerHighways Ltd | £19,420.72 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:723` | 2026-05-05 | VolkerHighways Ltd | £18,033.36 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:701` | 2026-05-12 | VolkerHighways Ltd | £17,896.87 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2179` | 2026-05-19 | VolkerHighways Ltd | £17,882.35 | Environment |
| 1 | `Over500_2026_P02_-_published.xlsx:2178` | 2026-05-05 | VolkerHighways Ltd | £16,916.01 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:13` | 2026-06-01 | The Better Group Ltd | £24,088.98 | Children's Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:2397` | 2026-06-01 | The Better Group Ltd | £22,361.26 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:9` | 2026-05-28 | The Better Group Ltd | £20,457.43 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:10` | 2026-05-28 | The Better Group Ltd | £19,605.14 | Children's Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:2396` | 2026-06-01 | The Better Group Ltd | £18,039.18 | Adult Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:269` | 2026-06-12 | Newbury & District Ltd | £14,852.00 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:268` | 2026-06-01 | Newbury & District Ltd | £13,826.61 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:274` | 2026-06-30 | Newbury & District Ltd | £13,663.85 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:171` | 2026-06-02 | Newbury & District Ltd | £10,529.33 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:336` | 2026-06-02 | Newbury & District Ltd | £9,861.00 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:450` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £9,615.23 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:452` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £9,483.38 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:183` | 2026-07-08 | WEAVAWAY TRAVEL LTD | £8,226.54 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:456` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £8,097.04 | Education & SEND |
| 4 | `Over500_2026_P04_-_published.xlsx:305` | 2026-07-24 | WEAVAWAY TRAVEL LTD | £7,986.00 | Education & SEND |
| 5 | `Over500_2026_P04_-_published.xlsx:735` | 2026-07-13 | Roadside Technologies Ltd | £21,000.00 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:733` | 2026-07-13 | Roadside Technologies Ltd | £11,188.22 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:1287` | 2026-07-13 | Roadside Technologies Ltd | £10,298.22 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:601` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:740` | 2026-07-13 | Roadside Technologies Ltd | £9,103.64 | Environment |
| 6 | `Over500_2026_P02_-_published.xlsx:284` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £3,120.00 | Education & SEND |
| 6 | `Over500_2026_P02_-_published.xlsx:424` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,940.00 | Education & SEND |
| 6 | `Over500_2026_P02_-_published.xlsx:427` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,925.00 | Education & SEND |
| 6 | `Over500_2026_P02_-_published.xlsx:265` | 2026-05-12 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,912.00 | Education & SEND |
| 6 | `Over500_2026_P02_-_published.xlsx:422` | 2026-05-28 | FD TRAVELS LIMITED T/A SCHOOL EXPRESS | £2,910.00 | Education & SEND |
| 7 | `Over500_2026_P02_-_published.xlsx:530` | 2026-05-27 | Elior UK PLC | £23,694.03 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:440` | 2026-06-16 | Elior UK PLC | £23,516.69 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:433` | 2026-06-17 | Elior UK PLC | £18,592.30 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:434` | 2026-06-11 | Elior UK PLC | £11,935.93 | Adult Social Care |
| 8 | `Over500_2026_P02_-_published.xlsx:404` | 2026-05-26 | BROADWAY CARS | £4,015.38 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:412` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:416` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:418` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:364` | 2026-05-12 | BROADWAY CARS | £3,747.69 | Education & SEND |
| 9 | `Over500_2026_P03_-_published.xlsx:688` | 2026-06-01 | R&A Haines Building Contractors | £20,332.89 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:742` | 2026-06-30 | R&A Haines Building Contractors | £18,707.55 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:740` | 2026-06-30 | R&A Haines Building Contractors | £16,600.00 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:733` | 2026-06-01 | R&A Haines Building Contractors | £9,666.85 | Development & Housing |
| 9 | `Over500_2026_P03_-_published.xlsx:709` | 2026-06-09 | R&A Haines Building Contractors | £5,487.25 | Development & Housing |
| 10 | `Over500_2026_P03_-_published.xlsx:649` | 2026-06-18 | Triple Value Impact | £24,244.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:641` | 2026-06-17 | Triple Value Impact | £13,275.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:2393` | 2026-06-17 | Triple Value Impact | £13,110.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:2392` | 2026-06-17 | Triple Value Impact | £10,787.00 | Chief Executive |
| 10 | `Over500_2026_P03_-_published.xlsx:642` | 2026-06-17 | Triple Value Impact | £6,612.00 | Chief Executive |


## R-03: Payments bunched just below the quote threshold [6 (Moderate; Moderate)]

**Audit objective.** Conclude whether payments just below the quote threshold reflect genuine order values.

**C-03.1. Expected control.** The quote route is set by the genuine total value of the requirement: one quote below the quote threshold, three through the Portal at or above it. [CPR-55, CPR-56] Owner: Budget holder.

**T-03.1. Test.** For each sampled payment, obtain the order and the quote; confirm the order value and that no related order to the same supplier was raised for the same requirement. [CPR-55, metric:$.tests.threshold_clustering.per_threshold[1].general_procurement.count]  
**Evidence to inspect:** Purchase order, quote, supplier order history  
**Sample:** 5 items from `threshold-clustering.csv`, where threshold = 25000, tag = general_procurement, largest Net amount first; 5 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:1281` | 2026-07-29 | The Better Group Ltd | £24,476.02 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:2201` | 2026-05-15 | WOKINGHAM BOROUGH COUNCIL | £24,416.73 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:649` | 2026-06-18 | Triple Value Impact | £24,244.00 | Chief Executive |
| 4 | `Over500_2026_P02_-_published.xlsx:560` | 2026-05-12 | DevComms South East Ltd | £24,227.07 | Development & Housing |
| 5 | `Over500_2026_P03_-_published.xlsx:13` | 2026-06-01 | The Better Group Ltd | £24,088.98 | Children's Social Care |


## R-04: High-value suppliers with no published contract notice [9 (High; Medium - High)]

**Audit objective.** Conclude whether high-value suppliers with no published notice are covered by a contract recorded in the Contract Register and published where required.

**C-04.1. Expected control.** Opportunities at or above the quote threshold have a contract notice on the Central Digital Platform, approved by the Service Lead for Procurement; framework call-offs rest on a scheme the Council may use, with Monitoring Officer approval where no further competition is run. [CPR-56, CPR-11, CPR-13, CPR-29, CPR-62] Owner: Service Lead for Procurement and Commissioning.

**T-04.1. Test.** For each sampled supplier, obtain the contract or framework call-off and its notice. A pass is a published notice, or a framework call-off with advice confirming the scheme and, where no further competition was run, Monitoring Officer approval. [CPR-56, CPR-29, CPR-62, metric:$.tests.off_contract.headline_unmatched_general_procurement.suppliers]  
**Evidence to inspect:** Contract or call-off, CDP / Contracts Finder / Find a Tender notice, framework access advice  
**Sample:** 10 items from `off-contract-unmatched.csv`, where dominant_tag = general_procurement, largest annualised_estimate first, 1 payments per supplier, excluding suppliers and rows already drawn in T-01.1; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:2198` | 2026-05-13 | SLOUGH BOROUGH COUNCIL | £296,177.15 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:183` | 2026-06-03 | Sikandar Hayat t/a Prompt Cars | £73,296.50 | Education & SEND |
| 3 | `Over500_2026_P03_-_published.xlsx:661` | 2026-06-08 | ANDY AND ES LIMITED | £59,335.72 | Education & SEND |
| 4 | `Over500_2026_P02_-_published.xlsx:530` | 2026-05-27 | Elior UK PLC | £23,694.03 | Adult Social Care |
| 5 | `Over500_2026_P04_-_published.xlsx:589` | 2026-07-16 | BBOWT | £118,027.50 | Environment |
| 6 | `Over500_2026_P03_-_published.xlsx:2217` | 2026-06-10 | BRACKNELL FOREST BOROUGH CNCL | £130,310.57 | Finance, Property & Procurement |
| 7 | `Over500_2026_P02_-_published.xlsx:738` | 2026-05-20 | ANCHOR PIPEWORK LIMITED | £33,148.00 | Finance, Property & Procurement |
| 8 | `Over500_2026_P03_-_published.xlsx:2143` | 2026-06-23 | WOKINGHAM BOROUGH COUNCIL | £95,104.51 | Finance, Property & Procurement |
| 9 | `Over500_2026_P03_-_published.xlsx:479` | 2026-06-29 | KPMG | £76,405.00 | Executive Director - Resources |
| 10 | `Over500_2026_P03_-_published.xlsx:730` | 2026-06-23 | SCOTTISH & SOUTHERN | £101,258.24 | Environment |

**C-04.2. Expected control.** Every award is notified to the Service Lead for Commissioning and Procurement and recorded on the published Contract Register. [CPR-36, CPR-08, CPR-07] Owner: Relevant Service Director.

**T-04.2. Test.** Obtain the Council Contract Register and confirm each T-04.1 supplier, and each T-01.1 supplier with no matching notice, has an entry with value, duration and supplier; confirm the award notification to the Service Lead. [CPR-36, CPR-08]  
**Evidence to inspect:** Contract Register extract, award notifications  
**Sample:** register test over the T-04.1 suppliers and the T-01.1 suppliers with no matching notice


## R-05: Spend after a contract notice ended without an approved extension [9 (High; Medium - High)]

**Audit objective.** Conclude whether suppliers paid after their notices ended were covered by an approved extension or a new contract.

**C-05.1. Expected control.** Extensions provided for in the contract are approved by the S151 Officer before the original term ends. [CPR-63] Owner: S151 Officer.

**T-05.1. Test.** For each sampled supplier, obtain the current contract or the extension and its S151 approval; confirm the approval pre-dates the original end date and covers the sampled payments. [CPR-63, metric:$.tests.expired_notice_spend.suppliers]  
**Evidence to inspect:** Contract, extension letter, S151 approval, register entry  
**Sample:** 7 items from `expired-notice-spend.csv`, largest annualised_estimate first, 2 payments per supplier, (only 7 available); 9 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:704` | 2026-06-16 | Hope & Clay (Construction) Ltd | £91,306.75 | Environment |
| 2 | `Over500_2026_P03_-_published.xlsx:58` | 2026-06-03 | BERKSHIRE MECHANICAL SERVICES | £8,250.00 | Development & Housing |
| 2 | `Over500_2026_P03_-_published.xlsx:42` | 2026-06-03 | BERKSHIRE MECHANICAL SERVICES | £6,250.00 | Development & Housing |
| 3 | `Over500_2026_P02_-_published.xlsx:467` | 2026-05-08 | G7 BUSINESS SOLUTIONS LIMITED | £5,469.78 | Finance, Property & Procurement |
| 3 | `Over500_2026_P03_-_published.xlsx:531` | 2026-06-10 | G7 BUSINESS SOLUTIONS LIMITED | £5,469.78 | Finance, Property & Procurement |
| 4 | `Over500_2026_P02_-_published.xlsx:459` | 2026-05-15 | CACI Limited | £12,071.67 | Children's Social Care |
| 5 | `Over500_2026_P03_-_published.xlsx:686` | 2026-06-22 | Morton Pattison Ltd | £1,102.00 | Environment |
| 6 | `Over500_2026_P03_-_published.xlsx:821` | 2026-06-03 | Davis and Associates Consultancy Limited | £800.00 | Chief Executive |
| 7 | `Over500_2026_P04_-_published.xlsx:58` | 2026-07-20 | Tactical Facilities Management Ltd | £681.94 | Development & Housing |


## R-06: Spend running ahead of the awarded contract value without an approved variation [12 (High; Medium - High)]

**Audit objective.** Conclude whether spend above the award's annual rate is covered by an approved variation.

**C-06.1. Expected control.** Variations of scope are approved in advance: by the Monitoring Officer and S151 Officer below the Threshold, and by the relevant board above it. [CPR-64] Owner: Monitoring Officer and S151 Officer / relevant board.

**T-06.1. Test.** For each sampled supplier, obtain the contract, the awarded value and any variation with its approval; compare cumulative spend with the awarded value. A pass is spend within the award or an approved variation covering it. [CPR-64, metric:$.tests.spend_vs_award.flagged]  
**Evidence to inspect:** Contract, variation notices, approvals, cumulative spend report  
**Sample:** 8 items from `spend-vs-award.csv`, where flagged = True, largest ratio first, 2 payments per supplier, (only 8 available); 13 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:905` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £129,125.00 | Finance, Property & Procurement |
| 1 | `Over500_2026_P04_-_published.xlsx:492` | 2026-07-22 | NEC SOFTWARE SOLUTIONS UK LIMITED | £91,629.15 | Finance, Property & Procurement |
| 2 | `Over500_2026_P03_-_published.xlsx:396` | 2026-06-10 | BookingLab Limited | £24,000.00 | Transformation, Customer & ICT |
| 3 | `Over500_2026_P03_-_published.xlsx:384` | 2026-06-04 | Exacom Systems Ltd | £12,105.85 | Development & Housing |
| 4 | `Over500_2026_P04_-_published.xlsx:1276` | 2026-07-22 | WCL UK Ltd (Trading as Everything ICT) | £102,882.78 | Education & SEND |
| 5 | `Over500_2026_P03_-_published.xlsx:276` | 2026-06-30 | SMS-Environmental Ltd | £2,070.00 | Adult Social Care |
| 5 | `Over500_2026_P04_-_published.xlsx:365` | 2026-07-09 | SMS-Environmental Ltd | £1,335.60 | Adult Social Care |
| 6 | `Over500_2026_P02_-_published.xlsx:460` | 2026-05-20 | Softcat Ltd | £8,979.02 | Education & SEND |
| 6 | `Over500_2026_P03_-_published.xlsx:375` | 2026-06-17 | Softcat Ltd | £2,025.98 | Transformation, Customer & ICT |
| 7 | `Over500_2026_P03_-_published.xlsx:371` | 2026-06-08 | IDOX SOFTWARE LTD | £48,579.20 | Community Services |
| 7 | `Over500_2026_P02_-_published.xlsx:462` | 2026-05-20 | IDOX SOFTWARE LTD | £2,647.21 | Development & Housing |
| 8 | `Over500_2026_P03_-_published.xlsx:2130` | 2026-06-09 | TWO SAINTS LTD | £38,775.00 | Development & Housing |
| 8 | `Over500_2026_P04_-_published.xlsx:3181` | 2026-07-22 | TWO SAINTS LTD | £38,775.00 | Development & Housing |


## R-07: Possible duplicate payments to the same supplier [9 (High; Medium - High)]

**Audit objective.** Conclude whether same-amount payments to one supplier within seven days were distinct supplies.

**C-07.1. Expected control.** Each payment is supported by its own invoice and written evidence of the purchase, so an invoice cannot be paid twice. [CPR-33] Owner: Accounts Payable.

**T-07.1. Test.** For each sampled group, obtain both invoices and the orders; confirm they are distinct supplies, or that the duplicate was identified and recovered. [CPR-33, metric:$.tests.duplicates.per_tier.different_time.general_procurement.groups]  
**Evidence to inspect:** Invoices, purchase orders, credit notes or recovery records  
**Sample:** 10 items from `duplicates-groups.csv`, where tier = different_time, dominant_tag = general_procurement, largest extra_gbp first; 25 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:3308` | 2026-07-15 | VolkerHighways Ltd | £101,925.86 | Environment |
| 1 | `Over500_2026_P04_-_published.xlsx:618` | 2026-07-17 | VolkerHighways Ltd | £101,925.86 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3210` | 2026-07-13 | VolkerHighways Ltd | £54,241.36 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:3302` | 2026-07-16 | VolkerHighways Ltd | £54,241.36 | Environment |
| 3 | `Over500_2026_P02_-_published.xlsx:2160` | 2026-05-12 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 3 | `Over500_2026_P02_-_published.xlsx:2161` | 2026-05-13 | TWO SAINTS LTD | £27,147.69 | Development & Housing |
| 4 | `Over500_2026_P04_-_published.xlsx:3184` | 2026-07-13 | VolkerHighways Ltd | £17,882.35 | Environment |
| 4 | `Over500_2026_P04_-_published.xlsx:3185` | 2026-07-16 | VolkerHighways Ltd | £17,882.35 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:1288` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:598` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:734` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 5 | `Over500_2026_P04_-_published.xlsx:789` | 2026-07-13 | Roadside Technologies Ltd | £5,594.11 | Environment |
| 6 | `Over500_2026_P04_-_published.xlsx:259` | 2026-07-13 | BROADWAY CARS | £5,330.00 | Education & SEND |
| 6 | `Over500_2026_P04_-_published.xlsx:264` | 2026-07-13 | BROADWAY CARS | £5,330.00 | Education & SEND |
| 6 | `Over500_2026_P04_-_published.xlsx:474` | 2026-07-13 | BROADWAY CARS | £5,330.00 | Education & SEND |
| 7 | `Over500_2026_P02_-_published.xlsx:8` | 2026-05-13 | Pavillion Publishing and Media Ltd | £9,084.60 | Adult Social Care |
| 7 | `Over500_2026_P02_-_published.xlsx:643` | 2026-05-14 | Pavillion Publishing and Media Ltd | £9,084.60 | Executive Director People - Children's Services |
| 8 | `Over500_2026_P02_-_published.xlsx:412` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:416` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 8 | `Over500_2026_P02_-_published.xlsx:418` | 2026-05-27 | BROADWAY CARS | £3,900.00 | Education & SEND |
| 9 | `Over500_2026_P02_-_published.xlsx:369` | 2026-05-12 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 9 | `Over500_2026_P02_-_published.xlsx:372` | 2026-05-12 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 9 | `Over500_2026_P02_-_published.xlsx:395` | 2026-05-13 | BROADWAY CARS | £3,640.00 | Education & SEND |
| 10 | `Over500_2026_P03_-_published.xlsx:459` | 2026-06-25 | LOCAL GOVERNMENT PROPERTY CONSULTANTS (LGPC) | £4,925.00 | Finance, Property & Procurement |
| 10 | `Over500_2026_P03_-_published.xlsx:467` | 2026-06-25 | LOCAL GOVERNMENT PROPERTY CONSULTANTS (LGPC) | £4,925.00 | Finance, Property & Procurement |

**T-07.2. Test.** For each sampled placement group, obtain the provider invoices or schedules and the care package records; confirm each payment covers a distinct period or individual, or that the duplicate was recovered. [CPR-33, metric:$.tests.duplicates.per_tier.different_time.placements.groups]  
**Evidence to inspect:** Provider invoices or payment schedules, care package records, recovery records  
**Sample:** 10 items from `duplicates-groups.csv`, where tier = different_time, dominant_tag = care_or_education_placement, largest extra_gbp first; 82 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:2164` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2165` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2166` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2167` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2169` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2170` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2173` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2175` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2176` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2177` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2189` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2190` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2195` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2199` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2200` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2201` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2203` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2204` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2311` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2312` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2313` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2315` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2316` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2317` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2321` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2322` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:2323` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3106` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3107` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3109` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3110` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3111` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3112` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3113` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3114` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 1 | `Over500_2026_P03_-_published.xlsx:3115` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,337.45 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2171` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2172` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2191` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2192` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2193` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2196` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2198` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2310` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2314` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2319` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2320` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:3108` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:3116` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2242` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2243` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2247` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2249` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2252` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2253` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2255` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2257` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2260` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P02_-_published.xlsx:2263` | 2026-05-21 | Phoenix Child Care Limited -The Grange School | £21,988.16 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:2157` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:2158` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:2159` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:2306` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:3102` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P03_-_published.xlsx:3103` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £18,768.75 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2246` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £32,711.33 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2248` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £32,711.33 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2251` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £32,711.33 | Education (DSG Funded) & Other Education Grants |
| 6 | `Over500_2026_P02_-_published.xlsx:2266` | 2026-05-26 | Huckleberry House | £30,918.75 | Education (DSG Funded) & Other Education Grants |
| 6 | `Over500_2026_P02_-_published.xlsx:2267` | 2026-05-26 | Huckleberry House | £30,918.75 | Education (DSG Funded) & Other Education Grants |
| 6 | `Over500_2026_P02_-_published.xlsx:2269` | 2026-05-26 | Huckleberry House | £30,918.75 | Education (DSG Funded) & Other Education Grants |
| 7 | `Over500_2026_P03_-_published.xlsx:1931` | 2026-06-16 | Care Services To You | £23,989.77 | Children's Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:2008` | 2026-06-16 | Care Services To You | £23,989.77 | Children's Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:3044` | 2026-06-22 | Care Services To You | £23,989.77 | Children's Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:3750` | 2026-07-17 | Care Services To You | £23,989.77 | Children's Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:3092` | 2026-07-23 | Care Services To You | £23,989.77 | Children's Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:3161` | 2026-07-23 | Care Services To You | £23,989.77 | Children's Social Care |
| 9 | `Over500_2026_P02_-_published.xlsx:2245` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 9 | `Over500_2026_P02_-_published.xlsx:2258` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 9 | `Over500_2026_P02_-_published.xlsx:2262` | 2026-05-21 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 10 | `Over500_2026_P02_-_published.xlsx:2092` | 2026-05-26 | Amegreen Childrens Services | £34,431.08 | Children's Social Care |
| 10 | `Over500_2026_P02_-_published.xlsx:2105` | 2026-05-27 | Amegreen Childrens Services | £34,431.08 | Children's Social Care |


## R-08: Care and education placements without recorded reasons or board approval [12 (High; Medium - High)]

**Audit objective.** Conclude whether individually chosen placements carry recorded reasons for the choice of provider and, above the Threshold, board approval.

**C-08.1. Expected control.** The reasons for the choice of provider are recorded on the individual's case notes. [CPR-65] Owner: Service Directors.

**T-08.1. Test.** For each sampled placement window, identify the placements behind the sampled payments and inspect the case notes for the recorded reasons for the choice of provider. [CPR-65, metric:$.tests.split_purchases.per_threshold[0].placements.windows]  
**Evidence to inspect:** Case notes, placement agreements, brokerage records  
**Sample:** 10 items from `split-purchases-windows.csv`, where dominant_tag = care_or_education_placement, threshold = 25000, largest window_total first, largest 2 payments per item, one item per supplier_norm; 20 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:1850` | 2026-07-08 | BUPA Care Services | £10,400.00 | Adult Social Care |
| 1 | `Over500_2026_P04_-_published.xlsx:1039` | 2026-07-08 | BUPA Care Services | £9,903.62 | Adult Social Care |
| 2 | `Over500_2026_P03_-_published.xlsx:2171` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 2 | `Over500_2026_P03_-_published.xlsx:2172` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P04_-_published.xlsx:2239` | 2026-07-01 | Affinity Trust Support Ltd | £24,926.00 | Adult Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:1629` | 2026-06-24 | Affinity Trust Support Ltd | £17,444.96 | Adult Social Care |
| 4 | `Over500_2026_P02_-_published.xlsx:2245` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P02_-_published.xlsx:2258` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £23,210.00 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:1508` | 2026-05-20 | GCH (Alder) Ltd t/a Hungerford Care Home | £18,144.00 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:1573` | 2026-05-20 | GCH (Alder) Ltd t/a Hungerford Care Home | £6,580.00 | Adult Social Care |
| 6 | `Over500_2026_P02_-_published.xlsx:1642` | 2026-05-13 | VOYAGE CARE | £14,756.16 | Adult Social Care |
| 6 | `Over500_2026_P03_-_published.xlsx:1465` | 2026-06-10 | VOYAGE CARE | £14,756.16 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:772` | 2026-06-10 | PURLEY PARK TRUST LTD | £10,156.00 | Adult Social Care |
| 7 | `Over500_2026_P04_-_published.xlsx:649` | 2026-07-08 | PURLEY PARK TRUST LTD | £10,156.00 | Adult Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:1415` | 2026-07-15 | WEST BERKSHIRE MENCAP | £18,035.64 | Adult Social Care |
| 8 | `Over500_2026_P04_-_published.xlsx:680` | 2026-07-29 | WEST BERKSHIRE MENCAP | £18,035.64 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:896` | 2026-07-08 | We Are The Care Company Ltd | £5,175.36 | Adult Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:921` | 2026-07-08 | We Are The Care Company Ltd | £5,175.36 | Adult Social Care |
| 10 | `Over500_2026_P03_-_published.xlsx:2307` | 2026-06-03 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £24,788.75 | Education (DSG Funded) & Other Education Grants |
| 10 | `Over500_2026_P02_-_published.xlsx:2241` | 2026-05-12 | Sukhbir Singh and Harvinder Singh T/A Calcot Services for Children (CSFC) | £24,618.75 | Education (DSG Funded) & Other Education Grants |

**C-08.2. Expected control.** Placement contracts whose annual or total value exceeds the Threshold are approved by the relevant board. [CPR-66] Owner: Relevant board.

**T-08.2. Test.** For the largest placement providers, obtain the board approval of the placement contract or framework; confirm it covers the period of the sampled payments. [CPR-66, metric:$.population.tags.care_or_education_placement.gbp]  
**Evidence to inspect:** Board minutes or approvals, placement framework or contract  
**Sample:** 10 items from `high-value-suppliers.csv`, where dominant_tag = care_or_education_placement, largest annualised_estimate first, 1 payments per supplier, excluding suppliers and rows already drawn in T-08.1; 10 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P02_-_published.xlsx:823` | 2026-05-13 | RUSKIN MILL TRUST | £179,236.76 | Adult Social Care |
| 2 | `Over500_2026_P02_-_published.xlsx:2095` | 2026-05-26 | Amegreen Childrens Services | £36,705.55 | Children's Social Care |
| 3 | `Over500_2026_P04_-_published.xlsx:3476` | 2026-07-29 | Brighter Living Care Ltd | £78,599.04 | Adult Social Care |
| 4 | `Over500_2026_P03_-_published.xlsx:2180` | 2026-06-17 | ACORN CARE & EDUCATION LTD | £28,482.93 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2124` | 2026-05-27 | Camino Care | £94,040.67 | Children's Social Care |
| 6 | `Over500_2026_P03_-_published.xlsx:1625` | 2026-06-17 | SM Voice Advocacy Limited | £15,847.26 | Adult Social Care |
| 7 | `Over500_2026_P04_-_published.xlsx:1247` | 2026-07-01 | Abi-support Ltd | £10,329.32 | Adult Social Care |
| 8 | `Over500_2026_P02_-_published.xlsx:2021` | 2026-05-01 | Care Services To You | £23,989.77 | Children's Social Care |
| 9 | `Over500_2026_P04_-_published.xlsx:3140` | 2026-07-27 | Johav Care support Healthcare Limited | £16,098.00 | Children's Social Care |
| 10 | `Over500_2026_P04_-_published.xlsx:3047` | 2026-07-22 | DIMENSIONS (NSO) LTD | £36,422.28 | Adult Social Care |


## R-09: Key Decision and delegated-authority approvals for awards above the Key Decision threshold [12 (High; Medium - High)]

**Audit objective.** Conclude whether awards above the Key Decision threshold carried the Key Decision, board report and, where required, Executive approval.

**C-09.1. Expected control.** Awards above the Key Decision threshold are made as a Key Decision with a written report approved by the relevant board, following a full tender where the Rules require one. [CPR-04, CPR-53, CPR-58, CPR-30, CPR-32] Owner: Relevant Service Director with the Portfolio Holder.

**T-09.1. Test.** For each sampled supplier, obtain the award decision: the Key Decision record, the forward plan entry, the board-approved report and the tender record. A pass is all four, dated before the award. [CPR-04, CPR-53, metric:$.tests.split_purchases.per_threshold[1].headline_general_procurement.windows]  
**Evidence to inspect:** Key Decision record, forward plan, board report and approval, tender record, award report  
**Sample:** 8 items from `split-purchases-windows.csv`, where threshold = 500000, largest window_total first, largest 2 payments per item, one item per supplier_norm, (only 8 available); 16 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P03_-_published.xlsx:699` | 2026-06-08 | VolkerHighways Ltd | £329,988.88 | Environment |
| 1 | `Over500_2026_P03_-_published.xlsx:701` | 2026-06-09 | VolkerHighways Ltd | £307,338.45 | Environment |
| 2 | `Over500_2026_P04_-_published.xlsx:1850` | 2026-07-08 | BUPA Care Services | £10,400.00 | Adult Social Care |
| 2 | `Over500_2026_P04_-_published.xlsx:1039` | 2026-07-08 | BUPA Care Services | £9,903.62 | Adult Social Care |
| 3 | `Over500_2026_P03_-_published.xlsx:2171` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 3 | `Over500_2026_P03_-_published.xlsx:2172` | 2026-06-17 | Oaklands SEN School Berkshire Limited | £20,534.90 | Education (DSG Funded) & Other Education Grants |
| 4 | `Over500_2026_P04_-_published.xlsx:2320` | 2026-07-08 | Affinity Trust Support Ltd | £28,512.00 | Adult Social Care |
| 4 | `Over500_2026_P03_-_published.xlsx:1628` | 2026-06-24 | Affinity Trust Support Ltd | £26,394.66 | Adult Social Care |
| 5 | `Over500_2026_P02_-_published.xlsx:2254` | 2026-05-20 | Phoenix Child Care Limited -The Grange School | £33,799.71 | Education (DSG Funded) & Other Education Grants |
| 5 | `Over500_2026_P02_-_published.xlsx:2244` | 2026-05-19 | Phoenix Child Care Limited -The Grange School | £32,944.66 | Education (DSG Funded) & Other Education Grants |
| 6 | `Over500_2026_P02_-_published.xlsx:823` | 2026-05-13 | RUSKIN MILL TRUST | £179,236.76 | Adult Social Care |
| 6 | `Over500_2026_P02_-_published.xlsx:1822` | 2026-05-13 | RUSKIN MILL TRUST | £151,859.86 | Adult Social Care |
| 7 | `Over500_2026_P03_-_published.xlsx:9` | 2026-06-15 | Comensura Ltd | £107,880.99 | Strategy & Governance |
| 7 | `Over500_2026_P03_-_published.xlsx:12` | 2026-06-08 | Comensura Ltd | £101,567.70 | Strategy & Governance |
| 8 | `Over500_2026_P02_-_published.xlsx:473` | 2026-05-27 | SoftwareONE UK Ltd | £375,697.68 | Transformation, Customer & ICT |
| 8 | `Over500_2026_P02_-_published.xlsx:474` | 2026-05-27 | SoftwareONE UK Ltd | £85,871.04 | Transformation, Customer & ICT |

**C-09.2. Expected control.** Contracts at the Executive threshold or above have Executive approval. [CPR-54] Owner: Executive.

**T-09.2. Test.** For each sampled supplier whose annualised spend reaches the Executive threshold, obtain the Executive approval or the quarterly report delegating the award. [CPR-54]  
**Evidence to inspect:** Executive minutes, quarterly procurement reports  
**Sample:** 3 items from `high-value-suppliers.csv`, where dominant_tag = general_procurement, annualised_estimate ≥ 2500000, largest annualised_estimate first, 1 payments per supplier, (only 3 available); 3 transactions

| # | Row ID | Date | Supplier | Amount | Service |
|---|---|---|---|---|---|
| 1 | `Over500_2026_P04_-_published.xlsx:793` | 2026-07-13 | VolkerHighways Ltd | £998,987.64 | Environment |
| 2 | `Over500_2026_P02_-_published.xlsx:2196` | 2026-05-27 | VEOLIA ES WEST BERKSHIRE LTD (CHAPS ONLY) | £2,201,856.40 | Environment |
| 3 | `Over500_2026_P03_-_published.xlsx:2144` | 2026-06-25 | Millbrook Healthcare Limited | £1,141,918.00 | Finance, Property & Procurement |

**C-09.3. Expected control.** No award is made without the delegated authority set out in Appendix A, within budget and in accordance with a decision. [CPR-02, CPR-05, CPR-51, CPR-52] Owner: Relevant Service Director.

**T-09.3. Test.** Obtain the scheme of delegation and the authority record for each T-09.1 and T-09.2 award; confirm the awarding officer held delegated authority for the value and the contract was within an approved budget. [CPR-05, CPR-51, CPR-52, CPR-02]  
**Evidence to inspect:** Scheme of delegation, nominations in writing, budget approval  
**Sample:** authority test over the T-09.1 and T-09.2 awards


## Prepared-by-client (PBC) request list

Derived from the test steps above. Each item names the tests that need it.

| # | Risk | Item requested | For tests |
|---|---|---|---|
| 1 | R-01 | Procurement Portal records of the quotation or tender exercise for the sampled suppliers | T-01.1 |
| 2 | R-01 | Evaluation criteria and scoring sheets | T-01.1 |
| 3 | R-01 | Purchase orders and signed contracts for the T-01.1 suppliers | T-01.2 |
| 4 | R-01 | Waiver and exception register for the spend window, with approvals and exception reports | T-01.3 |
| 5 | R-02 | Purchase orders, invoices and any quotes for the sampled split-purchase windows | T-02.1 |
| 6 | R-03 | Purchase orders and quotes for the sampled payments just below the quote threshold | T-03.1 |
| 7 | R-04 | Contracts, framework call-offs and published notices for the sampled unmatched suppliers | T-04.1 |
| 8 | R-04 | Council Contract Register extract as at the end of the spend window | T-04.2 |
| 9 | R-05 | Current contracts or extension approvals for suppliers paid after their notices ended | T-05.1 |
| 10 | R-06 | Contracts, variations and approvals for suppliers whose spend exceeds the award rate | T-06.1 |
| 11 | R-06 | Cumulative spend to date per sampled contract | T-06.1 |
| 12 | R-07 | Invoices, orders and any credit notes for the sampled duplicate groups | T-07.1 |
| 13 | R-07 | Provider invoices and care package records for the sampled placement duplicate groups | T-07.2 |
| 14 | R-08 | Case-note extracts recording the reason for provider choice for the sampled placements | T-08.1 |
| 15 | R-08 | Board approvals for the largest placement providers | T-08.2 |
| 16 | R-09 | Key Decision records, board reports and tender records for the sampled high-value suppliers | T-09.1 |
| 17 | R-09 | Executive approvals or quarterly delegation reports for contracts at the Executive threshold | T-09.2 |
| 18 | R-09 | Scheme of delegation and written nominations for the officers who made the sampled awards | T-09.3 |
