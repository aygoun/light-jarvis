/**
 * Custom hook for managing audio recording functionality
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { AudioRecorder, AudioRecorderOptions } from "@/lib/audio-recorder";
import { AudioRecordingState } from "@/types";
import { ERROR_MESSAGES, SUCCESS_MESSAGES, APP_CONFIG } from "@/lib/constants";

const initialState: AudioRecordingState = {
  isRecording: false,
  isListening: false,
  isProcessing: false,
  duration: 0,
  error: null,
};

export const useAudioRecorder = (
  onTranscript: (transcript: string) => void,
  onError: (error: string) => void,
  whisperServiceUrl?: string
) => {
  const [state, setState] = useState<AudioRecordingState>(initialState);
  const audioRecorderRef = useRef<AudioRecorder | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // ============================================================================
  // State Setters
  // ============================================================================

  const setIsRecording = useCallback((isRecording: boolean) => {
    setState((prev) => ({ ...prev, isRecording }));
  }, []);

  const setIsListening = useCallback((isListening: boolean) => {
    setState((prev) => ({ ...prev, isListening }));
  }, []);

  const setIsProcessing = useCallback((isProcessing: boolean) => {
    setState((prev) => ({ ...prev, isProcessing }));
  }, []);

  const setDuration = useCallback((duration: number) => {
    setState((prev) => ({ ...prev, duration }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState((prev) => ({ ...prev, error }));
  }, []);

  // ============================================================================
  // Audio Recorder Setup
  // ============================================================================

  const initializeAudioRecorder = useCallback(() => {
    if (typeof window === "undefined" || !navigator.mediaDevices) {
      setError("Audio recording not supported in this browser");
      return false;
    }

    // Check if we're in a secure context (HTTPS or localhost)
    if (!window.isSecureContext) {
      setError(ERROR_MESSAGES.MICROPHONE_DENIED);
      return false;
    }

    try {
      const options: AudioRecorderOptions = {
        onTranscript: (transcript: string) => {
          console.log("Transcript received:", transcript);
          onTranscript(transcript);
        },
        onError: (error: string) => {
          console.error("Audio recording error:", error);
          onError(error);
          setIsListening(false);
          setIsRecording(false);
          setError(error);
        },
        onStart: () => {
          console.log("Audio recording started");
          setIsListening(true);
          setIsRecording(true);
          setError(null);
          setDuration(0);
        },
        onStop: () => {
          console.log("Audio recording stopped");
          setIsListening(false);
          setIsRecording(false);
        },
        whisperServiceUrl:
          whisperServiceUrl || APP_CONFIG.services.WHISPER_SERVICE,
      };

      audioRecorderRef.current = new AudioRecorder(options);
      return true;
    } catch (error) {
      console.error("Failed to initialize audio recorder:", error);
      setError("Failed to initialize audio recorder");
      return false;
    }
  }, [
    onTranscript,
    onError,
    whisperServiceUrl,
    setIsListening,
    setIsRecording,
    setError,
    setDuration,
  ]);

  // ============================================================================
  // Recording Functions
  // ============================================================================

  const startRecording = useCallback(() => {
    console.log("Starting audio recording");

    if (!audioRecorderRef.current) {
      if (!initializeAudioRecorder()) {
        onError(ERROR_MESSAGES.RECORDING_FAILED);
        return;
      }
    }

    if (audioRecorderRef.current && !state.isRecording) {
      setError(null);
      audioRecorderRef.current.startRecording();

      // Start duration counter
      intervalRef.current = setInterval(() => {
        setState((prev) => ({ ...prev, duration: prev.duration + 100 }));
      }, 100);
    } else if (!audioRecorderRef.current) {
      onError(ERROR_MESSAGES.RECORDING_FAILED);
    }
  }, [
    state.isRecording,
    initializeAudioRecorder,
    onError,
    setError,
    setDuration,
  ]);

  const stopRecording = useCallback(() => {
    console.log("Stopping audio recording");

    if (audioRecorderRef.current && state.isRecording) {
      audioRecorderRef.current.stopRecording();

      // Stop duration counter
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [state.isRecording]);

  const destroyRecorder = useCallback(() => {
    if (audioRecorderRef.current) {
      audioRecorderRef.current.destroy();
      audioRecorderRef.current = null;
    }

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    setState(initialState);
  }, [setState]);

  // ============================================================================
  // Utility Functions
  // ============================================================================

  const isCurrentlyRecording = useCallback(() => {
    return audioRecorderRef.current?.isCurrentlyRecording() || false;
  }, []);

  const canRecord = useCallback(() => {
    return (
      typeof window !== "undefined" &&
      navigator.mediaDevices &&
      window.isSecureContext
    );
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    // Initialize audio recorder on mount
    initializeAudioRecorder();

    // Cleanup on unmount
    return () => {
      destroyRecorder();
    };
  }, [initializeAudioRecorder, destroyRecorder]);

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State
    ...state,

    // Setters
    setIsRecording,
    setIsProcessing,
    setDuration,
    setError,

    // Functions
    startRecording,
    stopRecording,
    destroyRecorder,
    initializeAudioRecorder,
    isCurrentlyRecording,
    canRecord,

    // Refs
    audioRecorderRef,
  };
};
