# API Endpoints Summary

## Problem Solved

**Issue**: Mixed HTML/JSON responses causing confusion - some endpoints returned HTML templates instead of pure JSON.

**Solution**: Created clear separation between API endpoints (JSON-only) and web interface (HTML templates).

## Clear API Structure

### JSON-Only API Endpoints (For Programmatic Access)

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| **GET** | `/api/v1/facebook/token/status/` | Get current token status | JSON only |
| **POST** | `/api/v1/facebook/token/validate/` | Validate & save Facebook token | JSON only |
| **POST** | `/api/v1/facebook/token/revoke/` | Revoke Facebook token | JSON only |

### HTML Web Interface (For Browser Users)

| Method | Endpoint | Purpose | Response |
|--------|----------|---------|----------|
| **GET** | `/facebook/settings/` | Facebook settings page | HTML template |

## Testing Your API

### 1. Quick Test (No Authentication)
```bash
curl -H "Accept: application/json" http://localhost:8000/api/v1/facebook/token/status/
```
**Expected Response:**
```json
{"detail":"Authentication credentials were not provided."}
```

### 2. With Authentication (Need API Key)
```bash
curl -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/facebook/token/status/
```

### 3. POST Request
```bash
curl -X POST \
     -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"access_token":"YOUR_FB_TOKEN"}' \
     http://localhost:8000/api/v1/facebook/token/validate/
```

## Key Differences

| Old (Confusing) | New (Clear) |
|-----------------|-------------|
| `/facebook/api/validate-token/` | `/api/v1/facebook/token/validate/` |
| Mixed HTML/JSON responses | Pure JSON responses |
| Inconsistent error formats | Standard JSON error format |
| No clear documentation | OpenAPI specification |

## Response Format Guarantee

✅ **All `/api/v1/` endpoints return JSON only**
✅ **Consistent error format**: `{"error": "message", "details": "..."}`
✅ **Standard HTTP status codes**: 200, 400, 401, 404
✅ **Proper Content-Type headers**: `application/json`

## Generated Documentation

- **OpenAPI Spec**: `static/openapi.yaml` (ready for Postman import)
- **Interactive Docs**: `http://localhost:8000/api/schema/swagger-ui/`
- **Usage Guide**: `API_USAGE.md`

## Frontend Integration

The React frontend now uses the clean API endpoints:
- Token validation: `/api/v1/facebook/token/validate/`
- Token revocation: `/api/v1/facebook/token/revoke/`

## Authentication Options

1. **API Key** (Recommended for external tools):
   ```
   Authorization: Api-Key YOUR_API_KEY
   ```

2. **Session Auth** (Browser-based):
   - Automatic with Django session cookies

## Next Steps

1. **Get API Key**: Go to `/admin/` → API Keys → Create new key
2. **Test in Postman**: Import `static/openapi.yaml`
3. **Use in Code**: Call `/api/v1/` endpoints for JSON responses

## No More Confusion!

- Want JSON? Use `/api/v1/...`
- Want HTML interface? Use `/facebook/settings/`
- Want documentation? Use `/api/schema/swagger-ui/`