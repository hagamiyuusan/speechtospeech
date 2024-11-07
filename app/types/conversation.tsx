export type Message = {
    id: string;
    role: string;
    content: string;
  };
  
  export type Conversation = {
    id: string;
    title: string;
    messages: Message[];
  };

export type shortDescription = {
  id: string;
  title: string;
}
