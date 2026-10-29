# Political appointees up, career staff down

Which federal offices added political appointees while losing career staff? This repo compares two
OPM employment snapshots, office by office, and charts the offices with the largest political gains.

![Offices where political headcount rose while career headcount fell](output/political_shift.png)

Each row is an agency subelement, the most detailed office level in OPM's data. The cells show headcount
at the start and end months and the percent change; blue cells grew and red cells shrank. The chart shows
the offices with the largest political gain, out of those that also lost career staff. Every office is in
`output/political_shift_by_office.csv`.

## Run

```bash
python3 -I scripts/download.py                  # accessions and separations after the start month -> data/
python3 -I scripts/pull_subelement_headcount.py # headcount by office for the two snapshots -> data/
python3 -I scripts/shift.py                     # change by office -> output/political_shift_by_office.csv
python3 -I scripts/chart.py                     # chart -> output/political_shift.png
```

The two months compared, and the definition of a political appointee, live in `scripts/common.py`.
The chart's row rules (how many offices, minimum size, reorganization cutoff) are constants at the top of
`scripts/chart.py`. `data/` is not committed; `data/files_used.json` records which file version was used
for each month.

## Definitions

- **Source**: OPM EHRI employment snapshots, accessions, and separations, via the
  `impactproject/opm-ehri-data` mirror of OPM's API (data.opm.gov). Snapshots are read over HTTP, and
  only the columns needed are pulled.
- **Office**: agency subelement, grouped by code (agency code plus subelement code), not by name, so
  same-named units in different departments stay separate.
- **Political**: appointment type 44 (Schedule C), 55 (noncareer SES), 46 or 36 (executive, mostly
  presidential appointees), or anyone on the Executive Schedule (pay plan EX), since some of those carry
  an invalid or non-political appointment code.
- **Career (non-political)**: everyone else, excluding series 1102 (contracting). HHS began moving
  contracting staff between offices in September 2025 and EHRI codes the moves as new hires. Schedule
  Policy/Career (appointment type 67) counts as career here and is reported separately as `sched_pc_*`.
- **Reorganization check**: `recode_gap` is the change in career headcount minus (hires minus
  separations) between the two snapshots. Near zero means real hiring and departures; a large gap means
  people were moved in or out by a reorganization. The chart drops offices whose gap is large relative to
  their size.

## Caveats

- The start month has a full Biden-era appointee corps, so this compares a mature administration against a
  second-term one partway through.
- "Political" is based on appointment codes. Experts and consultants (pay plans ED and EF) are almost all
  appointment type 48 and count as career here, however they were brought in.
- EHRI does not link positions over time, so it can't show a specific career job being turned into a
  political one. The data shows the mix of each office changing.
- OPM revises files, and counts can change between versions.
