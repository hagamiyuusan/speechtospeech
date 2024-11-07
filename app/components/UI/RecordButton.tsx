import React, { useState } from 'react';
import { Mic } from 'lucide-react';
import { useMicVAD, utils } from "@ricky0123/vad-react";
import { toast } from "sonner";

interface RecordButtonProps {
  onTranscription: (text: string) => void;
  onRecordingComplete?: () => void;
}

const RecordButton: React.FC<RecordButtonProps> = ({ onTranscription, onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);

  const vad = useMicVAD({
    startOnLoad: true,
    onSpeechEnd: async (audio) => {
      const wav = utils.encodeWAV(audio);
      const blob = new Blob([wav], { type: "audio/wav" });
      await getTranscription(blob);

      const isFirefox = navigator.userAgent.includes("Firefox");
      if (isFirefox) vad.pause();
    },
    workletURL: "/vad.worklet.bundle.min.js",
    modelURL: "/silero_vad.onnx",
    positiveSpeechThreshold: 0.6,
    minSpeechFrames: 4,
    ortConfig(ort) {
      const isSafari = /^((?!chrome|android).)*safari/i.test(
        navigator.userAgent
      );

      ort.env.wasm = {
        wasmPaths: {
          "ort-wasm-simd-threaded.wasm": "/ort-wasm-simd-threaded.wasm",
          "ort-wasm-simd.wasm": "/ort-wasm-simd.wasm",
          "ort-wasm.wasm": "/ort-wasm.wasm",
          "ort-wasm-threaded.wasm": "/ort-wasm-threaded.wasm",
        },
        numThreads: isSafari ? 1 : 4,
      };
    },
  });

  const getTranscription = async (blob: Blob) => {
    const formData = new FormData();
    formData.append("input", blob, "audio.wav");

    try {
      const response = await fetch("/api", {
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

  const startRecording = () => {
    setIsRecording(true);
    vad.start();
  };

  const stopRecording = () => {
    setIsRecording(false);
    vad.pause();
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