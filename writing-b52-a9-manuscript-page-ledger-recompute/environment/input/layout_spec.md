# Manuscript layout — repagination spec

This spec governs the recomputation of the page each flagged passage lands on. Every
passage in `passage_ledger.csv` gets one row in the register.

## How the manuscript is laid out

A page holds 30 lines. The passages run one after another in the order the
ledger lists them, the first passage beginning on the first line of the manuscript, and
each passage beginning on the line after the one before it ends. A passage's page is the
page its first line falls on.

## How long a passage is

A passage's length is its drafted lines plus the line change of every accepted edit
proposed for it. `edit_register.csv` names the passage each edit was proposed for and
says whether the edit was accepted. A deferred edit changes nothing: the lines it would
add or remove are not counted, and the passage is recorded as carrying a deferred edit.
A passage with no accepted edit keeps its drafted length.

A passage never falls below 1 line. Where its accepted edits would take it under that,
the passage is held at 1 line and recorded as floored. The lines the floor holds back
are real lines: every passage after it sits that much further down the manuscript than
the edit register alone would suggest.

## What each passage is recorded as

A passage held at the minimum is recorded as floored, whatever else is true of it. A
passage with a deferred edit is recorded as carrying a deferred edit. Otherwise a
passage whose first and last lines fall on different pages is recorded as crossing a
break, and one whose lines all fall on a single page is recorded as sitting wholly on it.

## What the roll-up figures mean

`straddling_passage_count`, `deferred_edit_count`, `length_floored_count` and
`wholly_on_page_count` are the numbers of passages recorded under each of those four
treatments. `final_page_count` is the final page, meaning the page the manuscript's last
line falls on.
