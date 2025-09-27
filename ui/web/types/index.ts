/**
 * Centralized type definitions for the Jarvis web application
 */

// ============================================================================
// API Types
// ============================================================================

export interface ServiceHealth {
  status: "healthy" | "error" | "unknown";
  service: string;
  tools_count?: number;
  auth_initialized?: boolean;
  google_authenticated?: boolean;
  assistant_initialized?: boolean;
  stt?: {
    status: string;
  };
  tts?: {
    status: string;
  };
  error?: string;
  [key: string]: any;
}

export interface ChatRequest {
  message: string;
  use_stt?: boolean;
}

export interface ChatResponse {
  success: boolean;
  response?: string;
  error?: string;
}

export interface TranscriptionRequest {
  file: File;
  language?: string;
  temperature?: number;
}

export interface TranscriptionResponse {
  success: boolean;
  text?: string;
  language?: string;
  confidence?: number;
  error?: string;
}

export interface TTSRequest {
  text: string;
  voice?: string;
  rate?: number;
  volume?: number;
}

export interface TTSResponse {
  success: boolean;
  audio_url?: string;
  text?: string;
  voice?: string;
  rate?: number;
  volume?: number;
  error?: string;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, any>;
}

export interface ToolResult {
  tool_call_id: string;
  content: string;
  success: boolean;
  error?: string;
}

export interface Voice {
  name: string;
  gender: string;
  locale: string;
  [key: string]: any;
}

export interface Tool {
  name: string;
  description: string;
  inputSchema?: {
    properties: Record<
      string,
      {
        type: string;
        description?: string;
      }
    >;
  };
}

export interface RouteInfo {
  path: string;
  method: string;
  summary: string;
  description: string;
  tags: string[];
  full_url: string;
}

export interface ServiceRoutes {
  base_url: string;
  status: "available" | "no_openapi" | "error";
  routes: RouteInfo[];
  total_routes: number;
  error?: string;
}

export interface RoutesResponse {
  services: Record<string, ServiceRoutes>;
  total_services: number;
  total_routes: number;
  timestamp: string;
  error?: string;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface InputFormProps {
  onSubmit: (message: string) => void;
  isLoading?: boolean;
  onStartListening?: () => void;
  onStopListening?: () => void;
  isListening?: boolean;
  transcript?: string;
  speechRecognitionAvailable?: boolean;
}

export interface SpeakingBubbleProps {
  isSpeaking: boolean;
  isPaused: boolean;
  onStopSpeaking: () => void;
  onPauseSpeaking: () => void;
  onResumeSpeaking: () => void;
}

export interface StatusIndicatorProps {
  className?: string;
}

// ============================================================================
// State Types
// ============================================================================

export interface ChatState {
  response: string;
  isLoading: boolean;
  isSpeaking: boolean;
  isPaused: boolean;
  isListening: boolean;
  transcript: string;
  isRecording: boolean;
  useVoiceMode: boolean;
  streamingController: AbortController | null;
  audioElement: HTMLAudioElement | null;
  completeResponse: string;
  speechRecognitionAvailable: boolean;
}

export interface ServiceInfo {
  name: string;
  port: number;
  description: string;
  icon: React.ReactNode;
  health: ServiceHealth | null;
  loading: boolean;
  error: string | null;
}

export interface StatusPageState {
  services: ServiceInfo[];
  isRefreshing: boolean;
  lastUpdated: Date | null;
  availableTools: Tool[];
  toolsLoading: boolean;
}

// ============================================================================
// Audio Recording Types
// ============================================================================

export interface AudioRecorderOptions {
  onTranscript: (transcript: string) => void;
  onError: (error: string) => void;
  onStart?: () => void;
  onStop?: () => void;
  whisperServiceUrl?: string;
}

export interface AudioRecordingState {
  isRecording: boolean;
  isListening: boolean;
  isProcessing: boolean;
  duration: number;
  error: string | null;
}

// ============================================================================
// Service Configuration Types
// ============================================================================

export interface ServiceEndpoints {
  MAIN_ORCHESTRATOR: string;
  WHISPER_SERVICE: string;
  MCP_ORCHESTRATOR: string;
}

export interface AppConfig {
  services: ServiceEndpoints;
  audio: {
    minimumRecordingTime: number;
    sampleRate: number;
    channelCount: number;
  };
  ui: {
    animationDuration: number;
    refreshInterval: number;
  };
}

// ============================================================================
// Error Types
// ============================================================================

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

// ============================================================================
// Event Types
// ============================================================================

export interface ChatEvent {
  type: "message" | "response" | "error" | "loading";
  data: any;
  timestamp: Date;
}

export interface AudioEvent {
  type: "start" | "stop" | "error" | "transcript";
  data: any;
  timestamp: Date;
}

// ============================================================================
// Utility Types
// ============================================================================

export type ServiceStatus = "healthy" | "error" | "loading" | "unknown";

export type ToolCategory =
  | "Gmail"
  | "Calendar"
  | "Notifications"
  | "Hue"
  | "Other";

export type AnimationVariant = "fadeIn" | "slideUp" | "scale" | "bounce";

// ============================================================================
// Generic Types
// ============================================================================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface StreamResponse {
  onToken: (token: string) => void;
  onComplete: (finalResponse: string) => void;
  onError: (error: string) => void;
  signal?: AbortSignal;
}
