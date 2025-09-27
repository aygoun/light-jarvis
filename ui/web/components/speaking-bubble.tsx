"use client";

import { motion } from "framer-motion";
// No icons needed for the simplified bubble

interface SpeakingBubbleProps {
  isSpeaking: boolean;
  response: string;
  isLoading: boolean;
  onStopSpeaking: () => void;
  transcript: string;
}

export function SpeakingBubble({
  isSpeaking,
  response,
  isLoading,
  onStopSpeaking,
  transcript,
}: SpeakingBubbleProps) {
  return (
    <div className="relative flex items-center justify-center">
      {/* Main bubble */}
      <motion.div
        animate={{
          scale: isSpeaking ? [1, 1.1, 1] : 1,
          y: isSpeaking ? [0, -10, 0] : 0,
        }}
        transition={{
          duration: 1.5,
          repeat: isSpeaking ? Infinity : 0,
          ease: "easeInOut",
        }}
        className="relative"
      >
        {/* Outer glow ring with Siri-like colors */}
        <motion.div
          animate={{
            scale: isSpeaking ? [1, 1.4, 1] : 1,
            opacity: isSpeaking ? [0.2, 0.6, 0.2] : 0,
          }}
          transition={{
            duration: 2.5,
            repeat: isSpeaking ? Infinity : 0,
            ease: "easeInOut",
          }}
          className="absolute inset-0 w-80 h-80 bg-gradient-to-r from-blue-400/30 via-purple-500/20 to-pink-500/30 rounded-full blur-2xl"
        />

        {/* Secondary glow for depth */}
        <motion.div
          animate={{
            scale: isSpeaking ? [1, 1.6, 1] : 1,
            opacity: isSpeaking ? [0.1, 0.4, 0.1] : 0,
          }}
          transition={{
            duration: 3,
            repeat: isSpeaking ? Infinity : 0,
            ease: "easeInOut",
            delay: 0.5,
          }}
          className="absolute inset-0 w-80 h-80 bg-gradient-to-r from-blue-300/20 via-purple-400/15 to-pink-400/20 rounded-full blur-3xl"
        />

        {/* Main bubble container - clickable to stop speaking */}
        <motion.button
          onClick={isSpeaking ? onStopSpeaking : undefined}
          disabled={!isSpeaking}
          className={`relative w-80 h-80 rounded-full shadow-2xl flex items-center justify-center overflow-hidden ${
            isSpeaking ? "cursor-pointer" : "cursor-default"
          }`}
          whileHover={isSpeaking ? { scale: 1.05 } : {}}
          whileTap={isSpeaking ? { scale: 0.95 } : {}}
        >
          {/* Siri-like gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 rounded-full" />

          {/* Inner glow effect */}
          <div className="absolute inset-2 bg-gradient-to-tr from-blue-300/30 via-purple-400/20 to-pink-400/30 rounded-full blur-sm" />

          {/* Highlight effect */}
          <div className="absolute top-4 left-4 w-24 h-24 bg-gradient-to-br from-white/40 to-transparent rounded-full blur-md" />

          {/* Bottom accent */}
          <div className="absolute bottom-6 right-6 w-16 h-16 bg-gradient-to-tl from-pink-400/60 to-transparent rounded-full blur-sm" />

          {/* Status text */}
          <motion.div
            animate={{
              opacity: isSpeaking ? [0.6, 1, 0.6] : 1,
              scale: isSpeaking ? [0.95, 1.05, 0.95] : 1,
            }}
            transition={{
              duration: 1.5,
              repeat: isSpeaking ? Infinity : 0,
              ease: "easeInOut",
            }}
            className="relative z-10 text-white/90 text-sm font-semibold drop-shadow-lg"
          >
            {isLoading ? "Thinking..." : isSpeaking ? "Click to stop" : "Ready"}
          </motion.div>

          {/* Siri-like sound waves */}
          {isSpeaking && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex items-center justify-center space-x-2">
                {[...Array(7)].map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{
                      height: [8, 32, 8],
                      opacity: [0.4, 1, 0.4],
                      scaleY: [0.5, 1.2, 0.5],
                    }}
                    transition={{
                      duration: 0.8,
                      repeat: Infinity,
                      delay: i * 0.15,
                      ease: "easeInOut",
                    }}
                    className="w-1.5 bg-white/80 rounded-full shadow-lg"
                    style={{ height: 8 }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Siri-like pulsing rings */}
          {isSpeaking && (
            <>
              <motion.div
                animate={{
                  scale: [1, 1.1, 1],
                  opacity: [0.3, 0.8, 0.3],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute inset-0 rounded-full border-2 border-white/30"
              />
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.2, 0.6, 0.2],
                }}
                transition={{
                  duration: 2.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 0.5,
                }}
                className="absolute inset-0 rounded-full border border-white/20"
              />
            </>
          )}
        </motion.button>

        {/* Siri-like floating orbs */}
        {isSpeaking && (
          <>
            {[...Array(6)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-3 h-3 bg-white/40 rounded-full blur-sm"
                style={{
                  left: `${50 + 50 * Math.cos((i * 60 * Math.PI) / 180)}%`,
                  top: `${50 + 50 * Math.sin((i * 60 * Math.PI) / 180)}%`,
                }}
                animate={{
                  scale: [0, 1.5, 0],
                  opacity: [0, 0.8, 0],
                  y: [0, -30, 0],
                  x: [0, (Math.random() - 0.5) * 20, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  delay: i * 0.4,
                  ease: "easeInOut",
                }}
              />
            ))}
          </>
        )}
      </motion.div>

      {/* Transcript display */}
      {transcript && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="absolute -bottom-32 left-1/2 transform -translate-x-1/2 w-full max-w-2xl"
        >
          <div className="bg-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-2xl p-4 shadow-2xl">
            <p className="text-gray-300 text-center text-sm">
              <span className="text-blue-400">You said:</span> {transcript}
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
