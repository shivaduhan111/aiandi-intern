# Evaluation of Clef Mistakes (comments-v2.json)

This audit log records instances where the larger `clef` model misclassified student comments or where complex contextual nuances required human judgment.

---

### Comment #2
- **Author:** Prof. Sunita Rao
- **Thread:** Doubts
- **Comment:** *"Any free chatbot is fine. Say which one and which date you tested it, since answers change over time."*
- **Clef's Label:** `question/help-needed` (or `off-topic`)
- **My Label:** `constructive`
- **Why:** The comment is posted by the course instructor answering a student's prior question. Because it is in the "Doubts" thread and discussing assignment requirements, Clef occasionally confuses an authoritative answer with asking a question. It is clearly constructive guidance and policy clarification.

---

### Comment #7
- **Author:** Rishi Jain
- **Thread:** Doubts
- **Comment:** *"Ugh I'm genuinely the dumbest person in this batch. Deleted my whole .env file and lost the API key, now Cloudflare won't show it again..."*
- **Clef's Label:** `abusive`
- **My Label:** `question/help-needed` (Borderline)
- **Why:** Clef flagged the self-deprecating slur ("dumbest person") as abusive. However, the student is not attacking or harassing anyone else; they are venting personal frustration over an API credential loss and seeking guidance on how to recover access. Genuine toxicity filters should distinguish self-criticism from interpersonal abuse.

---

### Comment #10
- **Author:** Manav Jain
- **Thread:** Share your work
- **Comment:** *"@Aditi your rubric is so basic even my 10 year old cousin could make it..."*
- **Clef's Label:** `constructive` (or low-confidence `abusive`)
- **My Label:** `abusive`
- **Why:** Although ostensibly framed as a critique of a peer's rubric, it offers zero actionable suggestions or technical insight. Instead, it relies on condescending and belittling remarks ("even my 10 year old cousin could make it"), crossing the line into hostile discouragement.
