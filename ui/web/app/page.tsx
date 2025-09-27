"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { InputForm } from "@/components/input-form";
import { SpeakingBubble } from "@/components/speaking-bubble";
import { StatusIndicator } from "@/components/status-indicator";
import { ChatRequest } from "@/types";
import { AudioRecorder } from "@/lib/audio-recorder";
import Link from "next/link";
import toast, { Toaster } from "react-hot-toast";
import { serviceManager } from "@/services/ServiceManager";

export default function Home() {
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [useVoiceMode, setUseVoiceMode] = useState(true);
  const [streamingController, setStreamingController] =
    useState<AbortController | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(
    null
  );
  const [completeResponse, setCompleteResponse] = useState("");
  const audioRecorderRef = useRef<AudioRecorder | null>(null);
  const [speechRecognitionAvailable, setSpeechRecognitionAvailable] =
    useState(false);

  useEffect(() => {
    // Initialize audio recorder
    if (typeof window !== "undefined" && navigator.mediaDevices) {
      // Check if we're in a secure context (HTTPS or localhost)
      if (!window.isSecureContext) {
        console.warn("Audio recording requires HTTPS or localhost");
        toast.error(
          "Audio recording requires HTTPS. Please use HTTPS or localhost to enable voice features."
        );
        setSpeechRecognitionAvailable(false);
        return;
      }

      // Initialize audio recorder
      audioRecorderRef.current = new AudioRecorder({
        onTranscript: (transcript: string) => {
          console.log("Transcript received:", transcript);
          setTranscript(transcript);
          // Auto-submit the transcribed text
          if (transcript.trim()) {
            handleSubmit(transcript.trim());
          }
        },
        onError: (error: string) => {
          console.error("Audio recording error:", error);
          toast.error(error);
          setIsListening(false);
          setIsRecording(false);
        },
        onStart: () => {
          console.log("Audio recording started");
          setIsListening(true);
          setIsRecording(true);
        },
        onStop: () => {
          console.log("Audio recording stopped");
          setIsListening(false);
          setIsRecording(false);
        },
        whisperServiceUrl: "http://localhost:3001", // Your local Whisper service
      });

      setSpeechRecognitionAvailable(true);
    } else {
      console.warn("Audio recording not supported in this browser");
      setSpeechRecognitionAvailable(false);
    }

    // Cleanup on unmount
    return () => {
      if (audioRecorderRef.current) {
        audioRecorderRef.current.destroy();
      }
    };
  }, []);

  const stopSpeaking = () => {
    setIsSpeaking(false);
    setIsPaused(false);
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }
  };

  const pauseSpeaking = () => {
    setIsPaused(true);
    if (audioElement) {
      audioElement.pause();
    }
  };

  const resumeSpeaking = () => {
    setIsPaused(false);
    if (audioElement) {
      audioElement.play();
    }
  };

  const stopStreaming = () => {
    if (streamingController) {
      streamingController.abort();
      setStreamingController(null);
      setIsLoading(false);
    }
  };

  const startListening = () => {
    console.log("Starting audio recording");
    if (audioRecorderRef.current && !isListening) {
      setTranscript("");
      audioRecorderRef.current.startRecording();
    } else if (!audioRecorderRef.current) {
      toast.error(
        "Audio recording not available. Please refresh the page and try again."
      );
    }
  };

  const stopListening = () => {
    console.log("Stopping audio recording");
    if (audioRecorderRef.current && isListening) {
      audioRecorderRef.current.stopRecording();
    }
  };

  const handleSubmit = async (message: string) => {
    // Stop any existing streaming
    if (streamingController) {
      streamingController.abort();
    }

    // Create new abort controller for this request
    const controller = new AbortController();
    setStreamingController(controller);

    setIsLoading(true);
    setResponse("");
    setCompleteResponse("");

    try {
      // Use the new API client with streaming
      const request: ChatRequest = {
        message,
        use_stt: false,
      };

      await serviceManager.chat.sendMessageStream(
        request,
        {
          onToken: (token: string) => {
            if (!controller.signal.aborted) {
              setResponse((prev) => {
                const newResponse = prev + token;
                setCompleteResponse(newResponse);
                console.log(
                  "Token received, completeResponse length:",
                  newResponse.length
                );
                return newResponse;
              });
            }
          },
          onComplete: async (finalResponse: string) => {
            if (!controller.signal.aborted) {
              setIsLoading(false);
              setStreamingController(null);

              console.log(
                "Streaming completed. useVoiceMode:",
                useVoiceMode,
                "finalResponse length:",
                finalResponse.length
              );

              // Generate TTS audio if voice mode is enabled
              if (useVoiceMode && finalResponse) {
                console.log(
                  "Generating TTS for response:",
                  finalResponse.substring(0, 100) + "..."
                );
                try {
                  const ttsRequest = { text: finalResponse };
                  const ttsResponse = await serviceManager.audio.speakText(
                    ttsRequest
                  );
                  console.log("TTS Response:", ttsResponse);

                  if (ttsResponse.success && ttsResponse.audio_url) {
                    const audio = new Audio(ttsResponse.audio_url);
                    setAudioElement(audio);

                    audio.onplay = () => {
                      console.log("Audio started playing");
                      setIsSpeaking(true);
                    };
                    audio.onpause = () => {
                      console.log("Audio paused");
                      setIsPaused(true);
                    };
                    audio.onended = () => {
                      console.log("Audio ended");
                      setIsSpeaking(false);
                      setIsPaused(false);
                    };

                    console.log("Starting audio playback...");
                    await audio.play();
                  } else {
                    console.log("TTS failed - no audio URL or success=false");
                  }
                } catch (error) {
                  console.error("TTS failed:", error);
                  toast.error("Failed to generate speech", {
                    duration: 3000,
                    position: "top-right",
                  });
                }
              } else {
                console.log(
                  "TTS skipped - useVoiceMode:",
                  useVoiceMode,
                  "finalResponse length:",
                  finalResponse.length
                );
              }
            }
          },
          onError: (error: string) => {
            if (!controller.signal.aborted) {
              console.error("Streaming failed:", error);
              toast.error(`Connection failed: ${error}`, {
                duration: 5000,
                position: "top-right",
              });

              // Fallback response
              const fallbackResponse = `I apologize, but I'm having trouble connecting to my services right now. Error: ${error}. Please check the service status below and try again.`;

              setResponse(fallbackResponse);
              setCompleteResponse(fallbackResponse);
              setIsLoading(false);
              setStreamingController(null);
            }
          },
        },
        controller.signal
      );
    } catch (error) {
      if (!controller.signal.aborted) {
        console.error("API call failed:", error);
        const errorMessage =
          error instanceof Error ? error.message : "Failed to get response";

        toast.error(`Request failed: ${errorMessage}`, {
          duration: 5000,
          position: "top-right",
        });

        // Fallback response
        const fallbackResponse = `I apologize, but I'm having trouble connecting to my services right now. 

Error: ${errorMessage}

Please check the service status below and try again.`;

        setResponse(fallbackResponse);
        setCompleteResponse(fallbackResponse);
        setIsLoading(false);
        setStreamingController(null);
      }
    }
  };

  const handleTranscription = (text: string) => {
    setTranscript(text);

    // Auto-submit the transcribed text
    if (text.trim()) {
      handleSubmit(text.trim());
    }
  };

  const handleError = (errorMessage: string) => {
    toast.error(`Voice error: ${errorMessage}`, {
      duration: 4000,
      position: "top-right",
    });
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center relative overflow-hidden">
      {/* Dark background with subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-black to-gray-800" />

      {/* Subtle grid pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.02%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%221%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-30" />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="absolute top-8 left-8 right-8 z-20 flex items-center justify-between"
      >
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12">
            <img
              src="/logo.svg"
              alt="Jarvis Logo"
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-white">Jarvis</h1>
            <p className="text-gray-400 mt-2">Your AI Assistant</p>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center space-x-2">
          <Link
            href="/status"
            className="flex items-center space-x-2 p-3 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg hover:bg-gray-700/50 transition-colors"
          >
            <StatusIndicator />
          </Link>
          <Link
            href="/routes"
            className="p-3 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg hover:bg-gray-700/50 transition-colors"
            title="View API Routes"
          >
            <svg
              className="w-5 h-5 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          </Link>
        </div>
      </motion.div>

      {/* Main centered content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen w-full max-w-4xl mx-auto px-4">
        {/* Speaking Bubble */}
        <SpeakingBubble
          isSpeaking={isSpeaking}
          isPaused={isPaused}
          onStopSpeaking={stopSpeaking}
          onPauseSpeaking={pauseSpeaking}
          onResumeSpeaking={resumeSpeaking}
        />

        {/* Voice Mode Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mb-8"
        >
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-400">Voice Mode:</span>
            <button
              onClick={() => setUseVoiceMode(!useVoiceMode)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                useVoiceMode ? "bg-blue-500" : "bg-gray-600"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useVoiceMode ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
            <span className="text-sm text-gray-400">
              {useVoiceMode ? "Enabled" : "Disabled"}
            </span>
          </div>
        </motion.div>

        {/* Transcript Display */}
        {transcript && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 p-4 bg-gray-800/30 border border-gray-600/30 rounded-lg"
          >
            <p className="text-gray-300 text-sm">
              <span className="font-medium text-gray-400">You said:</span>{" "}
              {transcript}
            </p>
          </motion.div>
        )}

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
            onStopListening={stopListening}
            isListening={isListening}
            transcript={transcript}
            speechRecognitionAvailable={speechRecognitionAvailable}
          />
        </motion.div>

        {/* Response text display below input */}
        {(response || isLoading) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-8 w-full max-w-4xl"
          >
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-center">
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.8 }}
                  className="text-gray-300 text-center leading-relaxed whitespace-pre-wrap flex-1"
                >
                  {response}
                  {isLoading && !response && (
                    <span className="inline-block ml-1">
                      <span className="animate-pulse">●</span>
                      <span className="animate-pulse delay-100">●</span>
                      <span className="animate-pulse delay-200">●</span>
                    </span>
                  )}
                  {isLoading && response && (
                    <span className="inline-block ml-1 animate-pulse">●</span>
                  )}
                </motion.p>

                {/* Stop streaming button */}
                {isLoading && streamingController && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    onClick={stopStreaming}
                    className="ml-4 p-2 bg-red-600 hover:bg-red-700 text-white rounded-full transition-colors"
                    title="Stop streaming"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1zm4 0a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </motion.button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: "#1f2937",
            color: "#f9fafb",
            border: "1px solid #374151",
            borderRadius: "8px",
          },
          success: {
            style: {
              background: "#065f46",
              color: "#f0fdf4",
              border: "1px solid #10b981",
            },
          },
          error: {
            style: {
              background: "#7f1d1d",
              color: "#fef2f2",
              border: "1px solid #ef4444",
            },
          },
        }}
      />
    </div>
  );
}
