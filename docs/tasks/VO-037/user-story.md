# VO-037: Fix code scanning: XSS vulnerabilities in dashboard templates

## User Story

## User Story: VO-035 — Fix XSS Vulnerabilities in Dashboard Templates

---

### User Story

**As a** user of the Virtual Office dashboard,
**I want** the application to safely handle all dynamic content rendering,
**so that** malicious scripts cannot be injected through the DOM and compromise my session, data, or machine.

---

### Acceptance Criteria

- [ ] `templates/dashboard.html` line 1924: Replace `innerHTML` assignment with `textContent` or DOMPurify-sanitized equivalent
- [ ] `templates/dashboard.html` line 2745: Same fix — no raw DOM insertion of external/user data
- [ ] `electron/wizard/wizard.js` line 195: Audit and fix unsafe DOM insertion; use `textContent` where content is plain text
- [ ] `templates/dashboard.html` line 1805: Fix incomplete sanitization — ensure the sanitization covers all attack vectors (not just partial escaping)
- [ ] No regressions in dashboard rendering or wizard flow after changes
- [ ] GitHub Code Scanning reports zero `js/xss-through-dom` and `js/incomplete-sanitization` alerts on these files post-merge
- [ ] If HTML rendering is genuinely required (e.g. rich text), DOMPurify is used with a strict allowlist config

---

### Priority Reasoning

**HIGH — ship this sprint.** These are HIGH-severity findings from automated scanning. XSS in an Electron app is especially dangerous — it can escalate to RCE via Node.js bridge access. This isn't theoretical risk; it's a known attack surface. Fixing it is low-effort, high-impact.

---

### Estimated Complexity

**2 / 5**

Surgical, targeted fixes. The locations are known. No architecture changes required. Risk of regression is low if the developer reads the surrounding context before editing.
