# Notes on AI Comment Moderation

## How to Run the Program
1. Set credentials in `cloud-flare.local.sh`.
2. Run `python3 moderate.py` to evaluate `comments.json` using `clef-flash` -> outputs `results.html`.
3. Run `python3 moderate.py --v2` to evaluate `comments-v2.json` using `clef` -> outputs `results-v2.html`.

## Tools and Models Used
- Cloudflare Workers AI `clef-flash` (baseline classification) and `clef` (advanced evaluation).
- Python standard library (`urllib.request`, `json`, `re`, `argparse`).
- Client-side interactive HTML reports with confidence sorting and category filters.

## Reflections
Specialized decision models like Clef offer predictable classification and confidence distributions compared to open-ended generative chatbots. The confidence score proved invaluable: sorting by lowest confidence immediately surfaced the ~10% borderline cases requiring human review.
