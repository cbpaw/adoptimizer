/**
 * Global Notification System
 * Provides a reusable notification system for the entire application
 */

class NotificationSystem {
    constructor(containerId = 'notification-container') {
        this.containerId = containerId;
        this.ensureContainer();
    }

    /**
     * Ensure notification container exists
     */
    ensureContainer() {
        let container = document.getElementById(this.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.containerId;
            container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    /**
     * Show a notification
     * @param {string} message - The notification message
     * @param {string} type - The notification type (success, error, warning, info)
     * @param {Object} options - Additional options
     * @param {number} options.duration - Duration in milliseconds (0 = no auto-remove)
     * @param {boolean} options.closeable - Whether the notification can be manually closed
     * @param {string} options.position - Position (bottom-right, top-right, etc.)
     * @returns {string} Notification ID
     */
    show(message, type = 'info', options = {}) {
        const config = {
            duration: 5000,
            closeable: true,
            position: 'bottom-right',
            ...options
        };

        const notificationId = 'notification-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const container = document.getElementById(this.containerId);

        if (!container) {
            console.error('Notification container not found');
            return null;
        }

        const notification = this.createNotificationElement(notificationId, message, type, config);
        container.appendChild(notification);

        // Trigger animation
        this.animateIn(notification);

        // Auto-remove if duration is set
        if (config.duration > 0) {
            setTimeout(() => {
                this.remove(notificationId);
            }, config.duration);
        }

        return notificationId;
    }

    /**
     * Create notification element
     * @param {string} id - Notification ID
     * @param {string} message - Message text
     * @param {string} type - Notification type
     * @param {Object} config - Configuration options
     * @returns {HTMLElement} Notification element
     */
    createNotificationElement(id, message, type, config) {
        const notification = document.createElement('div');
        notification.id = id;
        
        const typeConfig = this.getTypeConfig(type);
        
        notification.className = `${typeConfig.classes} border rounded-lg p-4 shadow-lg max-w-sm transition-all duration-300 transform translate-x-full opacity-0`;
        
        notification.innerHTML = `
            <div class="flex items-start gap-2">
                
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium break-words">${this.escapeHtml(message)}</p>
                </div>
                ${config.closeable ? `
                    <button onclick="window.notificationSystem.remove('${id}')" 
                            class="text-gray-400 hover:text-gray-600 flex-shrink-0 ml-2" 
                            aria-label="Sluiten">
                        <i class="fas fa-times text-xs"></i>
                    </button>
                ` : ''}
            </div>
        `;

        return notification;
    }

    /**
     * Get type-specific configuration
     * @param {string} type - Notification type
     * @returns {Object} Type configuration
     */
    getTypeConfig(type) {
        const configs = {
            success: {
                classes: 'bg-green-50 border-green-200 text-green-800',
                icon: 'fas fa-check-circle text-green-500'
            },
            error: {
                classes: 'bg-red-50 border-red-200 text-red-800',
                icon: 'fas fa-exclamation-circle text-red-500'
            },
            warning: {
                classes: 'bg-yellow-50 border-yellow-200 text-yellow-800',
                icon: 'fas fa-exclamation-triangle text-yellow-500'
            },
            info: {
                classes: 'bg-blue-50 border-blue-200 text-blue-800',
                icon: 'fas fa-info-circle text-blue-500'
            }
        };

        return configs[type] || configs.info;
    }

    /**
     * Animate notification in
     * @param {HTMLElement} notification - Notification element
     */
    animateIn(notification) {
        // Small delay to ensure element is in DOM
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
            notification.classList.add('translate-x-0', 'opacity-100');
        }, 10);
    }

    /**
     * Animate notification out and remove
     * @param {HTMLElement} notification - Notification element
     * @param {Function} callback - Callback after animation
     */
    animateOut(notification, callback) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            if (callback) callback();
        }, 300);
    }

    /**
     * Remove a notification by ID
     * @param {string} notificationId - The notification ID
     */
    remove(notificationId) {
        const notification = document.getElementById(notificationId);
        if (notification) {
            this.animateOut(notification);
        }
    }

    /**
     * Remove all notifications
     */
    removeAll() {
        const container = document.getElementById(this.containerId);
        if (container) {
            const notifications = container.querySelectorAll('[id^="notification-"]');
            notifications.forEach(notification => {
                this.animateOut(notification);
            });
        }
    }

    /**
     * Show success notification
     * @param {string} message - Success message
     * @param {Object} options - Additional options
     * @returns {string} Notification ID
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    /**
     * Show error notification
     * @param {string} message - Error message
     * @param {Object} options - Additional options
     * @returns {string} Notification ID
     */
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    /**
     * Show warning notification
     * @param {string} message - Warning message
     * @param {Object} options - Additional options
     * @returns {string} Notification ID
     */
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    /**
     * Show info notification
     * @param {string} message - Info message
     * @param {Object} options - Additional options
     * @returns {string} Notification ID
     */
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Update container position
     * @param {string} position - Position class (e.g., 'top-right', 'bottom-left')
     */
    setPosition(position) {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // Remove existing position classes
        container.className = container.className.replace(/(?:top|bottom|left|right)-\d+/g, '');
        
        // Add new position classes based on position string
        const positionClasses = {
            'top-right': 'fixed top-4 right-4 z-50 space-y-2',
            'top-left': 'fixed top-4 left-4 z-50 space-y-2',
            'bottom-right': 'fixed bottom-4 right-4 z-50 space-y-2',
            'bottom-left': 'fixed bottom-4 left-4 z-50 space-y-2',
            'top-center': 'fixed top-4 left-1/2 transform -translate-x-1/2 z-50 space-y-2',
            'bottom-center': 'fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50 space-y-2'
        };

        container.className = positionClasses[position] || positionClasses['bottom-right'];
    }

    /**
     * Get count of active notifications
     * @returns {number} Number of active notifications
     */
    getActiveCount() {
        const container = document.getElementById(this.containerId);
        return container ? container.querySelectorAll('[id^="notification-"]').length : 0;
    }

    /**
     * Check if notifications are supported (for feature detection)
     * @returns {boolean} Whether notifications are supported
     */
    isSupported() {
        return typeof document !== 'undefined' && 
               document.createElement && 
               document.getElementById;
    }
}

// Create global instance
window.notificationSystem = new NotificationSystem();

// Create convenience global functions for backward compatibility
window.showNotification = (message, type, duration) => window.notificationSystem.show(message, type, { duration });
window.showSuccess = (message, options) => window.notificationSystem.success(message, options);
window.showError = (message, options) => window.notificationSystem.error(message, options);
window.showWarning = (message, options) => window.notificationSystem.warning(message, options);
window.showInfo = (message, options) => window.notificationSystem.info(message, options);

// Export for module use if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
} 