/**
 * Card Component - Barakah Trader Lite
 * Reusable card container for educational content
 */

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  onClick?: () => void;
  variant?: 'default' | 'interactive' | 'success' | 'warning' | 'error';
}

const variantStyles = {
  default: 'border-gray-200 bg-white hover:shadow-md',
  interactive: 'border-blue-200 bg-blue-50 hover:bg-blue-100 hover:border-blue-300 cursor-pointer',
  success: 'border-green-200 bg-green-50',
  warning: 'border-yellow-200 bg-yellow-50',
  error: 'border-red-200 bg-red-50',
};

export function Card({ 
  children, 
  title, 
  subtitle, 
  className = "", 
  onClick,
  variant = 'default'
}: CardProps) {
  const baseStyles = "border rounded-lg p-6 transition-all duration-200";
  const variantStyle = variantStyles[variant];
  
  return (
    <div 
      className={`${baseStyles} ${variantStyle} ${className}`}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="mb-4">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-gray-600 text-sm">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}