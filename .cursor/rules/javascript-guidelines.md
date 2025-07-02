# JavaScript Guidelines

## Core Principles

### 1. Modular Architecture
- **NEVER** write JavaScript functions directly in HTML templates
- **ALWAYS** create separate JavaScript files in `/assets/javascript/`
- Use class-based architecture for reusable components
- All JavaScript files must be added to `vite.config.ts` as entry points
- Load files in templates using `{% vite_asset 'assets/javascript/filename.js' %}`

### 2. File Organization
```
assets/javascript/
├── notification-system.js         # Global notification system (required by all pages)
├── campaign-sync-manager.js       # Campaign sync state management
├── campaign-selection.js          # Campaign selection page logic
├── facebook-settings.js           # Facebook settings page logic
├── campaign-detail.js             # Campaign detail page logic
└── [feature-name].js              # Feature-specific files
```

### 3. Vite Integration
**All JavaScript files MUST be registered in `vite.config.ts`:**
```typescript
// In vite.config.ts rollupOptions.input:
'notification-system': path.resolve(__dirname, './assets/javascript/notification-system.js'),
'campaign-sync-manager': path.resolve(__dirname, './assets/javascript/campaign-sync-manager.js'),
'campaign-selection': path.resolve(__dirname, './assets/javascript/campaign-selection.js'),
'facebook-settings': path.resolve(__dirname, './assets/javascript/facebook-settings.js'),
'campaign-detail': path.resolve(__dirname, './assets/javascript/campaign-detail.js'),
```

**Build assets after adding new files:**
```bash
npm run build
```

### 4. Template Integration
**Required template setup:**
```html
{% extends "web/app/app_base.html" %}
{% load static %}
{% load django_vite %}

{% block page_js %}
<!-- Always load notification system first -->
{% vite_asset 'assets/javascript/notification-system.js' %}
<!-- Then load page-specific modules -->
{% vite_asset 'assets/javascript/feature-specific.js' %}
{% endblock %}
```

### 5. Class Structure
Each JavaScript file should follow this pattern:
```javascript
/**
 * [Component Name]
 * [Brief description of functionality]
 */
class ComponentName {
    constructor() {
        this.csrfToken = this.getCSRFToken();
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    initializeComponents() {
        // Component initialization logic
        this.attachGlobalFunctions();
    }

    attachGlobalFunctions() {
        // Make functions globally available for onclick handlers
        window.functionName = () => this.handleFunction();
    }
}

// Initialize when DOM is ready
new ComponentName();
```

## Notification System

### 6. Notification Usage
- **NEVER** use `alert()`, `confirm()`, or `prompt()` functions
- **ALWAYS** use the global notification system

```javascript
// Available globally after loading notification-system.js
window.showSuccess('Operation successful!');
window.showError('An error occurred.');
window.showWarning('Warning message.');
window.showInfo('Information message.');

// Or using the class directly with options
window.notificationSystem.success('Success message', { 
    duration: 3000,
    closeable: true 
});
```

### 7. Notification Options
```javascript
// All notification methods support these options:
{
    duration: 5000,        // Auto-dismiss time in milliseconds (0 = no auto-dismiss)
    closeable: true,       // Whether notification can be manually closed
    position: 'bottom-right' // Notification position
}
```

## State Management

### 8. Persistent Storage
- Use `localStorage` for client-side persistence
- Implement consistent storage prefixes (e.g., `campaignSync_`, `userSettings_`)
- Always check for storage availability before use

```javascript
class StateManager {
    constructor() {
        this.storagePrefix = 'featureName_';
    }

    setState(key, value) {
        try {
            localStorage.setItem(`${this.storagePrefix}${key}`, JSON.stringify(value));
        } catch (error) {
            console.error('localStorage not available:', error);
        }
    }

    getState(key) {
        try {
            const item = localStorage.getItem(`${this.storagePrefix}${key}`);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading localStorage:', error);
            return null;
        }
    }
}
```

## Page Updates

### 9. Dynamic Updates
- **NEVER** use `location.reload()` or similar page refresh methods
- **ALWAYS** implement dynamic content updates via JavaScript
- Use fetch API for server communication
- Update DOM elements selectively

```javascript
// Correct approach
async refreshData() {
    try {
        const response = await fetch('/api/endpoint/', {
            headers: { 'X-CSRFToken': this.csrfToken }
        });
        const data = await response.json();
        this.updateUIElements(data);
        window.showSuccess('Data refreshed successfully!');
    } catch (error) {
        console.error('Refresh failed:', error);
        window.showError('Failed to refresh data');
    }
}
```

## Event Handling

### 10. Event Listeners
- Use class methods for event handlers
- Properly manage event listener attachment/detachment
- Use delegation for dynamic content
- For onclick handlers in HTML, attach via `window.functionName`

```javascript
initializeEventListeners() {
    // For dynamic elements - use event delegation
    document.addEventListener('click', (e) => {
        if (e.target.matches('.my-button')) {
            this.handleClick(e);
        }
    });

    // For static elements - direct attachment
    document.querySelectorAll('.my-button').forEach(button => {
        button.addEventListener('click', (e) => this.handleClick(e));
    });
}

attachGlobalFunctions() {
    // For HTML onclick handlers
    window.handleButtonClick = (id) => this.handleClick(id);
}
```

## API Communication

### 11. CSRF Protection
- Always include CSRF tokens in POST requests
- Get token from DOM elements or meta tags

```javascript
getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}
```

### 12. Error Handling
- Always wrap async operations in try-catch blocks
- Provide meaningful error messages to users
- Log errors for debugging
- Handle authentication errors with proper redirects

```javascript
async performAction() {
    try {
        const response = await fetch('/api/action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        window.showSuccess('Action completed successfully!');
        return result;
    } catch (error) {
        console.error('Action failed:', error);
        
        // Handle authentication errors
        if (error.status === 401 || error.status === 403) {
            window.showError('Session expired. Redirecting to login...');
            setTimeout(() => {
                window.location.href = '/accounts/login/';
            }, 1500);
            return;
        }
        
        window.showError('Failed to perform action');
        throw error;
    }
}
```

## Component Communication

### 13. Inter-Component Communication
- Use global window objects for component instances when needed
- Implement event-based communication for loose coupling
- Use consistent naming conventions

```javascript
// Make components globally available when needed
window.featureManager = new FeatureManager();
window.campaignSyncManager = new CampaignSyncManager();

// Or use custom events for communication
document.dispatchEvent(new CustomEvent('featureUpdated', { 
    detail: { data: updateData } 
}));

// Listen for custom events
document.addEventListener('featureUpdated', (e) => {
    this.handleFeatureUpdate(e.detail.data);
});
```

## Performance

### 14. Optimization
- Minimize DOM queries by caching elements
- Use event delegation for dynamic content
- Debounce/throttle frequent operations
- Clean up resources and event listeners

```javascript
class OptimizedComponent {
    constructor() {
        this.cachedElements = new Map();
        this.init();
    }

    getElement(selector) {
        if (!this.cachedElements.has(selector)) {
            this.cachedElements.set(selector, document.querySelector(selector));
        }
        return this.cachedElements.get(selector);
    }

    // Debounce example
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}
```

## Template Requirements

### 15. HTML Template Standards
- Include `{% load django_vite %}` at the top
- Always include CSRF form for JavaScript access
- Place JavaScript loading in `{% block page_js %}`
- Use data attributes instead of inline onclick when possible

```html
{% extends "web/app/app_base.html" %}
{% load static %}
{% load django_vite %}

{% block app %}
<!-- Hidden form for CSRF token -->
<form style="display: none;">
    {% csrf_token %}
</form>

<!-- Page content here -->
{% endblock %}

{% block page_js %}
<!-- Always load notification system first -->
{% vite_asset 'assets/javascript/notification-system.js' %}
<!-- Then load page-specific modules -->
{% vite_asset 'assets/javascript/page-specific.js' %}
{% endblock %}
```

### 16. Migration from Inline JavaScript
When converting templates with inline JavaScript:

1. **Extract inline `<script>` tags** into separate `.js` files
2. **Add to Vite config** as new entry point
3. **Build assets** with `npm run build`
4. **Replace inline script** with `{% vite_asset %}` tags
5. **Test functionality** to ensure nothing breaks

## Existing Modular Components

### 17. Available Components
- **NotificationSystem** (`notification-system.js`) - Global notifications
- **CampaignSyncManager** (`campaign-sync-manager.js`) - Campaign sync state
- **CampaignSelectionManager** (`campaign-selection.js`) - Campaign selection page
- **FacebookSettingsManager** (`facebook-settings.js`) - Settings page management  
- **CampaignDetailManager** (`campaign-detail.js`) - Campaign detail page with charts

### 18. Development Workflow
1. Create new `.js` file in `/assets/javascript/`
2. Add entry point to `vite.config.ts`
3. Run `npm run build` to generate bundle
4. Add `{% vite_asset %}` to relevant templates
5. Test functionality works correctly
6. Remove any old inline JavaScript

This modular approach ensures maintainable, scalable, and performant JavaScript code across the entire application while providing excellent user experience through proper notifications and dynamic updates. 