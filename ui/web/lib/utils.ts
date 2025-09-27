/**
 * Utility functions for the Jarvis web application
 */

import { Tool, ToolCategory, ServiceInfo, ServiceStatus } from "@/types";
import { TOOL_CATEGORIES } from "./constants";

// ============================================================================
// Date and Time Utilities
// ============================================================================

export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString();
};

export const formatDate = (date: Date): string => {
  return date.toLocaleDateString();
};

export const formatDateTime = (date: Date): string => {
  return `${formatDate(date)} ${formatTime(date)}`;
};

export const getRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return "Just now";
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days !== 1 ? "s" : ""} ago`;
  }
};

// ============================================================================
// String Utilities
// ============================================================================

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + "...";
};

export const capitalizeFirst = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

export const sanitizeText = (text: string): string => {
  return text
    .replace(/[<>]/g, "") // Remove potential HTML tags
    .replace(/[\r\n\t]/g, " ") // Replace line breaks and tabs with spaces
    .replace(/\s+/g, " ") // Replace multiple spaces with single space
    .trim();
};

export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// ============================================================================
// Tool Utilities
// ============================================================================

export const getToolCategory = (toolName: string): ToolCategory => {
  const name = toolName.toLowerCase();

  if (name.includes("gmail") || name.includes("email")) {
    return TOOL_CATEGORIES.GMAIL;
  } else if (name.includes("calendar")) {
    return TOOL_CATEGORIES.CALENDAR;
  } else if (name.includes("notification") || name.includes("reminder")) {
    return TOOL_CATEGORIES.NOTIFICATIONS;
  } else if (name.includes("hue")) {
    return TOOL_CATEGORIES.HUE;
  }

  return TOOL_CATEGORIES.OTHER;
};

export const groupToolsByCategory = (
  tools: Tool[]
): Record<ToolCategory, Tool[]> => {
  return tools.reduce((acc, tool) => {
    const category = getToolCategory(tool.name);
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(tool);
    return acc;
  }, {} as Record<ToolCategory, Tool[]>);
};

export const sortToolsByName = (tools: Tool[]): Tool[] => {
  return [...tools].sort((a, b) => a.name.localeCompare(b.name));
};

export const filterToolsByCategory = (
  tools: Tool[],
  category: ToolCategory
): Tool[] => {
  return tools.filter((tool) => getToolCategory(tool.name) === category);
};

// ============================================================================
// Service Utilities
// ============================================================================

export const getServiceStatus = (service: ServiceInfo): ServiceStatus => {
  if (service.loading) return "loading";
  if (service.error || service.health?.status === "error") return "error";
  if (service.health?.status === "healthy") return "healthy";
  return "unknown";
};

export const isServiceHealthy = (service: ServiceInfo): boolean => {
  return getServiceStatus(service) === "healthy";
};

export const getAllServicesHealthy = (services: ServiceInfo[]): boolean => {
  return services.every((service) => isServiceHealthy(service));
};

export const getServiceError = (service: ServiceInfo): string | null => {
  if (service.error) return service.error;
  if (service.health?.error) return service.health.error;
  return null;
};

// ============================================================================
// Audio Utilities
// ============================================================================

export const formatDuration = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  }
  return `${remainingSeconds}s`;
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

export const isValidAudioFile = (file: File): boolean => {
  const validTypes = ["audio/webm", "audio/mp4", "audio/wav", "audio/mpeg"];
  return validTypes.includes(file.type);
};

// ============================================================================
// Validation Utilities
// ============================================================================

export const validateMessage = (
  message: string
): { isValid: boolean; error?: string } => {
  if (!message || message.trim().length === 0) {
    return { isValid: false, error: "Message cannot be empty" };
  }

  if (message.length > 1000) {
    return { isValid: false, error: "Message is too long" };
  }

  return { isValid: true };
};

export const validateTranscript = (
  transcript: string
): { isValid: boolean; error?: string } => {
  if (!transcript || transcript.trim().length === 0) {
    return { isValid: false, error: "Transcript cannot be empty" };
  }

  if (transcript.length > 500) {
    return { isValid: false, error: "Transcript is too long" };
  }

  return { isValid: true };
};

// ============================================================================
// Array Utilities
// ============================================================================

export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

export const unique = <T>(array: T[]): T[] => {
  return Array.from(new Set(array));
};

export const groupBy = <T, K extends string | number>(
  array: T[],
  keyFn: (item: T) => K
): Record<K, T[]> => {
  return array.reduce((groups, item) => {
    const key = keyFn(item);
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {} as Record<K, T[]>);
};

// ============================================================================
// Object Utilities
// ============================================================================

export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== "object") return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as T;
  if (obj instanceof Array) return obj.map((item) => deepClone(item)) as T;
  if (typeof obj === "object") {
    const cloned = {} as Record<string, any>;
    Object.keys(obj).forEach((key) => {
      cloned[key] = deepClone((obj as any)[key]);
    });
    return cloned as T;
  }
  return obj;
};

export const pick = <T extends object, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach((key) => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

export const omit = <T, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach((key) => {
    delete result[key];
  });
  return result;
};

// ============================================================================
// Error Utilities
// ============================================================================

export const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "An unknown error occurred";
};

export const isNetworkError = (error: unknown): boolean => {
  if (error instanceof Error) {
    return (
      error.name === "NetworkError" ||
      error.message.includes("fetch") ||
      error.message.includes("network")
    );
  }
  return false;
};

// ============================================================================
// Debounce and Throttle
// ============================================================================

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// ============================================================================
// Local Storage Utilities
// ============================================================================

export const getFromStorage = <T>(key: string, defaultValue: T): T => {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
};

export const setToStorage = <T>(key: string, value: T): void => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error("Failed to save to localStorage:", error);
  }
};

export const removeFromStorage = (key: string): void => {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error("Failed to remove from localStorage:", error);
  }
};

// ============================================================================
// Class Name Utilities
// ============================================================================

export const cn = (
  ...classes: (string | undefined | null | false)[]
): string => {
  return classes.filter(Boolean).join(" ");
};
