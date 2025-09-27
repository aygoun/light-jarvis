/**
 * Base service class for API communication
 */

import { ApiError, ApiResponse } from "@/types";
import { ERROR_MESSAGES } from "@/lib/constants";

export abstract class BaseService {
  protected baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * Make a GET request
   */
  protected async get<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Make a POST request
   */
  protected async post<T>(endpoint: string, data?: any): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: data ? JSON.stringify(data) : undefined,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Make a POST request with FormData
   */
  protected async postFormData<T>(
    endpoint: string,
    formData: FormData
  ): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Make a streaming request
   */
  protected async stream<T>(
    endpoint: string,
    data: any,
    onToken: (token: string) => void,
    onComplete: (finalResponse: string) => void,
    onError: (error: string) => void,
    signal?: AbortSignal
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
        signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No response body reader available");
      }

      const decoder = new TextDecoder();
      let buffer = "";
      let fullResponse = "";

      while (true) {
        // Check if the request was aborted
        if (signal?.aborted) {
          reader.cancel();
          return;
        }

        const { done, value } = await reader.read();

        if (done) {
          onComplete(fullResponse);
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
              onComplete(fullResponse);
              return;
            }

            if (data.trim()) {
              fullResponse += data;
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

  /**
   * Handle errors consistently
   */
  protected handleError(error: unknown): ApiError {
    if (error instanceof Error) {
      return {
        message: error.message,
        code: "API_ERROR",
      };
    }

    return {
      message: ERROR_MESSAGES.SERVICE_UNAVAILABLE,
      code: "UNKNOWN_ERROR",
    };
  }

  /**
   * Check if the service is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.get("/health");
      return true;
    } catch {
      return false;
    }
  }
}
