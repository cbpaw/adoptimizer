import React from 'react';
import { InlineNotification } from '@/components/ui/inline-notification';

// Global notification manager for page-level notifications
class PageNotificationManager {
  constructor() {
    this.listeners = new Set();
    this.notifications = [];
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach(listener => listener(this.notifications));
  }

  add(notification) {
    const id = Date.now() + Math.random();
    const newNotification = { ...notification, id };
    this.notifications = [...this.notifications, newNotification];
    this.notify();

    // Auto-remove after 5 seconds unless specified otherwise
    if (notification.autoClose !== false) {
      setTimeout(() => {
        this.remove(id);
      }, notification.duration || 5000);
    }

    return id;
  }

  remove(id) {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notify();
  }

  clear() {
    this.notifications = [];
    this.notify();
  }

  success(title, message, options = {}) {
    return this.add({
      variant: 'success',
      title,
      message,
      ...options
    });
  }

  error(title, message, options = {}) {
    return this.add({
      variant: 'error',
      title,
      message,
      ...options
    });
  }

  warning(title, message, options = {}) {
    return this.add({
      variant: 'warning',
      title,
      message,
      ...options
    });
  }

  info(title, message, options = {}) {
    return this.add({
      variant: 'info',
      title,
      message,
      ...options
    });
  }
}

// Global instance
const pageNotifications = new PageNotificationManager();

// React component for displaying page notifications
export function PageNotifications({ className = '' }) {
  const [notifications, setNotifications] = React.useState([]);

  React.useEffect(() => {
    const unsubscribe = pageNotifications.subscribe(setNotifications);
    return unsubscribe;
  }, []);

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {notifications.map((notification) => (
        <InlineNotification
          key={notification.id}
          variant={notification.variant}
          title={notification.title}
          message={notification.message}
          onClose={() => pageNotifications.remove(notification.id)}
        />
      ))}
    </div>
  );
}

// Export the global manager for use anywhere
export { pageNotifications };

// Hook for using page notifications
export function usePageNotifications() {
  return {
    success: pageNotifications.success.bind(pageNotifications),
    error: pageNotifications.error.bind(pageNotifications),
    warning: pageNotifications.warning.bind(pageNotifications),
    info: pageNotifications.info.bind(pageNotifications),
    add: pageNotifications.add.bind(pageNotifications),
    remove: pageNotifications.remove.bind(pageNotifications),
    clear: pageNotifications.clear.bind(pageNotifications)
  };
}