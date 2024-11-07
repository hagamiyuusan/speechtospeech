// components/Chat/ChatPanel.tsx
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { PauseIcon, MenuIcon, UserIcon, BotIcon, LoaderIcon, SendIcon } from 'lucide-react';
import IconButton from '../UI/IconButton';
import TextArea from '../UI/TextArea';
import { Message, shortDescription } from '@/types/conversation';
import { v4 as uuidv4 } from 'uuid';
import ReactMarkdown from 'react-markdown';

interface ChatPanelProps {
  conversationID: string | null;
  initialMessage: string;
  updateListConversation: (conversation: shortDescription) => void;
}




const ChatPanel: React.FC<ChatPanelProps> = ({ conversationID, initialMessage, updateListConversation }) => {

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);
  const [title, setTitle] = useState("New Chat");
  const [streamedContent, setStreamedContent] = useState('');
  const initialMessageSentRef = useRef(false);
  const playTextToSpeech = useCallback(async (text: string) => {
    try {
      console.log("text", text);
      const response = await fetch('http://localhost:8000/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        
        body: JSON.stringify({ text }),
      });

      if (!response.ok) throw new Error('TTS request failed');

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      await audio.play();

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
    } catch (error) {
      console.error('Error playing TTS:', error);
    }
  }, []);


  const getConversation = async () => {
    const response = await fetch(`http://localhost:8000/conversation/${conversationID}`);
    return response.json();
  }

  useEffect(() => {
    const loadConversation = async () => {
      if (!conversationID) return;
      
      try {
        setMessages([]);
        const data = await getConversation();
        if (!data) {
          console.log("no data");
          console.log(conversationID);
          if (initialMessage && !initialMessageSentRef.current) {
            initialMessageSentRef.current = true;
            await handleSend(initialMessage);
            const valConversation  =  await getConversation();
            console.log("full conversation", valConversation);
            console.log("title", valConversation?.title );
            if (valConversation) {
              setTitle(valConversation.title);
              updateListConversation({
                id: conversationID,
                title: valConversation.title
              });
            }
          }
        } else {
          console.log("data", data.messages);
          setMessages(data.messages || []);
          setTitle(data.title);
          initialMessageSentRef.current = true;
        }
      } catch (error) {
        console.error('Error loading conversation:', error);
        if (initialMessage && !initialMessageSentRef.current) {
          initialMessageSentRef.current = true;
          await handleSend(initialMessage);
        }
      }
    };

    loadConversation();
  }, [conversationID, initialMessage]);


  useEffect(() => {
    messageRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamedContent]);

  useEffect(() => {
    initialMessageSentRef.current = false;
  }, [conversationID]);


  const handleSend = async (message: string) => {
    if (message.trim() === "") return;

    const userMessage: Message = {
      id: uuidv4(),
      role: "user",
      content: message,
    };

    setMessages(prevMessages => {const newMessages = [...prevMessages, userMessage];
      return newMessages;
    });
    setInput("");
    setIsSending(true);
    setStreamedContent("");

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          conversation_id: conversationID,
          message: userMessage
        }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.content) {
              setStreamedContent(prev => prev + data.content);
            }
            if (data.full_response) {
              setMessages(prev => [...prev, {
                id: data.id,
                role: 'assistant',
                content: data.full_response
              }]);
              setStreamedContent('');
              playTextToSpeech(data.full_response);
            }
            if (data.done) {
              
              break;
            }
          } catch (e) {
            console.error('Error parsing chunk:', e);
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSending(false);
    }
  };


  return (
    <main className="flex-1 flex flex-col h-screen h-screen-padded">
      <header className="border-b border-gray-200 p-5 flex-shrink-0">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{title}</h1>
        <div className="flex items-center gap-2">
          <IconButton icon={<PauseIcon size={20} className="text-gray-600" />} aria-label="Pause conversation" />
          <IconButton icon={<MenuIcon size={20} className="text-gray-600" />} aria-label="Open menu" />
        </div>
      </div>
    </header>
    <div className="flex-1 overflow-y-auto">      
      <div className="p-4">
        <div className="space-y-6 max-w-4xl mx-auto">
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : ''}`}>
            <div className={`flex gap-4 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'
                }`}
              >
                {message.role === 'user' ? (
                  <UserIcon size={20} className="text-blue-600" />
                ) : (
                  <BotIcon size={20} className="text-gray-600" />
                )}
              </div>
              <div>
                <div
                  className={`rounded-lg p-4 ${
                    message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100'
                  }`}
                >
                  <ReactMarkdown className="whitespace-pre-wrap">{message.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          </div>
        ))}
        {isSending  && (
            <div className="flex gap-4 justify-start">
              <div className={`flex gap-4 max-w-[80%]`}>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center bg-gray-100`}
                >
                  <BotIcon size={20} className="text-gray-600" />
                </div>
                <div>
                  <div
                    className={`rounded-lg p-4 bg-gray-100`}
                  >
                    <ReactMarkdown className="whitespace-pre-wrap">{streamedContent}</ReactMarkdown>
                    <span className="inline-block w-2 h-4 bg-gray-500 ml-1 animate-blink"></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messageRef} />
        </div>
      </div>
    </div>

    <footer className="border-t border-gray-200 p-4 flex-shrink-0">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-2">
          <TextArea 
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isSending}
          />
          <IconButton icon={<SendIcon size={20} className="text-blue-600" />}
           aria-label="Send message"
           onClick={() => handleSend(input)}
           disabled={isSending}
           />
        </div>
      </div>
    </footer>
  </main>
  );
};

export default ChatPanel;
