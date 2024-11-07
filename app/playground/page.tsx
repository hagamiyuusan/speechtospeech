// pages/index.tsx
"use client";
import React, { useEffect, useState } from 'react';
import { Sidebar, ChatPanel } from '../components/Chat';
import BlankChat from '@/components/Chat/BlankChat';
import { v4 as uuidv4 } from 'uuid';
import { shortDescription } from '../types/conversation';




const ChatInterface: React.FC = () => {

  const [conversations, setConversations] = useState<shortDescription[]>([]);
  const [activeConversation, setActiveConversation] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [initialMessage, setInitialMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);


  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true);
      try {
        const response = await fetch('http://localhost:8000/conversations/', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });
        if (!response.ok) throw new Error('Failed to fetch short description of conversations');
        const data = await response.json();
        setConversations(data);
      } catch (error) {
        console.error('Error fetching conversations:', error);
      } finally {
        setIsLoading(false);
      }
    };
  
    fetchConversations();
  }, []);

  useEffect(() => {
    setActiveConversation(selectedId !== null);
  }, [selectedId]);

  const backToCreateNewChat = () => {
    setSelectedId(null);
    setActiveConversation(false);
  }

  const handleNewChat = (message: string) => {
    setInitialMessage(message);
    setActiveConversation(true);
    // setConversations([...conversations, newShortDescription]);
    // setSelectedId(newShortDescription.id);
  };



  const updateListConversation = (conversation: shortDescription) => {
    setConversations(prev => [...prev, conversation]);
    setSelectedId(conversation.id);
  };

  return (
    <div className="flex flex-1 h-full w-full bg-white rounded-3xl overflow-hidden shadow-md"
    >
        <Sidebar
          conversations={conversations}
          isLoading={isLoading}
          selectedId={selectedId || ''}
          onSelect={setSelectedId}
          onBackToCreateNewChat={backToCreateNewChat}
        />
      {activeConversation ? (
        <ChatPanel conversationID={selectedId || uuidv4()} initialMessage={initialMessage} updateListConversation={updateListConversation}/>
      ) : (
        <BlankChat onSubmit={(message: string) => handleNewChat(message)} />
      )}
    </div>
  );
};

export default ChatInterface;
