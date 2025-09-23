import React from 'react';
import { InlineNotification } from '@/components/ui/inline-notification';

const NotificationContext = React.createContext();

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = React.useState([]);

  const addNotification = React.useCallback((notification) => {
    const id = Date.now() + Math.random();
    const newNotification = { ...notification, id };

    setNotifications(prev => [...prev, newNotification]);

    // Auto-remove after 5 seconds unless specified otherwise
    if (notification.autoClose !== false) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.duration || 5000);
    }

    return id;
  }, []);

  const removeNotification = React.useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearNotifications = React.useCallback(() => {
    setNotifications([]);
  }, []);

  const showSuccess = React.useCallback((title, message, options = {}) => {
    return addNotification({
      variant: 'success',
      title,
      message,
      ...options
    });
  }, [addNotification]);

  const showError = React.useCallback((title, message, options = {}) => {
    return addNotification({
      variant: 'error',
      title,
      message,
      ...options
    });
  }, [addNotification]);

  const showWarning = React.useCallback((title, message, options = {}) => {
    return addNotification({
      variant: 'warning',
      title,
      message,
      ...options
    });
  }, [addNotification]);

  const showInfo = React.useCallback((title, message, options = {}) => {
    return addNotification({
      variant: 'info',
      title,
      message,
      ...options
    });
  }, [addNotification]);

  const value = {
    notifications,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer
        notifications={notifications}
        onRemove={removeNotification}
      />
    </NotificationContext.Provider>
  );
}

function NotificationContainer({ notifications, onRemove }) {
  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <InlineNotification
          key={notification.id}
          variant={notification.variant}
          title={notification.title}
          message={notification.message}
          onClose={() => onRemove(notification.id)}
          className="shadow-lg"
        />
      ))}
    </div>
  );
}

export function useNotifications() {
  const context = React.useContext(NotificationContext);

  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }

  return context;
}

// Higher-order component for easy integration
export function withNotifications(WrappedComponent) {
  return function WithNotificationsComponent(props) {
    return (
      <NotificationProvider>
        <WrappedComponent {...props} />
      </NotificationProvider>
    );
  };
}