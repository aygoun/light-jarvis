/**
 * Status service for monitoring service health and tools
 */

import { BaseService } from "./BaseService";
import { ServiceHealth, Tool } from "@/types";

export class StatusService extends BaseService {
  constructor(baseUrl: string) {
    super(baseUrl);
  }

  /**
   * Get service health status
   */
  async getHealth(): Promise<ServiceHealth> {
    return this.get<ServiceHealth>("/health");
  }

  /**
   * Get all available tools
   */
  async getTools(): Promise<Tool[]> {
    const response = await this.get<{ tools: Tool[] }>("/tools");
    return response.tools || [];
  }

  /**
   * Get services status
   */
  async getServicesStatus(): Promise<Record<string, ServiceHealth>> {
    return this.get<Record<string, ServiceHealth>>("/services/status");
  }
}
