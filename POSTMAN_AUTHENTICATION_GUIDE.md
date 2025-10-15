# AdOptimizer API Authentication Guide

## 🚫 Het Probleem: 403 Forbidden Error

Je kreeg een **403 Forbidden** error omdat je:
1. **Verkeerde authentication endpoints** gebruikte
2. **Geen CSRF token** meestuurde (vereist voor allauth headless API)

### Verkeerde Endpoints (Oud)
```
❌ POST /accounts/login/     (Django form-based login)
❌ POST /accounts/signup/    (Django form-based signup)
❌ POST /accounts/logout/    (Django form-based logout)
```

### Juiste Endpoints (Nieuw)
```
✅ POST /_allauth/browser/v1/auth/login     (Headless API login)
✅ POST /_allauth/browser/v1/auth/signup    (Headless API signup)
✅ DELETE /_allauth/browser/v1/auth/session (Headless API logout)
```

## 🔑 Authentication Flow - KRITIEK: CSRF Token Vereist!

### 1. **Stap 1: Verkrijg CSRF Token**

**Endpoint:** `GET /` (hoofdpagina)

**Response bevat CSRF token in cookies:**
```javascript
// Postman Test Script extraheert automatisch:
const csrfCookie = pm.cookies.get('csrftoken');
if (csrfCookie) {
    pm.environment.set('csrfToken', csrfCookie);
}
```

### 2. **Stap 2: Login Process**

**Endpoint:** `POST /_allauth/browser/v1/auth/login`

**Headers:**
```
Content-Type: application/json
X-CSRFToken: {{csrfToken}}         ← BELANGRIJK!
X-Session-Token: {{sessionToken}}  (if available)
```

**Request Body:**
```json
{
  "email": "your_email@example.com",
  "password": "your_password"
}
```

**Response (Success):**
```json
{
  "status": 200,
  "data": {
    "user": {
      "id": 1,
      "email": "your_email@example.com",
      "display": "Your Name"
    }
  },
  "meta": {
    "is_authenticated": true,
    "session_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### 3. **Stap 3: Authenticated Requests**

Voor alle andere API calls gebruik je **beide tokens**:

**Headers:**
```
X-Session-Token: {{sessionToken}}
X-CSRFToken: {{csrfToken}}
Content-Type: application/json
```

## 📝 Stap-voor-Stap Instructies

### Stap 1: Verkrijg CSRF Token
```
GET /
Postman extraheert automatisch csrftoken uit cookies
```

### Stap 2: Check Auth Status (optioneel)
```
GET /_allauth/browser/v1/auth/session
Headers: 
  X-CSRFToken: {{csrfToken}}
  X-Session-Token: {{sessionToken}}
```

### Stap 3: Login
```
POST /_allauth/browser/v1/auth/login
Headers: 
  Content-Type: application/json
  X-CSRFToken: {{csrfToken}}
Body: {"email": "user@example.com", "password": "password123"}
```

### Stap 4: Gebruik Beide Tokens
Voor alle AdOptimizer API calls:
```
GET /facebook-ads/api/dashboard/data/
Headers: 
  X-Session-Token: {{sessionToken}}
  X-CSRFToken: {{csrfToken}}
```

### Stap 5: Logout
```
DELETE /_allauth/browser/v1/auth/session
Headers: 
  X-CSRFToken: {{csrfToken}}
  X-Session-Token: {{sessionToken}}
```

## 🛠️ Postman Setup

### Environment Variables
Zorg ervoor dat je deze variabelen hebt ingesteld:

```
baseUrl: http://localhost:8000
allauthBaseUrl: http://localhost:8000/_allauth/browser/v1
csrfToken: (wordt automatisch gezet na GET /)
sessionToken: (wordt automatisch gezet na login)
```

### Automatische Token Management
De updated Postman collection heeft automatische scripts die:
- **CSRF tokens** ophalen uit cookies
- **Session tokens** opslaan na login
- **Beide tokens** gebruiken voor authenticated requests
- **Tokens wissen** na logout

## 🔄 Waarom Deze CSRF Requirement?

### Django-allauth Headless Browser Mode
Ook in headless mode blijft allauth **CSRF protection** gebruiken voor browser clients:

```javascript
// Uit allauth JavaScript code:
if (settings.client === Client.BROWSER) {
  options.headers['X-CSRFToken'] = getCSRFToken()
}
```

### Voordelen
- ✅ **Geen CSRF attacks**
- ✅ **Consistente beveiliging**
- ✅ **Standard Django protection**
- ✅ **Browser-compatible**

## 🚨 Belangrijke Foutoplossing

### 1. CSRF Token Ontbreekt
```
❌ Headers: alleen X-Session-Token
✅ Headers: X-Session-Token + X-CSRFToken
```

### 2. Verkeerde Volgorde
```
❌ Direct login zonder CSRF token
✅ 1. GET / voor CSRF token
✅ 2. POST login met CSRF token
```

### 3. Cookies Niet Ingeschakeld
```
❌ Postman: cookies uitgeschakeld
✅ Postman: cookies ingeschakeld voor domein
```

## 🎯 Volgende Stappen

1. **Re-importeer** de updated Postman collection
2. **Stel environment variables** in
3. **Test** in deze volgorde:
   - **GET /** (verkrijg CSRF token)
   - **POST login** (met CSRF token)
   - **Test** andere endpoints

## 📋 Checklist

- [ ] Postman collection geïmporteerd
- [ ] Environment variables ingesteld
- [ ] Cookies enabled in Postman
- [ ] GET / uitgevoerd voor CSRF token
- [ ] Login getest met beide tokens
- [ ] Other endpoints getest

---

**Nu zou je login moeten werken!** 🎉 