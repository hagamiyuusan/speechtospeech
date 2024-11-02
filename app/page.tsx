"use client";

import clsx from "clsx";
import { useActionState, useEffect, useRef, useState } from "react";
// import { Timeout } from "node";
import { toast } from "sonner";
import { EnterIcon, LoadingIcon } from "@/lib/icons";
import { usePlayer } from "@/lib/usePlayer";
import { track } from "@vercel/analytics";
import { useMicVAD, utils } from "@ricky0123/vad-react";
import { IncomingMessage } from "http";

type Message = {
  role: "user" | "assistant";
  content: string;
  latency?: number;
};


export default function Home() {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const player = usePlayer();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isPending, setIsPending] = useState(false);
  const [inComingMessage, setInComingMessage] = useState("");
  const timeoutRef = useRef<ReturnType<typeof setInterval> | undefined>(
    undefined
  );

  const vad = useMicVAD({
    startOnLoad: true,
    onSpeechEnd: (audio) => {
      const wav = utils.encodeWAV(audio);
      const blob = new Blob([wav], { type: "audio/wav" });
      const transciption = getTranscription(blob);

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
      return "";
    }

    const transcript = await response.text(); // The transcript is now directly in the response body
    setInput(transcript);
  };

  useEffect(() => {
    function keyDown(e: KeyboardEvent) {
      if (e.key === "Enter") return inputRef.current?.focus();
      if (e.key === "Escape") return setInput("");
    }

    window.addEventListener("keydown", keyDown);
    return () => window.removeEventListener("keydown", keyDown);
  });

  const handlerSubmit = async (data: string) => {
    setIsPending(true);
    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ input_text: data }),
    });
    if (!response.body) {
      throw new Error("ReadableStream not supported.");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedMessage = "";
    setInComingMessage("");
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      accumulatedMessage += chunk;
      console.log(chunk);
      setInComingMessage((prev) => prev + chunk);
    }
    setMessages((prevMessages) => [
      ...prevMessages,
      {
        role: "user",
        content: data,
      },
      {
        role: "assistant",
        content: accumulatedMessage,
      },
    ]);
    setIsPending(false);
  };

  useEffect(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      handleVariableUnchanged();
    }, 30000);

    return () => {
      clearTimeout(timeoutRef.current);
    };
  }, [vad.userSpeaking]);

  const handleVariableUnchanged = () => {
    console.log("new section");
  };

  function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    handlerSubmit(input);
  }

  return (
    <>
      <div className="pb-4 min-h-28" />

      <form
        className="rounded-full bg-neutral-200/80 dark:bg-neutral-800/80 flex items-center w-full max-w-3xl border border-transparent hover:border-neutral-300 focus-within:border-neutral-400 hover:focus-within:border-neutral-400 dark:hover:border-neutral-700 dark:focus-within:border-neutral-600 dark:hover:focus-within:border-neutral-600"
        onSubmit={handleFormSubmit}
      >
        <input
          type="text"
          className="bg-transparent focus:outline-none p-4 w-full placeholder:text-neutral-600 dark:placeholder:text-neutral-400"
          required
          placeholder="Ask me anything"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          ref={inputRef}
        />

        <button
          type="submit"
          className="p-4 text-neutral-700 hover:text-black dark:text-neutral-300 dark:hover:text-white"
          disabled={isPending}
          aria-label="Submit"
        >
          {isPending ? <LoadingIcon /> : <EnterIcon />}
        </button>
      </form>

      <div className="text-neutral-400 dark:text-neutral-600 pt-4 text-center max-w-xl text-balance min-h-28 space-y-4">
        <p>{inComingMessage}</p>

        {IncomingMessage.length === 0 && (
          <>
            {vad.loading ? (
              <p>Loading speech detection...</p>
            ) : vad.errored ? (
              <p>Failed to load speech detection.</p>
            ) : (
              <p>Start talking to chat.</p>
            )}
          </>
        )}
      </div>
      <div
        className={clsx(
          "absolute size-36 blur-3xl rounded-full bg-gradient-to-b from-red-200 to-red-400 dark:from-red-600 dark:to-red-800 -z-50 transition ease-in-out",
          {
            "opacity-0": vad.loading || vad.errored,
            "opacity-30": !vad.loading && !vad.errored && !vad.userSpeaking,
            "opacity-100 scale-110": vad.userSpeaking,
          }
        )}
      />
    </>
  );
}

function A(props: any) {
  return (
    <a
      {...props}
      className="text-neutral-500 dark:text-neutral-500 hover:underline font-medium"
    />
  );
}
