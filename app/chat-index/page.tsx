// pages/index.tsx
"use client";
import React, { useEffect, useState } from 'react';
import { Sidebar, ChatPanel } from '../components/Chat';
import { Conversation } from '../types/conversation';
import BlankChat from '@/components/Chat/BlankChat';
import { v4 as uuidv4 } from 'uuid';


interface shortDescription {
  id: string;
  title: string;
}


const ChatInterface: React.FC = () => {

  const [conversations, setConversations] = useState<shortDescription[]>([]);
  const [activeConversation, setActiveConversation] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchConversations()
  }, [])

  
  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:8000/conversations')
      const data = await response.json()
      setConversations(data)
    } catch (error) {
      console.error('Error fetching conversations:', error)
    }
  }


  useEffect(() => {
    setActiveConversation(selectedId !== null);
  }, [selectedId]);

  const backToCreateNewChat = () => {
    setSelectedId(null);
    setActiveConversation(false);
  }

  const handleNewChat = (message: string) => {
    const newShortDescription: shortDescription = {
      id: uuidv4(),
      title: 'New Chat',
    };
    
    setConversations([...conversations, newShortDescription]);
    setSelectedId(newShortDescription.id);
  };


  return (
    <div className="flex flex-1 h-full w-full bg-white"
    >
        <Sidebar
          conversationIDs={conversations}
          selectedId={selectedId || ''}
          onSelect={setSelectedId}
          onBackToCreateNewChat={backToCreateNewChat}
        />
      {activeConversation ? (
        <ChatPanel conversationID={selectedId || ''} initialMessage={''}/>
      ) : (
        <BlankChat onSubmit={(message: string) => handleNewChat(message)} />
      )}
    </div>
  );
};

export default ChatInterface;
