# Submission format

Deliver exactly these files, in your working directory:

- `page_register.csv` — the page register: one row per flagged passage.
- `results.json` — a JSON object; see below.

## `page_register.csv`

Header, exactly: `passage_id,page_number,verdict`

One row per passage in `passage_ledger.csv`, in any order, with `passage_id` in the
ledger's own form (`PS-04`, not `PS4` or `4`). `page_number` is the page that passage's
first line falls on once the accepted edits are in, and `verdict` is how the passage is
recorded under the layout spec, exactly one of: `WHOLLY_ON_PAGE`, `STRADDLES_BREAK`,
`EDIT_DEFERRED`, `LENGTH_FLOORED`.

Write `page_number` as a plain whole number (`6`, not `p. 6` or `006`).

Example (placeholder values):

```
passage_id,page_number,verdict
PS-00,1,WHOLLY_ON_PAGE
```

## `results.json`

A JSON object with exactly these keys and nothing else, each a whole number:

- `straddling_passage_count`
- `deferred_edit_count`
- `length_floored_count`
- `wholly_on_page_count`
- `final_page_count`

Shape example (placeholder values):

```json
{
  "straddling_passage_count": 0,
  "deferred_edit_count": 0,
  "length_floored_count": 0,
  "wholly_on_page_count": 0,
  "final_page_count": 0
}
```
