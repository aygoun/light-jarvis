"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Loader2, Mic } from "lucide-react";

interface InputFormProps {
  onSubmit: (message: string) => void;
  isLoading?: boolean;
  onStartListening?: () => void;
  isListening?: boolean;
}

export function InputForm({
  onSubmit,
  isLoading = false,
  onStartListening,
  isListening = false,
}: InputFormProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSubmit(message.trim());
      setMessage("");
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
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask Jarvis anything..."
            disabled={isLoading}
            className="h-16 pr-32 text-lg bg-gray-800/50 backdrop-blur-sm border-2 border-gray-600 focus:border-blue-400 transition-all duration-300 rounded-2xl shadow-2xl hover:shadow-blue-500/20 text-white placeholder:text-gray-400"
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

          {/* Microphone button */}
          <Button
            type="button"
            onClick={onStartListening}
            disabled={isLoading || isListening}
            size="icon"
            className="absolute right-16 top-1/2 -translate-y-1/2 h-10 w-10 rounded-xl bg-gray-700/80 hover:bg-gray-600/80 shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50"
          >
            <Mic className="h-5 w-5" />
          </Button>

          {/* Send button */}
          <Button
            type="submit"
            disabled={!message.trim() || isLoading}
            size="icon"
            className="absolute right-2 top-1/2 -translate-y-1/2 h-12 w-12 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Subtle status text */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="flex items-center justify-center mt-6"
        >
          <span className="text-sm text-gray-500">
            {isLoading
              ? "Processing your request..."
              : "Press Enter or click to send"}
          </span>
        </motion.div>
      </form>
    </motion.div>
  );
}
