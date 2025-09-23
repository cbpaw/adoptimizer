def filter_schema_apis(endpoints):
    """
    Used to filter out certain API endpoints from the auto-generated docs / clients.
    This helps keep the API documentation clean and focused on relevant endpoints.
    """
    return [e for e in endpoints if include_in_schema(e)]


def include_in_schema(endpoint):
    """
    Determine whether an endpoint should be included in the OpenAPI schema.

    Args:
        endpoint: Tuple containing (url_path, url_pattern, method, callback)

    Returns:
        bool: True if endpoint should be included in schema
    """
    url_path = endpoint[0]

    # Exclude paths that shouldn't be in public API documentation
    excluded_prefixes = [
        "/cms/",           # Wagtail CMS URLs
        "/admin/",         # Django admin URLs
        "/accounts/",      # Django allauth URLs
        "/_allauth/",      # Allauth headless URLs
        "/hijack/",        # Hijack impersonation URLs
        "/stripe/",        # Stripe webhook URLs
        "/celery-progress/", # Celery progress URLs
        "/i18n/",          # Internationalization URLs
        "/jsi18n/",        # JavaScript i18n URLs
        "/sitemap.xml",    # Sitemap URLs
    ]

    # Exclude specific paths
    excluded_paths = [
        "/",               # Root redirect
        "/api/schema/",    # Schema endpoint itself
        "/api/schema/swagger-ui/",  # Swagger UI
        "/api/schema/redoc/",       # ReDoc UI
    ]

    # Check if path should be excluded
    for prefix in excluded_prefixes:
        if url_path.startswith(prefix):
            return False

    if url_path in excluded_paths:
        return False

    return True


def postprocess_schema_enhancements(result, generator, request, public):
    """
    Post-process the generated schema to add enhancements and customizations.
    This function can be used in SPECTACULAR_SETTINGS['POSTPROCESSING_HOOKS'].
    """
    # Add additional API information
    if 'info' not in result:
        result['info'] = {}

    # Enhance API info
    result['info'].update({
        'contact': {
            'name': 'AdOptimizer API Support',
            'email': 'support@adoptimizer.com'
        },
        'license': {
            'name': 'Proprietary',
        }
    })

    # Add server information for different environments
    result['servers'] = [
        {
            'url': 'http://localhost:8000',
            'description': 'Development server'
        },
        {
            'url': 'https://api.adoptimizer.com',
            'description': 'Production server'
        }
    ]

    # Organize endpoints into logical groups using tags
    if 'paths' in result:
        for path, methods in result['paths'].items():
            for method, operation in methods.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    # Auto-tag based on URL path
                    if path.startswith('/facebook/'):
                        if 'tags' not in operation:
                            operation['tags'] = ['Facebook Integration']
                    elif path.startswith('/api/'):
                        if 'tags' not in operation:
                            operation['tags'] = ['API']
                    elif path.startswith('/dashboard/'):
                        if 'tags' not in operation:
                            operation['tags'] = ['Dashboard']
                    elif path.startswith('/users/'):
                        if 'tags' not in operation:
                            operation['tags'] = ['User Management']

    return result
