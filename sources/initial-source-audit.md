# Initial source audit

Status: **superseded by visible-list queue policy**.

## Queue policy

The project no longer requires proof of the channel's historical absolute first upload.
The processing queue is the **currently discoverable/public long-form YouTube list**, ordered oldest to newest.

A 2020 third-party review reports that the channel's first upload was on 2019-07-16, but the exact title/video ID/transcript of that historical upload has not been reliably recovered in the current public-source workflow. This is treated as a possible unavailable/deleted/private gap and does not block processing.

## First processed public long-form sequence

1. 2019-08-25 — `AzY0FU-HxME` — 초보투자자들의 흔한 실수 5가지
2. 2019-09-13 — `OlurWhrOsLs` — 1만원으로 투자 시작하는 5가지 방법
3. 2019-10-06 — `4wt9xB9KV6A` — 연금저축펀드를 꼭 가지고 있어야 하는 이유

The dates and IDs above are verified from currently accessible YouTube search metadata.

## Data-quality rule

- Do not guess missing/deleted/private videos.
- Record possible gaps separately.
- A video may be counted as queue-processed while its analysis has `partial_source`; such items remain eligible for later enrichment without changing chronological sequence.
- Third-party summaries never replace an available primary transcript.
