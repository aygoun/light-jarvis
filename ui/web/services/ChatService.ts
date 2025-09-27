/**
 * Chat service for handling chat functionality
 */

import { BaseService } from "./BaseService";
import {
  ChatRequest,
  ChatResponse,
  TTSRequest,
  TTSResponse,
  TranscriptionRequest,
  TranscriptionResponse,
  StreamResponse,
} from "@/types";

export class ChatService extends BaseService {
  constructor(baseUrl: string) {
    super(baseUrl);
  }

  /**
   * Send a chat message
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.post<ChatResponse>("/chat", request);
  }

  /**
   * Send a chat message with streaming response
   */
  async sendMessageStream(
    request: ChatRequest,
    callbacks: StreamResponse,
    signal?: AbortSignal
  ): Promise<void> {
    return this.stream(
      "/chat/stream",
      request,
      callbacks.onToken,
      callbacks.onComplete,
      callbacks.onError,
      signal
    );
  }

  /**
   * Transcribe audio
   */
  async transcribeAudio(
    request: TranscriptionRequest
  ): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append("file", request.file);

    if (request.language) {
      formData.append("language", request.language);
    }

    if (request.temperature !== undefined) {
      formData.append("temperature", request.temperature.toString());
    }

    return this.postFormData<TranscriptionResponse>(
      "/stt/transcribe",
      formData
    );
  }

  /**
   * Convert text to speech
   */
  async speakText(request: TTSRequest): Promise<TTSResponse> {
    const formData = new FormData();
    formData.append("text", request.text);

    const response = await fetch(`${this.baseUrl}/tts/speak`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`TTS request failed: ${response.statusText}`);
    }

    // The response is binary audio data, not JSON
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);

    return {
      success: true,
      audio_url: audioUrl,
    };
  }
}
