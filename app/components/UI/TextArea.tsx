// components/UI/TextArea.tsx
import React from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const TextArea: React.FC<TextAreaProps> = (props) => {
  return (
    <textarea
      className="flex-1 resize-none border-0 focus:ring-0 p-2 h-10 max-h-40 outline-none"
      {...props}
    />
  );
};

export default TextArea;
