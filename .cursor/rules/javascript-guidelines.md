## Notification System

- **NEVER use alert(), confirm(), or prompt()** - These are prohibited
- **ALWAYS use the notification popup system** with showError(), showSuccess(), showWarning(), showInfo()
- Place notification container: `<div id="notification-container" class="fixed bottom-4 right-4 z-50 space-y-2">`
- Notifications auto-dismiss after 5 seconds and have manual close buttons
- Use semantic colors: red for errors, green for success, yellow for warnings, blue for info

## Dynamic Updates vs Page Refresh

- **AVOID location.reload()** whenever possible - prefer dynamic updates
- **ALWAYS use dynamic data updates** instead of full page refresh for better UX
- Use fetch() to get fresh data and update only the necessary DOM elements
- Show loading indicators during dynamic updates
- Re-attach event listeners after dynamically updating content
- Only use page refresh as a fallback when dynamic updates fail
- Provide smooth transitions and animations for dynamic content changes

## Error Handling 