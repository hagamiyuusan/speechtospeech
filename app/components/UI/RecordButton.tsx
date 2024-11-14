import React, { useState, useRef } from 'react';
import { Mic } from 'lucide-react';
import { toast } from "sonner";

interface RecordButtonProps {
  onTranscription: (text: string) => void;
  onRecordingComplete?: () => void;
  onRecording?: (isRecording: boolean) => void;
}

const RecordButton: React.FC<RecordButtonProps> = ({ onTranscription, onRecordingComplete, onRecording }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const getTranscription = async (blob: Blob) => {
    const formData = new FormData();
    formData.append("input", blob, "audio.mp3");

    try {
      const response = await fetch("/api/voice", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 429) {
          toast.error("Too many requests. Please try again later.");
        } else {
          toast.error((await response.text()) || "An error occurred.");
        }
        return;
      }

      const transcript = await response.text();
      onTranscription(transcript);
      onRecordingComplete?.();
    } catch (error) {
      toast.error("Failed to transcribe audio");
    }
  };

  const startRecording = async () => {
    onRecording?.(true);
    console.log("start recording")
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error("Could not access microphone");
    }
  };

  const stopRecording = () => {
    onRecording?.(false);
    if (!mediaRecorderRef.current) return;

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
      await getTranscription(audioBlob);
      
      // Stop all tracks in the stream
      mediaRecorderRef.current?.stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  return (
    <button
      className={`p-2 rounded-full transition-all ${
        isRecording 
          ? 'bg-red-500 text-white scale-110' 
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onMouseLeave={stopRecording}
      type="button"
      aria-label="Record message"
    >
      <Mic size={40} />
    </button>
  );
};

export default RecordButton;