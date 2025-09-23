# AdOptimizer API Documentation

This document explains how to generate and use the OpenAPI documentation for the AdOptimizer API.

## Generated API Documentation Files

The API documentation is available in multiple formats:

- **YAML Format**: `static/openapi.yaml` - Human-readable format, best for version control
- **JSON Format**: `static/openapi.json` - Machine-readable format, compatible with most tools

## Generating API Documentation

Use the custom Django management command to generate up-to-date API documentation:

```bash
# Generate YAML format (default)
make manage ARGS='generate_openapi --output=static/openapi.yaml'

# Generate JSON format
make manage ARGS='generate_openapi --output=static/openapi.json --format=json'

# Generate with custom title and description
make manage ARGS='generate_openapi --title="My API" --description="Custom API description"'
```

### Command Options

- `--output` / `-o`: Output file path (default: `openapi.yaml`)
- `--format` / `-f`: Output format (`yaml` or `json`, default: `yaml`)
- `--title` / `-t`: Override API title
- `--api-version`: Override API version
- `--description` / `-d`: Override API description

## Using with API Testing Tools

### Postman

1. Open Postman
2. Click **Import** button
3. Select **Upload Files** tab
4. Choose the generated `openapi.yaml` or `openapi.json` file
5. Postman will create a collection with all API endpoints

### Insomnia

1. Open Insomnia
2. Click **Import Data**
3. Select **From File**
4. Choose the generated OpenAPI file
5. Insomnia will import all endpoints with proper documentation

### Swagger UI (Online)

1. Go to [Swagger Editor](https://editor.swagger.io/)
2. Click **File** → **Import file**
3. Upload the generated `openapi.yaml` file
4. Interactive documentation will be displayed

### Swagger UI (Local)

Access the built-in Swagger UI at: http://localhost:8000/api/schema/swagger-ui/

## API Endpoints Overview

The documentation includes the following endpoint categories:

### Facebook Authentication (`/facebook/api/v1/`)
- **GET** `/token/status/` - Get current token status
- **POST** `/token/validate/` - Validate and save Facebook token
- **POST** `/token/revoke/` - Revoke Facebook token

### Dashboard (`/dashboard/api/`)
- Various dashboard and analytics endpoints

## Authentication

The API supports multiple authentication methods:

1. **API Key Authentication**: Add header `Authorization: Api-Key YOUR_API_KEY`
2. **Session Authentication**: Browser-based authentication using Django sessions
3. **Basic Authentication**: For development/testing purposes

## Schema Components

The documentation includes detailed schemas for:

- Request/response models
- Error responses
- Authentication requirements
- Field validation rules

## Development Workflow

1. **Make API Changes**: Modify views, serializers, or add new endpoints
2. **Update Documentation**: Run the generation command to update docs
3. **Test with Tools**: Import updated schema into Postman/Insomnia
4. **Commit Changes**: Include both code and documentation updates

## Automatic Generation

For CI/CD integration, you can add the generation command to your deployment pipeline:

```bash
# In your deployment script
python manage.py generate_openapi --output=docs/api.yaml
```

## Customization

The OpenAPI schema generation can be customized by modifying:

- `apps/api/schema.py` - Schema filtering and post-processing
- `adoptimizer/settings.py` - SPECTACULAR_SETTINGS configuration
- API view docstrings and `@extend_schema` decorators

## Support

For questions about the API documentation:
- Email: support@adoptimizer.com
- Check the Django admin for API key management
- Review the Swagger UI for interactive testing