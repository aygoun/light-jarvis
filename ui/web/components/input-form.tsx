"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Loader2, Mic, MicOff, Square } from "lucide-react";

interface InputFormProps {
  onSubmit: (message: string) => void;
  isLoading?: boolean;
  onStartListening?: () => void;
  onStopListening?: () => void;
  isListening?: boolean;
  transcript?: string;
  speechRecognitionAvailable?: boolean;
}

export function InputForm({
  onSubmit,
  isLoading = false,
  onStartListening,
  onStopListening,
  isListening = false,
  transcript = "",
  speechRecognitionAvailable = true,
}: InputFormProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !isListening) {
      onSubmit(message.trim());
      setMessage("");
    }
  };

  const handleMicClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    console.log("Mic button clicked, isListening:", isListening);
    if (isListening) {
      console.log("Stopping listening...");
      onStopListening?.();
    } else {
      console.log("Starting listening...");
      onStartListening?.();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="w-full max-w-2xl mx-auto"
    >
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          {/* Input field with listening state */}
          <AnimatePresence mode="wait">
            {isListening ? (
              <motion.div
                key="listening"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="relative"
              >
                <Input
                  value={transcript || "Listening..."}
                  placeholder="Listening..."
                  disabled={true}
                  className="h-16 pr-36 text-lg bg-red-900/20 backdrop-blur-sm border-2 border-red-500/50 transition-all duration-300 rounded-2xl shadow-2xl text-white placeholder:text-red-300"
                />

                {/* Pulsing red glow effect */}
                <motion.div
                  animate={{
                    opacity: [0.2, 0.6, 0.2],
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="absolute inset-0 rounded-2xl bg-gradient-to-r from-red-500/20 to-pink-500/20 pointer-events-none"
                />

                {/* Animated listening indicator */}
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.7, 1, 0.7],
                  }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center space-x-2"
                >
                  <div className="flex space-x-1">
                    <motion.div
                      animate={{ height: [4, 16, 4] }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0,
                      }}
                      className="w-1 bg-red-400 rounded-full"
                    />
                    <motion.div
                      animate={{ height: [4, 20, 4] }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.1,
                      }}
                      className="w-1 bg-red-400 rounded-full"
                    />
                    <motion.div
                      animate={{ height: [4, 12, 4] }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.2,
                      }}
                      className="w-1 bg-red-400 rounded-full"
                    />
                    <motion.div
                      animate={{ height: [4, 18, 4] }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: 0.3,
                      }}
                      className="w-1 bg-red-400 rounded-full"
                    />
                  </div>
                  <span className="text-red-300 text-sm font-medium">
                    Listening...
                  </span>
                </motion.div>
              </motion.div>
            ) : (
              <motion.div
                key="normal"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="relative"
              >
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask Jarvis anything..."
                  disabled={isLoading}
                  className="h-16 pr-36 text-lg bg-gray-800/50 backdrop-blur-sm border-2 border-gray-600 focus:border-blue-400 transition-all duration-300 rounded-2xl shadow-2xl hover:shadow-blue-500/20 text-white placeholder:text-gray-400"
                />

                {/* Animated background glow */}
                <motion.div
                  animate={{
                    opacity: [0.1, 0.3, 0.1],
                    scale: [1, 1.02, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 pointer-events-none"
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Microphone button */}
          <Button
            type="button"
            onClick={handleMicClick}
            disabled={isLoading || !speechRecognitionAvailable}
            size="icon"
            className={`absolute right-16 top-1/2 -translate-y-1/2 h-10 w-10 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 hover:scale-105 active:scale-95 z-10 ${
              isListening
                ? "bg-red-600 hover:bg-red-700 text-white"
                : speechRecognitionAvailable
                ? "bg-gray-700/80 hover:bg-gray-600/80"
                : "bg-gray-500/50 cursor-not-allowed"
            }`}
            style={{ zIndex: 10 }}
            title={
              !speechRecognitionAvailable
                ? "Speech recognition not available"
                : ""
            }
          >
            <AnimatePresence mode="wait">
              {isListening ? (
                <motion.div
                  key="stop"
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: 90 }}
                  transition={{ duration: 0.2 }}
                >
                  <Square className="h-5 w-5" />
                </motion.div>
              ) : (
                <motion.div
                  key="mic"
                  initial={{ opacity: 0, rotate: 90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  exit={{ opacity: 0, rotate: -90 }}
                  transition={{ duration: 0.2 }}
                >
                  <Mic className="h-5 w-5" />
                </motion.div>
              )}
            </AnimatePresence>
          </Button>

          {/* Send button */}
          <Button
            type="submit"
            disabled={!message.trim() || isLoading || isListening}
            size="icon"
            className="absolute right-2 top-1/2 -translate-y-1/2 h-12 w-12 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 hover:scale-105 active:scale-95 z-10"
            style={{ zIndex: 10 }}
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Status text */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="flex items-center justify-center mt-6"
        >
          <AnimatePresence mode="wait">
            {isListening ? (
              <motion.span
                key="listening-status"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-sm text-red-400 flex items-center space-x-2"
              >
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{
                    duration: 1,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                  className="w-2 h-2 bg-red-400 rounded-full"
                />
                <span>Click the stop button to finish recording</span>
              </motion.span>
            ) : isLoading ? (
              <motion.span
                key="loading-status"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-sm text-gray-500"
              >
                Processing your request...
              </motion.span>
            ) : (
              <motion.span
                key="normal-status"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-sm text-gray-500"
              >
                Press Enter or click to send • Click mic to record (local
                transcription)
              </motion.span>
            )}
          </AnimatePresence>
        </motion.div>
      </form>
    </motion.div>
  );
}
