/**
 * Loader Component - Barakah Trader Lite
 * Loading states for educational content
 */

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  className?: string;
}

const sizeStyles = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export function Loader({ 
  size = 'md', 
  message, 
  className = "" 
}: LoaderProps) {
  const sizeStyle = sizeStyles[size];
  
  return (
    <div className={`flex flex-col items-center justify-center py-8 ${className}`}>
      <div className={`animate-spin rounded-full border-2 border-gray-200 border-t-blue-600 ${sizeStyle}`} />
      {message && (
        <p className="mt-4 text-gray-600 text-sm">
          {message}
        </p>
      )}
    </div>
  );
}

export function InlineLoader({ size = 'sm' }: { size?: 'sm' | 'md' }) {
  const sizeStyle = sizeStyles[size];
  
  return (
    <div className={`animate-spin rounded-full border-2 border-gray-200 border-t-blue-600 ${sizeStyle}`} />
  );
}