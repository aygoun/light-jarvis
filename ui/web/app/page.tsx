"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { InputForm } from "@/components/input-form";
import { SpeakingBubble } from "@/components/speaking-bubble";

export default function Home() {
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    // Initialize speech recognition
    if (typeof window !== "undefined" && "webkitSpeechRecognition" in window) {
      recognitionRef.current = new (window as any).webkitSpeechRecognition();
      if (recognitionRef.current) {
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = "en-US";

        recognitionRef.current.onresult = (event: any) => {
          const transcript = Array.from(event.results)
            .map((result: any) => result[0])
            .map((result: any) => result.transcript)
            .join("");
          setTranscript(transcript);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
          setIsRecording(false);
        };
      }
    }

    // Initialize speech synthesis
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      synthRef.current = window.speechSynthesis;
    }
  }, []);

  const speakText = (text: string) => {
    if (synthRef.current) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);

      synthRef.current.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript("");
      setIsListening(true);
      setIsRecording(true);
      recognitionRef.current.start();
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setIsRecording(false);
    }
  };

  const handleSubmit = async (message: string) => {
    setIsLoading(true);
    setResponse("");

    // Simulate API call with a beautiful response
    setTimeout(() => {
      const aiResponse = `Thank you for your message: "${message}"

I'm Jarvis, your AI assistant. I'm here to help you with a wide range of tasks including:

• Answering questions and providing information
• Helping with creative writing and brainstorming
• Assisting with problem-solving and analysis
• Providing explanations on complex topics
• And much more!

How can I assist you today? I'm ready to help with whatever you need.`;

      setResponse(aiResponse);
      setIsLoading(false);

      // Automatically speak the response
      speakText(aiResponse);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center relative overflow-hidden">
      {/* Dark background with subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-black to-gray-800" />

      {/* Subtle grid pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.02%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%221%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-30" />

      {/* Main centered content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full max-w-4xl mx-auto px-4">
        {/* Speaking Bubble */}
        <SpeakingBubble
          isSpeaking={isSpeaking}
          response={response}
          isLoading={isLoading}
          onStopSpeaking={stopSpeaking}
          transcript={transcript}
        />

        {/* Input Form at bottom */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-16 w-full max-w-2xl"
        >
          <InputForm
            onSubmit={handleSubmit}
            isLoading={isLoading}
            onStartListening={startListening}
            isListening={isListening}
          />
        </motion.div>

        {/* Response text display below input */}
        {response && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-8 w-full max-w-4xl"
          >
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-6 shadow-2xl">
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
                className="text-gray-300 text-center leading-relaxed whitespace-pre-wrap"
              >
                {response}
              </motion.p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
