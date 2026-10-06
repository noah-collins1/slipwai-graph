# Demo 2: tokens conserved over every session (iteration 25)

The source is `--json` from the clone at 75bd48c, saved as `demo2-benchmark.json-output.json`. The feature record's
`session_totals` lists 25 sessions.

- **Conservation:** for each of the 25, Σ over all 18 records of `cost.sessions[s]` + `shared[s]` = `total[s]`.
  All 25 hold. Total 1 662 521 579, of which 385 852 904 is shared.
- **Independent count from the transcripts** (`demo2-tokens-per-session.txt`). I read each request (`requestId`,
  else `message.id`, else `uuid`) at the largest value each usage field reaches over its lines. A request found
  in several sessions goes to the session holding its earliest line. This agrees with the script's `total` for
  24 of 25 sessions. The 25th, `2382cd35`, is this iteration's live session (iteration 25 started
  10:45:35Z, and its transcript was still growing). I re-ran `--json` and recounted it back to back: script
  28 401 543, mine 28 401 543.
- **What changed since demo 1:** the totals went up, never down. Session `d883234c` went from 358 475 109
  (first line of each request, which is what the quickstart's step 4 counts) to 360 184 669, a rise of
  1 709 560. Over all 25 sessions the rise is 9 568 054 (+0.58 %). S08's cost went from 174.5M to 175.4M
  (175 356 594). The S08 17:17 implement went from 50 537 230 to 50 725 980.
  - All of the rise comes from streamed responses. Their later lines carry larger usage, mostly output tokens,
    and the first line undercounted them.
  - The copy rule (a request copied into a second session is counted once) moved nothing here. No request key
    appears in more than one of this directory's 25 transcripts.
  - Both rules are right. The figure is now the response's final usage. The quickstart's step-4 snippet still
    counts first-seen lines, so it now prints the old, lower number.
