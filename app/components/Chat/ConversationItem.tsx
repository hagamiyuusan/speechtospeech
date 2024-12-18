// components/Chat/ConversationItem.tsx
import React from 'react';
import { MessageCircleIcon } from 'lucide-react';
import classNames from 'classnames';
import { Conversation } from '../../types/conversation';

interface ConversationItemProps {
  shortDescription: string;
  isActive: boolean;
  onClick: () => void;
}

const ConversationItem: React.FC<ConversationItemProps> = ({ shortDescription, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={classNames(
      'w-full text-left px-4 py-2 rounded-lg transition-colors duration-200',
      {
        'bg-blue-50 border-blue-100': isActive,
        'hover:bg-gray-100': !isActive,
      }
    )}
    aria-label={`Select conversation: ${shortDescription}`}
    aria-pressed={isActive}
  >
    <div className="flex items-center gap-2">
      <div className="flex-shrink-0"> {/* Added flex-shrink-0 to prevent icon from shrinking */}
        <MessageCircleIcon 
          size={18} 
          className={isActive ? 'text-blue-500' : 'text-gray-500'} 
        />
      </div>
      <span className="text-sm truncate flex-1 text-left">{shortDescription}</span> {/* Added flex-1 and text-left */}
    </div>
  </button>
);

export default ConversationItem;
