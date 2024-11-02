// components/Chat/Sidebar.tsx
import React, { useEffect, useState } from 'react';
import { PlusIcon } from 'lucide-react';
import ConversationItem from './ConversationItem';
import Button from '../UI/Button';

interface ConversationID {
  id: string;
  title: string;
}

interface SidebarProps {
  conversationIDs: ConversationID[];
  selectedId: string;
  onSelect: (id: string) => void;
  onBackToCreateNewChat: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ conversationIDs, selectedId, onSelect, onBackToCreateNewChat }) => {
  const [conversations, setConversations] = useState<ConversationID[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // useEffect(() => {
  //   const fetchConversations = async () => {
  //     try {
  //       const response = await fetch('http://localhost:8000/conversations/', {
  //         method: 'GET',
  //         headers: {
  //           'Content-Type': 'application/json',
  //         },
  //         credentials: 'include'
  //       });
  //       if (!response.ok) throw new Error('Failed to fetch conversations');
  //       const data = await response.json();
  //       setConversations(data);
  //     } catch (error) {
  //       console.error('Error fetching conversations:', error);
  //     } finally {
  //       setIsLoading(false);
  //     }
  //   };
  
  //   fetchConversations();
  // }, []);
  return (
  <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="p-5 border-b border-gray-200">
        <Button onClick={onBackToCreateNewChat} className="w-full flex items-center justify-center gap-2">
          <PlusIcon size={18} />
          New Chat
      </Button>
    </div>
    <nav className="flex-1 overflow-y-auto p-2" role="navigation">
      <div className="space-y-1">
        {conversationIDs.map((conv) => (
          <ConversationItem
            key={conv.id}
            shortDescription={conv.title}
            isActive={selectedId === conv.id}
            onClick={() => onSelect(conv.id)}
          />
        ))}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
