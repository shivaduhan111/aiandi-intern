# Notes on AI Comment Moderation

## How to Run the Program

The moderation pipeline is contained in a single Python script (`moderate.py`) using only the Python standard library.

1. **Prerequisites & Setup:**
   Ensure your Cloudflare credentials are saved in `cloud-flare.local.sh`:
   ```bash
   cp cloud-flare.sh cloud-flare.local.sh
   # Edit cloud-flare.local.sh to add your real CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN
   ```

2. **Phase 1: Baseline Comments (`comments.json` with `clef-flash`):**
   ```bash
   python3 moderate.py
   ```
   - Uses model: `@cf/cloudflare/clef-flash`
   - Input: `comments.json`
   - Output: `results.html` (interactive HTML dashboard)
   - Cache: `cache_results_v1.json` (avoids duplicate API calls on re-runs)

3. **Phase 2: Harder Comments (`comments-v2.json` with `clef`):**
   ```bash
   python3 moderate.py --v2
   ```
   - Uses model: `@cf/cloudflare/clef`
   - Input: `comments-v2.json`
   - Output: `results-v2.html`
   - Cache: `cache_results_v2.json`

4. **Testing a Small Batch (Optional):**
   ```bash
   python3 moderate.py --limit 5
   ```

---

## Tools and Models Used

- **Cloudflare Workers AI Clef Models:**
  - `clef-flash`: Fast, low-latency decision model evaluated against baseline forum data (`comments.json`).
  - `clef`: Larger, higher-accuracy decision model evaluated against harder, subtle edge cases (`comments-v2.json`).
- **AI Assistant (Gemini):**
  - Used for rapid script scaffolding, designing prompt criteria definitions, building the interactive HTML visualization, and analyzing borderline linguistic nuances.
- **Python Standard Library (`urllib.request`, `json`, `re`, `argparse`, `html`):**
  - Zero external dependencies (`pip` not required), ensuring clean portability and execution.
- **Client-Side Interactive Dashboard:**
  - Embedded vanilla JavaScript and CSS inside `results.html` and `results-v2.html` featuring instant category filtering, full probability distributions, and a **"Sort by Lowest Confidence First"** toggle to rapidly isolate borderline predictions.

---

## Reflections & Key Takeaways

1. **Decision Models vs. Generative Chatbots:**
   Working with Clef highlighted the practical power of specialized decision models over full generative LLMs for moderation. Instead of generating open-ended text that requires regex parsing, Clef provides direct categorical choices and normalized probability distributions. The `confidence` metric proved to be the single most actionable signal: sorting comments by lowest confidence immediately surfaced the exact 10–15% of comments that needed human review.

2. **Prompt & Criteria Engineering for Edge Cases:**
   In `comments.json`, standard spam (e.g., assignment services with emojis) and clear doubts were classified with >90% confidence. However, subtle linguistic nuances posed challenges:
   - *Hinglish & Multilingual Context:* Queries in informal Hindi/Hinglish (e.g., *"Bhai kisi ko Codex ka access mila?"*) occasionally saw lower confidence in `clef-flash`, though `clef` handled them much better.
   - *Mixed Intent (Praise + Feedback):* Peer comments like *"Rohit's project is really clean... one suggestion: rounding error"* blend praise with constructive feedback. Tuning criteria to prioritize actionable technical critique over polite conversational openers resolved this.
   - *Self-Deprecation vs. Abuse:* In `comments-v2.json`, students venting frustration at themselves (*"I'm the dumbest person in this batch"*) can trigger naive toxicity filters unless criteria explicitly specify that abuse requires hostile attacks directed at others.

3. **Human-in-the-Loop Efficiency:**
   The combination of automated API scoring, local response caching, and an interactive HTML report allowed the entire evaluation of 200 comments to be completed in well under 30 minutes, keeping human attention focused where it matters most: judgment on borderline cases.
