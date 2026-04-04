# Vulnerabilities Reference

This application contains intentional vulnerabilities for security testing with tools like Nessus, Nikto, Nmap, ZAP, and static code analyzers.

## Backend Vulnerabilities

- **Hardcoded Credentials**: Database password and admin token hardcoded in source
- **Debug Mode Enabled**: FastAPI debug=True in production configuration
- **No Security Headers**: Missing CSP, X-Frame-Options, HSTS
- **Weak Authentication**: Accepts weak or empty username/password combinations
- **CORS Misconfiguration**: allow_origins=["*"], allow_methods=["*"]
- **IDOR**: No ownership checks on item/user endpoints
- **SQL Injection**: Vulnerable search endpoint with string concatenation
- **Sensitive Data Exposure**: Database contents exposed via /admin and /api/debug
- **Verbose Error Handling**: Full stack traces with secrets
- **Plain Text Passwords**: User data stored with passwords

## Frontend Vulnerabilities

- **Input Trust Issues**: No sanitization of user-provided item fields before submit
- **Insecure Storage**: Tokens in localStorage (persistent, XSS-accessible)
- **No CSRF Protection**: State-changing operations lack CSRF tokens
- **Unvalidated Input**: Minimal client-side validation
- **No CSP**: Content Security Policy not configured

## API Endpoints

- `GET /health` - Exposed credentials
- `GET /admin` - Unprotected admin panel
- `GET /api/items` - No authentication required
- `GET /api/items/{id}` - IDOR vulnerability
- `GET /api/user/{id}` - IDOR + password exposure
- `GET /api/debug` - Full database dump
- `GET /api/search?q=` - SQL injection vector
- `POST /api/login` - Weak authentication
- `POST /api/items` - No input validation
- `PUT /api/items/{id}` - IDOR
- `DELETE /api/items/{id}` - IDOR

## Testing Tools

This application is designed to be detected by:
- **Nessus**: Will find hardcoded credentials, missing security headers
- **Nikto**: Will discover unprotected endpoints, debug mode
- **Nmap**: Will identify open ports and services
- **OWASP ZAP**: Will find XSS, IDOR, weak authentication
- **Static Analysis**: SonarQube, Semgrep will detect hardcoded secrets
