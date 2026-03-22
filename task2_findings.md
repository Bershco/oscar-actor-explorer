# Task 2.3 Findings

## Candidate Findings Ranked

1. Most nominations without a win
   Reason: Strong, simple, and directly comparable across the whole dataset.
2. Longest wait from first nomination to first win
   Reason: Time-based and memorable, with a clear verification path.
3. Broadest category range for an individual nominee
   Reason: Shows unusual career breadth across multiple Oscar categories.
4. People nominated in both acting and directing
   Reason: Relevant to the actor/director app, but less striking than the top three.
5. Modern high-profile nominees with many losses
   Reason: Readable, but overlaps too much with the no-win finding.

## Selected Findings

### Finding 1: Most nominations without a win

- Finding: Greg P. Russell has 16 Oscar nominations and 0 wins.
- How it was found: Grouped nominations by person, filtered to individual nominees (`source_person_id` starting with `nm`), kept only people whose summed winner flag was 0, then ordered by nomination count descending.
- Why it is interesting: It highlights sustained Academy recognition without a single win.

### Finding 2: Longest wait from first nomination to first win

- Finding: Angela Lansbury waited 69 years, from the 1944 ceremony to the 2013 ceremony, for a first Oscar win.
- How it was found: Loaded each individual nominee's nominations ordered by ceremony year, took the first nomination year and the first winning year for each person, computed the year gap in Python, and selected the maximum.
- Why it is interesting: It shows how long Oscar recognition can take, even for eventual winners.

### Finding 3: Broadest category range for an individual nominee

- Finding: Walt Disney appears in 8 distinct Oscar categories: DOCUMENTARY, DOCUMENTARY (Short Subject), IRVING G. THALBERG MEMORIAL AWARD, OUTSTANDING PICTURE, SHORT SUBJECT (Cartoon), SHORT SUBJECT (Live Action), SHORT SUBJECT (Two-reel), SPECIAL AWARD.
- How it was found: Joined people to nominations and categories, counted distinct category names per individual nominee, ordered descending, then fetched that person's category list.
- Why it is interesting: It highlights an unusually broad Oscar footprint across very different types of work.

Run:

- `python3 -m app.findings`
