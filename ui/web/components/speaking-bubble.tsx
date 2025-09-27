"use client";

import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { Pause, Square, Play } from "lucide-react";

interface SpeakingBubbleProps {
  isSpeaking: boolean;
  onStopSpeaking?: () => void;
  onPauseSpeaking?: () => void;
  onResumeSpeaking?: () => void;
  isPaused?: boolean;
}

export function SpeakingBubble({
  isSpeaking,
  onStopSpeaking,
  onPauseSpeaking,
  onResumeSpeaking,
  isPaused = false,
}: SpeakingBubbleProps) {
  const delays = useMemo(
    () => Array.from({ length: 3 }, () => Math.random() * 2),
    []
  );

  return (
    <div className="relative flex items-center justify-center w-80 h-80">
      {/* Main clickable blob */}
      <motion.button
        onClick={
          isSpeaking
            ? isPaused
              ? onResumeSpeaking
              : onPauseSpeaking
            : undefined
        }
        disabled={!isSpeaking}
        className={`relative w-72 h-72 rounded-full flex items-center justify-center overflow-hidden ${
          isSpeaking ? "cursor-pointer" : "cursor-default"
        }`}
        whileHover={isSpeaking ? { scale: 1.05 } : {}}
        whileTap={isSpeaking ? { scale: 0.95 } : {}}
      >
        {/* Core neon blob */}
        <motion.div
          className="absolute inset-0 rounded-full bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500"
          animate={{
            borderRadius: isSpeaking
              ? [
                  "50% 50% 50% 50%",
                  "60% 40% 70% 30%",
                  "40% 60% 30% 70%",
                  "50% 50% 50% 50%",
                ]
              : "50% 50% 50% 50%",
            scale: isSpeaking ? [1, 1.07, 0.96, 1] : 1,
          }}
          transition={{
            duration: 6,
            repeat: isSpeaking ? Infinity : 0,
            ease: "easeInOut",
          }}
        />

        {/* Neon blur glows */}
        {delays.map((d, i) => (
          <motion.div
            key={i}
            className="absolute inset-0 rounded-full blur-3xl bg-gradient-to-tr from-blue-400/40 via-fuchsia-500/30 to-purple-400/40"
            animate={{
              scale: isSpeaking ? [1, 1.2, 0.9, 1] : 1,
              opacity: isSpeaking ? [0.3, 0.7, 0.3] : 0,
            }}
            transition={{
              duration: 4 + i,
              repeat: isSpeaking ? Infinity : 0,
              ease: "easeInOut",
              delay: d,
            }}
          />
        ))}

        {/* Inner white-ish highlight for depth */}
        <motion.div
          className="absolute w-24 h-24 rounded-full bg-white/40 blur-2xl"
          animate={{
            x: isSpeaking ? [0, 20, -15, 0] : 0,
            y: isSpeaking ? [0, -15, 10, 0] : 0,
            opacity: isSpeaking ? [0.4, 0.8, 0.4] : 0.3,
          }}
          transition={{
            duration: 5,
            repeat: isSpeaking ? Infinity : 0,
            ease: "easeInOut",
          }}
        />
      </motion.button>

      {/* Floating neon sparks */}
      {isSpeaking &&
        [...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-4 h-4 rounded-full blur-md bg-gradient-to-br from-blue-400 to-purple-500"
            style={{
              left: `${50 + 55 * Math.cos((i * 60 * Math.PI) / 180)}%`,
              top: `${50 + 55 * Math.sin((i * 60 * Math.PI) / 180)}%`,
            }}
            animate={{
              y: [0, -25, 0],
              x: [0, (Math.random() - 0.5) * 20, 0],
              opacity: [0.2, 0.9, 0.2],
              scale: [0.8, 1.3, 0.8],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              delay: i * 0.4,
              ease: "easeInOut",
            }}
          />
        ))}
    </div>
  );
}
