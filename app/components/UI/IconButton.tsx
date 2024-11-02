// components/UI/IconButton.tsx
import React from 'react';
import classNames from 'classnames';

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  'aria-label': string;
}

const IconButton: React.FC<IconButtonProps> = ({ icon, className, ...props }) => {
  const baseStyles = 'p-2 hover:bg-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500';

  return (
    <button className={classNames(baseStyles, className)} {...props}>
      {icon}
    </button>
  );
};

export default IconButton;
