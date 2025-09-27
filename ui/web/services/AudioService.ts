/**
 * Audio service for handling audio-related functionality
 */

import { BaseService } from "./BaseService";
import {
  TranscriptionRequest,
  TranscriptionResponse,
  TTSRequest,
  TTSResponse,
  Voice,
} from "@/types";

export class AudioService extends BaseService {
  constructor(baseUrl: string) {
    super(baseUrl);
  }

  /**
   * Transcribe audio directly
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
   * Convert text to speech directly
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

    return await response.json();
  }

  /**
   * Get available voices
   */
  async getVoices(): Promise<Voice[]> {
    const response = await this.get<{ voices: Voice[] }>("/tts/voices");
    return response.voices || [];
  }

  /**
   * Check if audio service is healthy
   */
  async isHealthy(): Promise<boolean> {
    try {
      return await this.healthCheck();
    } catch {
      return false;
    }
  }
}
