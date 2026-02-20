# VO-026: Edge case in chat message persistence when input is empty

## User Story

---

**Story ID:** VO-026

---

### User Story

> As a **user of the Virtual Office chat interface**, I want **empty or whitespace-only messages to be silently rejected without being saved or sent**, so that **my chat history stays clean and I'm not confused by blank messages appearing in conversations**.

---

### Acceptance Criteria

- [ ] Submitting an empty input (zero characters) does not create a message record in the database
- [ ] Submitting a whitespace-only input (spaces, tabs, newlines) does not create a message record
- [ ] The send action (button click or keyboard shortcut) is a no-op when input is empty/whitespace — no API call is made
- [ ] No error toast or alert is shown to the user for a silent no-op submit; the input field simply retains focus
- [ ] Existing non-empty messages are unaffected — persistence behavior is unchanged
- [ ] Backend endpoint rejects empty/whitespace message payloads with a `400 Bad Request` if called directly (defensive server-side guard)
- [ ] Unit tests cover: empty string, whitespace-only string, and valid message submission paths

---

### Priority Reasoning

**Medium.** QA-confirmed edge case with low user impact today but real data integrity risk at scale. Blank messages polluting the persistence layer create noise in analytics, waste storage, and could surface as UX confusion (blank bubbles in chat). The fix is low-risk and low-effort — ship it clean before the chat feature gets broader adoption.

---

### Estimated Complexity

**1 / 5**

Frontend guard is a one-liner trim check before submission. Backend validation is a single guard clause. No schema changes, no migrations, no architectural impact.
