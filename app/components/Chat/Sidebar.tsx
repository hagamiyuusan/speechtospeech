// components/Chat/Sidebar.tsx
import React, { useEffect, useState } from 'react';
import { PlusIcon, Loader2 } from 'lucide-react';
import ConversationItem from './ConversationItem';
import Button from '../UI/Button';
import { shortDescription } from '@/types/conversation';


interface SidebarProps {
  selectedId: string;
  onSelect: (id: string) => void;
  onBackToCreateNewChat: () => void;
  conversations: shortDescription[];
  isLoading: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ selectedId,
  onSelect,
  onBackToCreateNewChat,
  conversations,
  isLoading }) => {
  
  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col h-screen">
      <div className="p-5 border-b border-gray-200 flex-shrink-0">
        <Button onClick={onBackToCreateNewChat} className="w-full flex items-center justify-center gap-2">
          <PlusIcon size={18} />
          New Chat
        </Button>
      </div>
      <nav className="flex-1 overflow-y-auto p-2 scrollbar-none" role="navigation">
        {isLoading ? (
          <div className="flex justify-center items-center h-20">
            <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <ConversationItem
                key={conv.id}
                shortDescription={conv.title}
                isActive={selectedId === conv.id}
                onClick={() => onSelect(conv.id)}
              />
            ))}
          </div>
        )}
      </nav>
    </aside>
  );
};

export default Sidebar;
