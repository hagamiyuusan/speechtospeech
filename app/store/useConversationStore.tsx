import { create } from 'zustand';
import { shortDescription } from '../types/conversation';

interface ConversationStore {
  conversations: shortDescription[];
  selectedId: string | null;
  isLoading: boolean;
  setConversations: (conversations: shortDescription[]) => void;
  addConversation: (conversation: shortDescription) => void;
  setSelectedId: (id: string | null) => void;
  setIsLoading: (loading: boolean) => void;
  fetchConversations: () => Promise<void>;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  selectedId: null,
  isLoading: false,
  
  setConversations: (conversations) => set({ conversations }),
  addConversation: (conversation) => 
    set((state) => ({ conversations: [conversation, ...state.conversations] })),
  setSelectedId: (id) => set({ selectedId: id }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  
  fetchConversations: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch('http://localhost:8000/conversations/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch conversations');
      const data = await response.json();
      set({ conversations: data });
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      set({ isLoading: false });
    }
  }
}));