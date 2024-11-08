import { MessageSquare } from 'lucide-react'
import { ReactTyped } from "react-typed";
import RecordButton from '../UI/RecordButton';
import { useRef, useState } from 'react';

export default function Component({ onSubmit }: { onSubmit: (message: string) => void }) {
  const [input, setInput] = useState(""); // Add this state
  const formRef = useRef<HTMLFormElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (input.trim()) {
      onSubmit(input.trim());
      setInput("");
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center">
      <div className="text-center space-y-6 max-w-md px-4">
        <div className="bg-white dark:bg-gray-800 rounded-full p-6 inline-block shadow-lg">
          <MessageSquare className="w-12 h-12 text-gray-400 dark:text-gray-500" />
        </div>
        <p className=" text-2xl font-bold text-gray-900 dark:text-gray-100">
          Choose an existing conversation from the sidebar or {" "}
        </p>
        <p className='inline text-blue-600 text-2xl font-bold'>
          <ReactTyped strings={[
            'start a new journey to begin.',
            'start a new adventure to begin.',
            'start a new one to begin chatting.'
          ]} typeSpeed={40}
          backSpeed={40}
          /> {/* Updated component */}
        </p>
        <div className='justify-center'>

        </div>

      </div>
      <form ref={formRef} onSubmit={handleSubmit} className='w-1/2 flex gap-2'>
        <input
          type="text"
          placeholder="Talk to me or type your message and press Enter..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 px-4 py-4 text-gray-700 bg-white border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 dark:focus:ring-blue-500"
        />
        <RecordButton 
          onTranscription={setInput}
          onRecordingComplete={() => handleSubmit()}
        />
      </form>
    </div>
  );
}