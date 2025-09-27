/**
 * Audio recording service using MediaRecorder API
 * Sends recorded audio to local Whisper service for transcription
 */

export interface AudioRecorderOptions {
  onTranscript: (transcript: string) => void;
  onError: (error: string) => void;
  onStart?: () => void;
  onStop?: () => void;
  whisperServiceUrl?: string;
}

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private isRecording = false;
  private options: AudioRecorderOptions;
  private minimumRecordingTime = 2000; // 2 seconds minimum
  private recordingStartTime = 0;

  constructor(options: AudioRecorderOptions) {
    this.options = {
      whisperServiceUrl: "http://localhost:3001", // Default whisper service URL
      ...options,
    };

    // Test connection to Whisper service
    this.testConnection();
  }

  private async testConnection(): Promise<void> {
    try {
      const response = await fetch(
        `${this.options.whisperServiceUrl}/stt/health`
      );
      if (response.ok) {
        console.log("Whisper service is available");
      } else {
        console.warn("Whisper service health check failed:", response.status);
      }
    } catch (error) {
      console.warn("Cannot connect to Whisper service:", error);
    }
  }

  async startRecording(): Promise<void> {
    try {
      // Get microphone access
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Determine the best supported audio format
      let mimeType = "audio/webm;codecs=opus";
      if (MediaRecorder.isTypeSupported("audio/webm")) {
        mimeType = "audio/webm";
      } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
        mimeType = "audio/mp4";
      } else if (MediaRecorder.isTypeSupported("audio/wav")) {
        mimeType = "audio/wav";
      }

      console.log("Using audio format:", mimeType);

      // Create MediaRecorder
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: mimeType,
      });

      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        this.processAudio();
      };

      this.mediaRecorder.onerror = (event) => {
        console.error("MediaRecorder error:", event);
        this.options.onError("Recording failed");
      };

      // Start recording
      this.mediaRecorder.start(1000); // Collect data every second
      this.isRecording = true;
      this.options.onStart?.();

      // Set a minimum recording duration
      this.minimumRecordingTime = 2000; // 2 seconds minimum
      this.recordingStartTime = Date.now();
    } catch (error) {
      console.error("Failed to start recording:", error);
      if (error instanceof Error) {
        if (error.name === "NotAllowedError") {
          this.options.onError(
            "Microphone access denied. Please allow microphone access and try again."
          );
        } else if (error.name === "NotFoundError") {
          this.options.onError(
            "No microphone found. Please connect a microphone and try again."
          );
        } else {
          this.options.onError(`Recording failed: ${error.message}`);
        }
      } else {
        this.options.onError("Failed to start recording");
      }
    }
  }

  stopRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      const recordingDuration = Date.now() - this.recordingStartTime;

      if (recordingDuration < this.minimumRecordingTime) {
        console.log(
          `Recording too short (${recordingDuration}ms), waiting for minimum duration...`
        );
        // Wait for minimum duration
        setTimeout(() => {
          if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.options.onStop?.();
          }
        }, this.minimumRecordingTime - recordingDuration);
      } else {
        this.mediaRecorder.stop();
        this.isRecording = false;
        this.options.onStop?.();
      }
    }
  }

  private async processAudio(): Promise<void> {
    if (this.audioChunks.length === 0) {
      this.options.onError("No audio data recorded");
      return;
    }

    try {
      // Create audio blob
      const audioBlob = new Blob(this.audioChunks, { type: "audio/webm" });

      // Validate audio blob size
      if (audioBlob.size === 0) {
        this.options.onError("Empty audio recording");
        return;
      }

      console.log(`Audio blob size: ${audioBlob.size} bytes`);

      // Send to Whisper service
      await this.transcribeAudio(audioBlob);
    } catch (error) {
      console.error("Failed to process audio:", error);
      this.options.onError("Failed to process audio");
    } finally {
      // Clean up
      this.cleanup();
    }
  }

  private async convertToWav(audioBlob: Blob): Promise<Blob> {
    // For now, we'll send the webm directly and let the backend handle conversion
    // In a production app, you might want to convert to WAV on the frontend
    return audioBlob;
  }

  private async transcribeAudio(audioBlob: Blob): Promise<void> {
    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");
      formData.append("language", "en");
      formData.append("temperature", "0.0");

      console.log("Sending audio to Whisper service...");

      const response = await fetch(
        `${this.options.whisperServiceUrl}/stt/transcribe`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error(
          `HTTP error! status: ${response.status}, body: ${errorText}`
        );
        throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      console.log("Whisper service response:", result);

      if (result.success && result.transcript) {
        console.log("Transcription successful:", result.transcript);
        this.options.onTranscript(result.transcript);
      } else {
        console.error("Transcription failed:", result);
        this.options.onError(result.error || "Transcription failed");
      }
    } catch (error) {
      console.error("Transcription failed:", error);
      if (error instanceof Error) {
        this.options.onError(`Transcription failed: ${error.message}`);
      } else {
        this.options.onError("Transcription failed");
      }
    }
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.audioChunks = [];
    this.mediaRecorder = null;
  }

  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }

  destroy(): void {
    this.stopRecording();
    this.cleanup();
  }
}
