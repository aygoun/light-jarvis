/**
 * Custom hook for managing chat state and functionality
 */

import { useState, useCallback, useRef } from "react";
import { serviceManager } from "@/services/ServiceManager";
import { ChatState, ChatRequest, TTSRequest } from "@/types";
import { ERROR_MESSAGES, SUCCESS_MESSAGES } from "@/lib/constants";
import toast from "react-hot-toast";

const initialState: ChatState = {
  response: "",
  isLoading: false,
  isSpeaking: false,
  isPaused: false,
  isListening: false,
  transcript: "",
  isRecording: false,
  useVoiceMode: true,
  streamingController: null,
  audioElement: null,
  completeResponse: "",
  speechRecognitionAvailable: false,
};

export const useChat = () => {
  const [state, setState] = useState<ChatState>(initialState);
  const audioRecorderRef = useRef<any>(null);

  // ============================================================================
  // State Setters
  // ============================================================================

  const setResponse = useCallback((response: string) => {
    setState((prev) => ({ ...prev, response }));
  }, []);

  const setIsLoading = useCallback((isLoading: boolean) => {
    setState((prev) => ({ ...prev, isLoading }));
  }, []);

  const setIsSpeaking = useCallback((isSpeaking: boolean) => {
    setState((prev) => ({ ...prev, isSpeaking }));
  }, []);

  const setIsPaused = useCallback((isPaused: boolean) => {
    setState((prev) => ({ ...prev, isPaused }));
  }, []);

  const setIsListening = useCallback((isListening: boolean) => {
    setState((prev) => ({ ...prev, isListening }));
  }, []);

  const setTranscript = useCallback((transcript: string) => {
    setState((prev) => ({ ...prev, transcript }));
  }, []);

  const setIsRecording = useCallback((isRecording: boolean) => {
    setState((prev) => ({ ...prev, isRecording }));
  }, []);

  const setUseVoiceMode = useCallback((useVoiceMode: boolean) => {
    setState((prev) => ({ ...prev, useVoiceMode }));
  }, []);

  const setStreamingController = useCallback(
    (controller: AbortController | null) => {
      setState((prev) => ({ ...prev, streamingController: controller }));
    },
    []
  );

  const setAudioElement = useCallback(
    (audioElement: HTMLAudioElement | null) => {
      setState((prev) => ({ ...prev, audioElement }));
    },
    []
  );

  const setCompleteResponse = useCallback((completeResponse: string) => {
    setState((prev) => ({ ...prev, completeResponse }));
  }, []);

  const setSpeechRecognitionAvailable = useCallback((available: boolean) => {
    setState((prev) => ({ ...prev, speechRecognitionAvailable: available }));
  }, []);

  // ============================================================================
  // Audio Control Functions
  // ============================================================================

  const stopSpeaking = useCallback(() => {
    setIsSpeaking(false);
    setIsPaused(false);
    if (state.audioElement) {
      state.audioElement.pause();
      state.audioElement.currentTime = 0;
    }
  }, [state.audioElement, setIsSpeaking, setIsPaused]);

  const pauseSpeaking = useCallback(() => {
    setIsPaused(true);
    if (state.audioElement) {
      state.audioElement.pause();
    }
  }, [state.audioElement, setIsPaused]);

  const resumeSpeaking = useCallback(() => {
    setIsPaused(false);
    if (state.audioElement) {
      state.audioElement.play();
    }
  }, [state.audioElement, setIsPaused]);

  const stopStreaming = useCallback(() => {
    if (state.streamingController) {
      state.streamingController.abort();
      setStreamingController(null);
      setIsLoading(false);
    }
  }, [state.streamingController, setStreamingController, setIsLoading]);

  // ============================================================================
  // Audio Recording Functions
  // ============================================================================

  const startListening = useCallback(() => {
    console.log("Starting audio recording");
    if (audioRecorderRef.current && !state.isListening) {
      setTranscript("");
      audioRecorderRef.current.startRecording();
    } else if (!audioRecorderRef.current) {
      toast.error(ERROR_MESSAGES.RECORDING_FAILED);
    }
  }, [state.isListening, setTranscript]);

  const stopListening = useCallback(() => {
    console.log("Stopping audio recording");
    if (audioRecorderRef.current && state.isListening) {
      audioRecorderRef.current.stopRecording();
    }
  }, [state.isListening]);

  // ============================================================================
  // Chat Functions
  // ============================================================================

  const handleSubmit = useCallback(
    async (message: string) => {
      // Stop any existing streaming
      if (state.streamingController) {
        state.streamingController.abort();
      }

      // Create new abort controller for this request
      const controller = new AbortController();
      setStreamingController(controller);

      setIsLoading(true);
      setResponse("");
      setCompleteResponse("");

      try {
        const request: ChatRequest = {
          message,
          use_stt: false,
        };

        await serviceManager.chat.sendMessageStream(
          request,
          {
            onToken: (token: string) => {
              if (!controller.signal.aborted) {
                setState((prev) => {
                  const newResponse = prev.response + token;
                  setCompleteResponse(newResponse);
                  return { ...prev, response: newResponse };
                });
              }
            },
            onComplete: async (finalResponse: string) => {
              if (!controller.signal.aborted) {
                setIsLoading(false);
                setStreamingController(null);

                // Generate TTS audio if voice mode is enabled
                if (state.useVoiceMode && finalResponse) {
                  try {
                    const ttsRequest: TTSRequest = { text: finalResponse };
                    const ttsResponse = await serviceManager.audio.speakText(
                      ttsRequest
                    );

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

                      await audio.play();
                    }
                  } catch (error) {
                    console.error("TTS failed:", error);
                    toast.error(ERROR_MESSAGES.TTS_FAILED);
                  }
                }
              }
            },
            onError: (error: string) => {
              if (!controller.signal.aborted) {
                console.error("Streaming failed:", error);
                toast.error(`${ERROR_MESSAGES.CONNECTION_FAILED}: ${error}`);

                const fallbackResponse = `I apologize, but I'm having trouble connecting to my services right now.

Error: ${error}

Please check the service status below and try again.`;

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

          toast.error(`${ERROR_MESSAGES.REQUEST_FAILED}: ${errorMessage}`);

          const fallbackResponse = `I apologize, but I'm having trouble connecting to my services right now.

Error: ${errorMessage}

Please check the service status below and try again.`;

          setResponse(fallbackResponse);
          setCompleteResponse(fallbackResponse);
          setIsLoading(false);
          setStreamingController(null);
        }
      }
    },
    [
      state.streamingController,
      state.useVoiceMode,
      setStreamingController,
      setIsLoading,
      setResponse,
      setCompleteResponse,
      setAudioElement,
      setIsSpeaking,
      setIsPaused,
    ]
  );

  const handleTranscription = useCallback(
    (text: string) => {
      setTranscript(text);
      if (text.trim()) {
        handleSubmit(text.trim());
      }
    },
    [setTranscript, handleSubmit]
  );

  const handleError = useCallback((errorMessage: string) => {
    toast.error(`Voice error: ${errorMessage}`);
  }, []);

  // ============================================================================
  // Reset Functions
  // ============================================================================

  const resetChat = useCallback(() => {
    setState(initialState);
  }, []);

  const clearResponse = useCallback(() => {
    setResponse("");
    setCompleteResponse("");
  }, [setResponse, setCompleteResponse]);

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State
    ...state,

    // Setters
    setResponse,
    setIsLoading,
    setIsSpeaking,
    setIsPaused,
    setIsListening,
    setTranscript,
    setIsRecording,
    setUseVoiceMode,
    setStreamingController,
    setAudioElement,
    setCompleteResponse,
    setSpeechRecognitionAvailable,

    // Audio Controls
    stopSpeaking,
    pauseSpeaking,
    resumeSpeaking,
    stopStreaming,

    // Recording
    startListening,
    stopListening,

    // Chat
    handleSubmit,
    handleTranscription,
    handleError,

    // Reset
    resetChat,
    clearResponse,

    // Refs
    audioRecorderRef,
  };
};
