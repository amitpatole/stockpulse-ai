# VO-022: Missing input validation in alert system allows XSS

## User Story

Done. Here's the summary:

---

**VO-022: Missing input validation in alert system allows XSS**

**User story:** As a trader using the alert system, I want all alert inputs sanitized before rendering, so that malicious scripts can't be injected through alert fields and executed in other users' browsers.

**Key acceptance criteria:**
- Server-side sanitization on all alert fields (name, message, condition expression)
- HTML-escaped on output — no raw DOM interpolation of user data
- Malicious markup (`<script>`, `onerror=`, SVG injection) rejected with a clear validation error
- Escape-on-output backstop for any malicious content already in storage
- Test coverage for common XSS payloads; no regression on legitimate special characters

**Priority: P1.** QA-confirmed, reproducible XSS with session token exfiltration potential. This doesn't ship.

**Complexity: 3/5.** Sanitization logic is simple, but alerts render across multiple surfaces (UI, email, push). Each needs auditing. The bulk of effort is test coverage and ensuring legitimate condition syntax isn't broken by overly aggressive escaping.
