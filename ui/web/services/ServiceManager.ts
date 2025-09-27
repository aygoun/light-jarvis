/**
 * Service manager for coordinating all API services
 */

import { ChatService } from "./ChatService";
import { StatusService } from "./StatusService";
import { AudioService } from "./AudioService";
import {
  ServiceHealth,
  ChatRequest,
  ChatResponse,
  TTSRequest,
  TTSResponse,
  TranscriptionRequest,
  TranscriptionResponse,
  Tool,
  StreamResponse,
  RoutesResponse,
} from "@/types";
import { SERVICES } from "@/lib/constants";

export class ServiceManager {
  private static instance: ServiceManager;

  public readonly chat: ChatService;
  public readonly status: StatusService;
  public readonly audio: AudioService;

  private constructor() {
    this.chat = new ChatService(SERVICES.MAIN_ORCHESTRATOR);
    this.status = new StatusService(SERVICES.MAIN_ORCHESTRATOR);
    this.audio = new AudioService(SERVICES.WHISPER_SERVICE);
  }

  /**
   * Get singleton instance
   */
  static getInstance(): ServiceManager {
    if (!ServiceManager.instance) {
      ServiceManager.instance = new ServiceManager();
    }
    return ServiceManager.instance;
  }

  // ============================================================================
  // Chat Methods
  // ============================================================================

  async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.chat.sendMessage(request);
  }

  async sendChatMessageStream(
    request: ChatRequest,
    callbacks: StreamResponse,
    signal?: AbortSignal
  ): Promise<void> {
    return this.chat.sendMessageStream(request, callbacks, signal);
  }

  async transcribeAudio(
    request: TranscriptionRequest
  ): Promise<TranscriptionResponse> {
    return this.chat.transcribeAudio(request);
  }

  async speakText(request: TTSRequest): Promise<TTSResponse> {
    return this.chat.speakText(request);
  }

  // ============================================================================
  // Status Methods
  // ============================================================================

  async checkAllServicesHealth(): Promise<Record<string, ServiceHealth>> {
    const [main, whisper, mcp] = await Promise.allSettled([
      this.status.getHealth(),
      this.audio.isHealthy(),
      this.checkMCPOrchestratorHealth(),
    ]);

    return {
      assistant:
        main.status === "fulfilled"
          ? main.value
          : {
              status: "error",
              service: "main-orchestrator",
              error: main.reason?.message,
            },
      whisper_service:
        whisper.status === "fulfilled" && whisper.value
          ? {
              status: "healthy",
              service: "whisper-service",
            }
          : {
              status: "error",
              service: "whisper-service",
              error:
                whisper.status === "rejected"
                  ? whisper.reason?.message || "Service unavailable"
                  : "Service unavailable",
            },
      mcp_orchestrator:
        mcp.status === "fulfilled"
          ? mcp.value
          : {
              status: "error",
              service: "mcp-orchestrator",
              error: mcp.reason?.message,
            },
    };
  }

  async checkMainOrchestratorHealth(): Promise<ServiceHealth> {
    return this.status.getHealth();
  }

  async checkWhisperServiceHealth(): Promise<ServiceHealth> {
    try {
      const isHealthy = await this.audio.isHealthy();
      return {
        status: isHealthy ? "healthy" : "error",
        service: "whisper-service",
      };
    } catch (error) {
      return {
        status: "error",
        service: "whisper-service",
        error: error instanceof Error ? error.message : "Service unavailable",
      };
    }
  }

  async checkMCPOrchestratorHealth(): Promise<ServiceHealth> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/health`);
    if (!response.ok) {
      throw new Error(
        `MCP Orchestrator health check failed: ${response.statusText}`
      );
    }
    return response.json();
  }

  async listAvailableTools(): Promise<Tool[]> {
    const response = await fetch(`${SERVICES.MCP_ORCHESTRATOR}/tools`);
    if (!response.ok) {
      throw new Error(`Failed to list tools: ${response.statusText}`);
    }
    const data = await response.json();
    return data.tools || [];
  }

  async getServicesRoutes(): Promise<RoutesResponse> {
    const response = await fetch(
      `${SERVICES.MAIN_ORCHESTRATOR}/services/routes`
    );
    if (!response.ok) {
      throw new Error(`Failed to get services routes: ${response.statusText}`);
    }
    return response.json();
  }

  // ============================================================================
  // Audio Methods
  // ============================================================================

  async transcribeAudioDirect(
    request: TranscriptionRequest
  ): Promise<TranscriptionResponse> {
    return this.audio.transcribeAudio(request);
  }

  async speakTextDirect(request: TTSRequest): Promise<TTSResponse> {
    return this.audio.speakText(request);
  }

  async getAvailableVoices(): Promise<any[]> {
    return this.audio.getVoices();
  }

  // ============================================================================
  // MCP Methods
  // ============================================================================

  async executeTool(toolCall: any): Promise<any> {
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
    if (!response.ok) {
      throw new Error(`Failed to get auth status: ${response.statusText}`);
    }
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
export const serviceManager = ServiceManager.getInstance();
