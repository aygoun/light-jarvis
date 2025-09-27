/**
 * Centralized API client for Jarvis microservices
 * Integrates with Main Orchestrator, Whisper Service, and MCP Orchestrator
 */

// Service endpoints
const SERVICES = {
  MAIN_ORCHESTRATOR: "http://localhost:3002",
  WHISPER_SERVICE: "http://localhost:3001",
  MCP_ORCHESTRATOR: "http://localhost:3000",
} as const;

// API Response types
export interface ServiceHealth {
  status: string;
  service: string;
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
}

export interface TTSResponse {
  success: boolean;
  audio_url?: string;
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

/**
 * Main API client class
 */
export class JarvisAPI {
  private static instance: JarvisAPI;

  private constructor() {}

  static getInstance(): JarvisAPI {
    if (!JarvisAPI.instance) {
      JarvisAPI.instance = new JarvisAPI();
    }
    return JarvisAPI.instance;
  }

  /**
   * Check health of all services
   */
  async checkAllServicesHealth(): Promise<Record<string, ServiceHealth>> {
    const [main, whisper, mcp] = await Promise.allSettled([
      this.checkMainOrchestratorHealth(),
      this.checkWhisperServiceHealth(),
      this.checkMCPOrchestratorHealth(),
    ]);

    return {
      main:
        main.status === "fulfilled"
          ? main.value
          : {
              status: "error",
              service: "main-orchestrator",
              error: main.reason?.message,
            },
      whisper:
        whisper.status === "fulfilled"
          ? whisper.value
          : {
              status: "error",
              service: "whisper-service",
              error: whisper.reason?.message,
            },
      mcp:
        mcp.status === "fulfilled"
          ? mcp.value
          : {
              status: "error",
              service: "mcp-orchestrator",
              error: mcp.reason?.message,
            },
    };
  }

  // Main Orchestrator API
  async checkMainOrchestratorHealth(): Promise<ServiceHealth> {
    const response = await fetch(`${SERVICES.MAIN_ORCHESTRATOR}/health`);
    if (!response.ok)
      throw new Error(
        `Main Orchestrator health check failed: ${response.statusText}`
      );
    return response.json();
  }

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${SERVICES.MAIN_ORCHESTRATOR}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async sendChatMessageStream(
    request: ChatRequest,
    onToken: (token: string) => void,
    onComplete: () => void,
    onError: (error: string) => void,
    signal?: AbortSignal
  ): Promise<void> {
    try {
      const response = await fetch(
        `${SERVICES.MAIN_ORCHESTRATOR}/chat/stream`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
          signal,
        }
      );

      if (!response.ok) {
        throw new Error(
          `Streaming chat request failed: ${response.statusText}`
        );
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader available");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        // Check if the request was aborted
        if (signal?.aborted) {
          reader.cancel();
          return;
        }

        const { done, value } = await reader.read();

        if (done) {
          onComplete();
          break;
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6); // Remove 'data: ' prefix

            if (data === "[DONE]") {
              onComplete();
              return;
            }

            if (data.trim()) {
              onToken(data);
            }
          }
        }
      }
    } catch (error) {
      // Don't call onError if the request was aborted
      if (signal?.aborted) {
        return;
      }
      const errorMessage =
        error instanceof Error ? error.message : "Streaming failed";
      onError(errorMessage);
    }
  }

  async transcribeAudio(
    request: TranscriptionRequest
  ): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append("file", request.file);
    if (request.language) formData.append("language", request.language);
    if (request.temperature)
      formData.append("temperature", request.temperature.toString());

    const response = await fetch(
      `${SERVICES.MAIN_ORCHESTRATOR}/stt/transcribe`,
      {
        method: "POST",
        body: formData,
      }
    );

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.statusText}`);
    }

    return response.json();
  }

  async speakText(request: TTSRequest): Promise<TTSResponse> {
    const formData = new FormData();
    formData.append("text", request.text);

    const response = await fetch(`${SERVICES.MAIN_ORCHESTRATOR}/tts/speak`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`TTS request failed: ${response.statusText}`);
    }

    // The response is binary audio data, not JSON
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);

    console.log("audioUrl", audioUrl);

    return {
      success: true,
      audio_url: audioUrl,
      // text: request.text,
      // voice: request.voice || "default",
      // rate: request.rate || 200,
      // volume: request.volume || 0.8,
    };
  }

  // Whisper Service API (direct access)
  async checkWhisperServiceHealth(): Promise<ServiceHealth> {
    const response = await fetch(`${SERVICES.WHISPER_SERVICE}/health`);
    if (!response.ok)
      throw new Error(
        `Whisper Service health check failed: ${response.statusText}`
      );
    return response.json();
  }

  async transcribeAudioDirect(
    request: TranscriptionRequest
  ): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append("file", request.file);
    if (request.language) formData.append("language", request.language);
    if (request.temperature)
      formData.append("temperature", request.temperature.toString());

    const response = await fetch(`${SERVICES.WHISPER_SERVICE}/stt/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Direct transcription failed: ${response.statusText}`);
    }

    return response.json();
  }

  async speakTextDirect(request: TTSRequest): Promise<TTSResponse> {
    const formData = new FormData();
    formData.append("text", request.text);

    const response = await fetch(`${SERVICES.WHISPER_SERVICE}/tts/speak`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Direct TTS request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getAvailableVoices(): Promise<Voice[]> {
    const response = await fetch(`${SERVICES.WHISPER_SERVICE}/tts/voices`);
    if (!response.ok)
      throw new Error(`Failed to get voices: ${response.statusText}`);
    const data = await response.json();
    return data.voices || [];
  }

  // MCP Orchestrator API
  async checkMCPOrchestratorHealth(): Promise<ServiceHealth> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/health`);
    if (!response.ok)
      throw new Error(
        `MCP Orchestrator health check failed: ${response.statusText}`
      );
    return response.json();
  }

  async listAvailableTools(): Promise<any[]> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/tools`);
    if (!response.ok)
      throw new Error(`Failed to list tools: ${response.statusText}`);
    const data = await response.json();
    return data.tools || [];
  }

  async executeTool(toolCall: ToolCall): Promise<ToolResult> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/tools/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toolCall),
    });

    if (!response.ok) {
      throw new Error(`Tool execution failed: ${response.statusText}`);
    }

    return response.json();
  }

  async initializeAuth(): Promise<any> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/auth/init`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`Auth initialization failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getAuthStatus(): Promise<any> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/auth/status`);
    if (!response.ok)
      throw new Error(`Failed to get auth status: ${response.statusText}`);
    return response.json();
  }

  async authenticateGoogle(): Promise<any> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/auth/google`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`Google authentication failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const jarvisAPI = JarvisAPI.getInstance();
