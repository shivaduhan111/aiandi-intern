# Evaluation of Clef-Flash Mistakes (comments.json)

This audit log records instances where the `clef-flash` model misclassified student comments or where borderline nuances required human discernment.

---

### Comment #2
- **Author:** Sneha Iyer
- **Thread:** Share your artifacts
- **Comment:** *"Submitted my artifact: a timetable clash checker for our dept. Claude made the UI in like 10 mins but I spent 2 hours tweaking prompt edge cases."*
- **Clef's Label:** `praise` (or `off-topic`)
- **My Label:** `constructive` (Borderline)
- **Why:** Clef focuses on the positive sentiment about Claude ("Claude made the UI in like 10 mins"). However, the core intent is sharing assignment progress and highlighting practical prompt engineering friction ("spent 2 hours tweaking prompt edge cases"), which is constructive experience-sharing for fellow students.

---

### Comment #5
- **Author:** Harsh Agarwal
- **Thread:** Share your artifacts
- **Comment:** *"@Rohit your expense splitter is really clean. One suggestion: there's a rounding error when splitting ₹100 three ways."*
- **Clef's Label:** `praise`
- **My Label:** `constructive`
- **Why:** The comment begins with a compliment ("really clean"), causing Clef to weight praise heavily. In reality, the actionable substance of the post is technical feedback pointing out a floating-point rounding bug in the artifact. Actionable technical feedback should take precedence over polite compliments.

---

### Comment #7
- **Author:** Mohd. Faizan
- **Thread:** Doubts
- **Comment:** *"Bhai kisi ko Codex ka access mila? My college email isn't working for the student plan."*
- **Clef's Label:** `off-topic` (or low-confidence `question/help-needed`)
- **My Label:** `question/help-needed`
- **Why:** Clef's confidence dropped significantly due to the informal Hinglish phrasing ("Bhai kisi ko..."). Despite the colloquial opener, the student is facing an authentication blocker with the designated course tool and actively asking peers for assistance.

---

### Comment #9
- **Author:** Vivek Menon
- **Thread:** Doubts
- **Comment:** *"I found that Claude kept adding features I didn't ask for. Telling it 'do only X, nothing else' at the start helped a lot."*
- **Clef's Label:** `question/help-needed`
- **My Label:** `constructive`
- **Why:** Posted in the "Doubts" thread, but contains no actual question. It is an unsolicited, highly valuable prompt-engineering tip sharing how negative prompting stopped hallucinations. Clef was likely misled by the thread title.
