import { MessageSquare } from 'lucide-react'
import Button from '../UI/Button'
import { ReactTyped } from "react-typed";
export default function Component({ onSubmit }: { onSubmit: (message: string) => void }) {
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
          <ReactTyped strings={['start a new one to begin chatting.',
            'start a new journey to begin.',
            'start a new adventure to begin.'
          ]} typeSpeed={40}
          backSpeed={40}
          /> {/* Updated component */}
        </p>
        <div className='justify-center'>
          <input
            type="text"
            placeholder="Type your message and press Enter..."
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                onSubmit(e.currentTarget.value.trim());
                e.currentTarget.value = '';
              }
            }}
            className="w-full px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600 dark:focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  )
}