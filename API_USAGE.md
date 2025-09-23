# AdOptimizer API Usage Guide

## Clear JSON-Only API Endpoints

All API endpoints under `/api/v1/` return **JSON responses only** - no HTML templates.

## Base URL Structure

- **API Endpoints (JSON)**: `http://localhost:8000/api/v1/`
- **Web Pages (HTML)**: `http://localhost:8000/facebook/` (for settings UI)

## Authentication

All API endpoints require authentication. You can use:

1. **Session Authentication** (for browser-based requests)
2. **API Key Authentication** (for programmatic access)

### API Key Authentication
```bash
curl -H "Authorization: Api-Key YOUR_API_KEY" http://localhost:8000/api/v1/...
```

### Session Authentication (browser)
Include session cookies in your requests.

## Facebook API Endpoints

### 1. Get Token Status
**GET** `/api/v1/facebook/token/status/`

Returns the current Facebook token status for the authenticated user.

**Request:**
```bash
curl -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/facebook/token/status/
```

**Response (with token):**
```json
{
  "has_token": true,
  "facebook_user_name": "John Doe",
  "facebook_user_email": "john@example.com",
  "facebook_user_id": "123456789",
  "scopes": ["ads_read", "ads_management", "business_management"],
  "last_used_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-03-15T10:30:00Z",
  "token_expired": false,
  "token_expires_soon": false
}
```

**Response (no token):**
```json
{
  "has_token": false,
  "facebook_user_name": null,
  "facebook_user_email": null,
  "facebook_user_id": null,
  "scopes": [],
  "last_used_at": null,
  "expires_at": null,
  "token_expired": false,
  "token_expires_soon": false
}
```

### 2. Validate and Save Token
**POST** `/api/v1/facebook/token/validate/`

Validates a Facebook access token and saves it for the user.

**Request:**
```bash
curl -X POST \
     -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"access_token":"YOUR_FACEBOOK_TOKEN"}' \
     http://localhost:8000/api/v1/facebook/token/validate/
```

**Request Body:**
```json
{
  "access_token": "EAABwzLixnj"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Token validated and saved successfully",
  "created": true,
  "user_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "facebook_id": "123456789"
  },
  "token_info": {
    "scopes": ["ads_read", "ads_management"],
    "expires_at": "2025-03-15T10:30:00Z",
    "facebook_user_name": "John Doe",
    "facebook_user_email": "john@example.com",
    "facebook_user_id": "123456789",
    "last_used_at": "2025-01-15T10:30:00Z",
    "token_expired": false,
    "token_expires_soon": false
  }
}
```

**Error Response:**
```json
{
  "error": "Facebook API validation failed: Invalid OAuth access token",
  "details": "Error code: 190"
}
```

### 3. Revoke Token
**POST** `/api/v1/facebook/token/revoke/`

Deactivates the user's Facebook access token.

**Request:**
```bash
curl -X POST \
     -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/facebook/token/revoke/
```

**Success Response:**
```json
{
  "success": true,
  "message": "Facebook token revoked successfully"
}
```

**Error Response (no token):**
```json
{
  "error": "No Facebook token found for this user"
}
```

## Error Responses

All endpoints return consistent error responses:

### Authentication Required (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Validation Error (400)
```json
{
  "error": "Invalid request data",
  "details": {
    "access_token": ["This field is required."]
  }
}
```

### Not Found (404)
```json
{
  "error": "No Facebook token found for this user"
}
```

## Testing with Postman

1. **Import OpenAPI Schema**: Import `static/openapi.yaml` into Postman
2. **Set Base URL**: `http://localhost:8000`
3. **Add Authentication**:
   - Type: API Key
   - Key: `Authorization`
   - Value: `Api-Key YOUR_API_KEY`
   - Add to: Header

## Testing with cURL

### Complete Example Workflow:

```bash
# 1. Check current token status
curl -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/facebook/token/status/

# 2. Validate and save a new token
curl -X POST \
     -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json" \
     -d '{"access_token":"YOUR_FACEBOOK_TOKEN"}' \
     http://localhost:8000/api/v1/facebook/token/validate/

# 3. Check status again (should show token info)
curl -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/facebook/token/status/

# 4. Revoke the token
curl -X POST \
     -H "Authorization: Api-Key YOUR_API_KEY" \
     -H "Accept: application/json" \
     http://localhost:8000/api/v1/facebook/token/revoke/
```

## API vs Web Interface

| Purpose | URL Pattern | Response Type | Usage |
|---------|-------------|---------------|-------|
| **API Calls** | `/api/v1/...` | JSON only | Programmatic access, mobile apps, integrations |
| **Web Interface** | `/facebook/settings/` | HTML template | Browser-based user interface |
| **Documentation** | `/api/schema/swagger-ui/` | Interactive UI | API testing and documentation |

## Key Differences from Previous Setup

- ✅ **Clean separation**: API endpoints return JSON, web endpoints return HTML
- ✅ **Consistent structure**: All API endpoints under `/api/v1/`
- ✅ **Proper HTTP methods**: GET for reading, POST for actions
- ✅ **Standard status codes**: 200, 400, 401, 404
- ✅ **Consistent error format**: Always JSON with `error` and optional `details`

## Getting API Keys

1. Login to Django admin: `http://localhost:8000/admin/`
2. Go to **API Key** section
3. Create a new API key for your user
4. Use the generated key in API requests