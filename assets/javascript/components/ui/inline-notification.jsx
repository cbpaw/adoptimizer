import React from 'react';

const variants = {
  success: {
    container: 'bg-green-50 border border-green-200 text-green-900',
    icon: '✓',
    iconBg: 'bg-green-500'
  },
  error: {
    container: 'bg-red-50 border border-red-200 text-red-900',
    icon: '✕',
    iconBg: 'bg-red-500'
  },
  warning: {
    container: 'bg-yellow-50 border border-yellow-200 text-yellow-900',
    icon: '⚠',
    iconBg: 'bg-yellow-500'
  },
  info: {
    container: 'bg-blue-50 border border-blue-200 text-blue-900',
    icon: 'ℹ',
    iconBg: 'bg-blue-500'
  }
};

export function InlineNotification({
  variant = 'info',
  title,
  message,
  onClose,
  className = '',
  showIcon = true,
  closable = true
}) {
  const [isVisible, setIsVisible] = React.useState(true);

  const handleClose = () => {
    setIsVisible(false);
    if (onClose) {
      setTimeout(onClose, 300); // Allow animation to complete
    }
  };

  if (!isVisible) {
    return null;
  }

  const variantStyles = variants[variant] || variants.info;

  return (
    <div className={`
      relative rounded-lg p-4 mb-4 transition-all duration-300 ease-in-out transform
      ${isVisible ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0'}
      ${variantStyles.container}
      ${className}
    `}>
      <div className="flex items-start">
        {showIcon && (
          <div className={`
            flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-white text-sm font-bold mr-3
            ${variantStyles.iconBg}
          `}>
            {variantStyles.icon}
          </div>
        )}

        <div className="flex-1 min-w-0">
          {title && (
            <h4 className="text-sm font-medium mb-1">
              {title}
            </h4>
          )}
          {message && (
            <p className="text-sm">
              {message}
            </p>
          )}
        </div>

        {closable && (
          <button
            onClick={handleClose}
            className="flex-shrink-0 ml-3 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close notification"
          >
            <span className="text-lg">×</span>
          </button>
        )}
      </div>
    </div>
  );
}