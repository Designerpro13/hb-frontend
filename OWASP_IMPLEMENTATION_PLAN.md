# OWASP + Misconfiguration Implementation Plan

This project does **not** implement intentional vulnerabilities. It is a secure baseline that maps each risk area to controls and hardening tasks.

## Frontend Plan

1. Broken Access Control
- Store access token in session scope and clear on logout.
- Hide privileged UI actions by role once role model is added.

2. Cryptographic Failures
- Use HTTPS in non-local environments.
- Never embed secrets in frontend code or bundles.

3. Injection
- Use safe text rendering (no unsafe HTML rendering).
- Enforce client-side validation as UX, not as trust boundary.

4. Insecure Design
- Add abuse-case acceptance criteria for every feature.
- Add threat-model checkpoints in PR template.

5. Security Misconfiguration
- Strict CSP and frame protections from backend headers.
- Disable source maps in production build if not needed.

6. Vulnerable and Outdated Components
- Weekly dependency audit and version pinning.
- Remove unused dependencies and lockfile drift.

7. Identification and Authentication Failures
- Keep token in session storage only for local demo.
- Move to secure httpOnly cookie + CSRF defenses in prod.

8. Software and Data Integrity Failures
- Pin dependency versions and verify integrity in CI.
- Protect build pipeline and branch permissions.

9. Security Logging and Monitoring Failures
- Show generic errors in UI, no stack traces.
- Correlate frontend request IDs with backend logs.

10. Server-Side Request Forgery
- Frontend does not proxy arbitrary URLs.
- Block user-supplied remote fetch features unless allowlisted.

11. API Security - Broken Object Level Authorization
- Never trust client-side item IDs for authorization logic.

12. API Security - Broken Authentication
- Require backend token checks on every protected endpoint.

13. API Security - Excessive Data Exposure
- Request only needed fields; avoid admin/debug fields.

14. API Security - Lack of Resources and Rate Limiting
- Surface retry UI for 429 responses and backoff.

15. API Security - Unsafe Consumption of APIs
- Validate response shape before rendering sensitive data.

## Backend Plan

1. Broken Access Control
- Enforce auth dependency on all CRUD routes.
- Add object ownership checks when multi-user support is added.

2. Cryptographic Failures
- Require TLS in deployment.
- Move secrets to environment/secret manager and rotate regularly.

3. Injection
- Validate and constrain all user input with pydantic models.
- Use parameterized queries when DB is introduced.

4. Insecure Design
- Add explicit security requirements for each endpoint.
- Define abuse-rate thresholds and lockout behavior.

5. Security Misconfiguration
- Restrict CORS origins and trusted hosts.
- Set secure response headers and disable debug mode in prod.

6. Vulnerable and Outdated Components
- Pin dependencies and patch monthly (or faster on CVEs).

7. Identification and Authentication Failures
- Replace static token with proper identity provider/JWT lifecycle.
- Add token expiry and revocation strategy.

8. Software and Data Integrity Failures
- Signed releases, protected CI, and verified deploy artifacts.

9. Security Logging and Monitoring Failures
- Structured logs for auth failures, rate-limit events, and CRUD actions.
- Alert on repeated 401/429 spikes.

10. Server-Side Request Forgery
- If outbound requests are added, enforce allowlists and block private CIDRs.

11. API Security - Broken Object Level Authorization
- Check ownership on every read/update/delete object action.

12. API Security - Broken Authentication
- Uniform token validation middleware with deny-by-default.

13. API Security - Excessive Data Exposure
- Explicit response models; never dump raw internal models.

14. API Security - Lack of Resources and Rate Limiting
- Global and route-level rate limits and payload size caps.

15. API Security - Improper Assets Management and Common Misconfigs
- Maintain endpoint inventory and deprecate old versions.
- Block admin routes from public exposure.
- Disable default credentials and verbose error responses.
- Prevent directory listing and open cloud storage buckets.
- Enforce secure cookies, HSTS, and correct cache-control.
