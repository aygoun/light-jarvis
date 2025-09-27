/**
 * Application constants and configuration
 */

import { AppConfig, ServiceEndpoints } from "@/types";

// ============================================================================
// Service Endpoints
// ============================================================================

export const SERVICES: ServiceEndpoints = {
  MAIN_ORCHESTRATOR: "http://localhost:3002",
  WHISPER_SERVICE: "http://localhost:3001",
  MCP_ORCHESTRATOR: "http://localhost:3000",
} as const;

// ============================================================================
// Application Configuration
// ============================================================================

export const APP_CONFIG: AppConfig = {
  services: SERVICES,
  audio: {
    minimumRecordingTime: 2000, // 2 seconds
    sampleRate: 16000,
    channelCount: 1,
  },
  ui: {
    animationDuration: 0.6,
    refreshInterval: 10000, // 10 seconds
  },
} as const;

// ============================================================================
// Audio Configuration
// ============================================================================

export const AUDIO_CONFIG = {
  MIME_TYPES: [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/wav",
  ] as const,
  DEFAULT_MIME_TYPE: "audio/webm;codecs=opus" as const,
  RECORDING_INTERVAL: 1000, // 1 second
  MINIMUM_DURATION: 2000, // 2 seconds
} as const;

// ============================================================================
// UI Constants
// ============================================================================

export const UI_CONSTANTS = {
  ANIMATION_DURATION: {
    FAST: 0.2,
    NORMAL: 0.6,
    SLOW: 0.8,
  },
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 4000,
  REFRESH_INTERVAL: 10000,
} as const;

// ============================================================================
// Tool Categories
// ============================================================================

export const TOOL_CATEGORIES = {
  GMAIL: "Gmail",
  CALENDAR: "Calendar",
  NOTIFICATIONS: "Notifications",
  HUE: "Hue",
  OTHER: "Other",
} as const;

// ============================================================================
// Service Names
// ============================================================================

export const SERVICE_NAMES = {
  MAIN_ORCHESTRATOR: "Main Orchestrator",
  WHISPER_SERVICE: "Whisper Service",
  MCP_ORCHESTRATOR: "MCP Orchestrator",
} as const;

// ============================================================================
// Error Messages
// ============================================================================

export const ERROR_MESSAGES = {
  MICROPHONE_DENIED:
    "Microphone access denied. Please allow microphone access and try again.",
  NO_MICROPHONE:
    "No microphone found. Please connect a microphone and try again.",
  RECORDING_FAILED: "Recording failed",
  TRANSCRIPTION_FAILED: "Transcription failed",
  TTS_FAILED: "Failed to generate speech",
  CONNECTION_FAILED: "Connection failed",
  REQUEST_FAILED: "Request failed",
  AUTH_FAILED: "Authentication failed",
  SERVICE_UNAVAILABLE: "Service unavailable",
} as const;

// ============================================================================
// Success Messages
// ============================================================================

export const SUCCESS_MESSAGES = {
  RECORDING_STARTED: "Recording started",
  RECORDING_STOPPED: "Recording stopped",
  TRANSCRIPTION_SUCCESS: "Transcription completed",
  TTS_SUCCESS: "Speech generated successfully",
  AUTH_SUCCESS: "Authentication successful",
} as const;

// ============================================================================
// API Endpoints
// ============================================================================

export const API_ENDPOINTS = {
  HEALTH: "/health",
  CHAT: "/chat",
  CHAT_STREAM: "/chat/stream",
  STT_TRANSCRIBE: "/stt/transcribe",
  TTS_SPEAK: "/tts/speak",
  TTS_VOICES: "/tts/voices",
  TOOLS: "/tools",
  TOOLS_EXECUTE: "/tools/execute",
  AUTH_INIT: "/auth/init",
  AUTH_STATUS: "/auth/status",
  AUTH_GOOGLE: "/auth/google",
  OAUTH_CALLBACK: "/oauth2/callback",
} as const;

// ============================================================================
// CSS Classes
// ============================================================================

export const CSS_CLASSES = {
  ANIMATION: {
    FADE_IN: "animate-fade-in",
    SLIDE_UP: "animate-slide-up",
    SCALE: "animate-scale",
    BOUNCE: "animate-bounce",
  },
  STATUS: {
    HEALTHY: "text-green-400",
    ERROR: "text-red-400",
    LOADING: "text-blue-400",
    UNKNOWN: "text-yellow-400",
  },
  BUTTON: {
    PRIMARY: "bg-blue-500 hover:bg-blue-600",
    SECONDARY: "bg-gray-700 hover:bg-gray-600",
    DANGER: "bg-red-600 hover:bg-red-700",
    SUCCESS: "bg-green-600 hover:bg-green-700",
  },
} as const;

// ============================================================================
// Local Storage Keys
// ============================================================================

export const STORAGE_KEYS = {
  VOICE_MODE: "jarvis_voice_mode",
  THEME: "jarvis_theme",
  SETTINGS: "jarvis_settings",
  AUTH_TOKEN: "jarvis_auth_token",
} as const;

// ============================================================================
// Validation Rules
// ============================================================================

export const VALIDATION_RULES = {
  MESSAGE_MIN_LENGTH: 1,
  MESSAGE_MAX_LENGTH: 1000,
  TRANSCRIPT_MIN_LENGTH: 1,
  TRANSCRIPT_MAX_LENGTH: 500,
} as const;
