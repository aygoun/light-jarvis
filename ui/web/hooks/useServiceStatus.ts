/**
 * Custom hook for managing service status and health monitoring
 */

import { useState, useEffect, useCallback } from "react";
import { serviceManager } from "@/services/ServiceManager";
import { ServiceInfo, ServiceHealth, Tool, StatusPageState } from "@/types";
import { SERVICE_NAMES, UI_CONSTANTS } from "@/lib/constants";
import {
  getServiceStatus,
  isServiceHealthy,
  getAllServicesHealthy,
} from "@/lib/utils";

const initialServices: ServiceInfo[] = [
  {
    name: SERVICE_NAMES.MAIN_ORCHESTRATOR,
    port: 3002,
    description: "Coordinates all services and handles chat requests",
    icon: null, // Will be set by component
    health: null,
    loading: true,
    error: null,
  },
  {
    name: SERVICE_NAMES.WHISPER_SERVICE,
    port: 3001,
    description: "Speech-to-text and text-to-speech functionality",
    icon: null, // Will be set by component
    health: null,
    loading: true,
    error: null,
  },
  {
    name: SERVICE_NAMES.MCP_ORCHESTRATOR,
    port: 3000,
    description: "Gmail, Calendar, and Notification tools",
    icon: null, // Will be set by component
    health: null,
    loading: true,
    error: null,
  },
];

const initialState: StatusPageState = {
  services: initialServices,
  isRefreshing: false,
  lastUpdated: null,
  availableTools: [],
  toolsLoading: false,
};

export const useServiceStatus = () => {
  const [state, setState] = useState<StatusPageState>(initialState);

  // ============================================================================
  // State Setters
  // ============================================================================

  const setServices = useCallback((services: ServiceInfo[]) => {
    setState((prev) => ({ ...prev, services }));
  }, []);

  const setIsRefreshing = useCallback((isRefreshing: boolean) => {
    setState((prev) => ({ ...prev, isRefreshing }));
  }, []);

  const setLastUpdated = useCallback((lastUpdated: Date | null) => {
    setState((prev) => ({ ...prev, lastUpdated }));
  }, []);

  const setAvailableTools = useCallback((availableTools: Tool[]) => {
    setState((prev) => ({ ...prev, availableTools }));
  }, []);

  const setToolsLoading = useCallback((toolsLoading: boolean) => {
    setState((prev) => ({ ...prev, toolsLoading }));
  }, []);

  // ============================================================================
  // Service Health Functions
  // ============================================================================

  const checkServicesHealth = useCallback(async () => {
    setIsRefreshing(true);

    try {
      const healthData = await serviceManager.status.getServicesStatus();
      console.log("Health data received:", healthData);

      setState((prev) => ({
        ...prev,
        services: prev.services.map((service) => {
          // Map service names to health data keys
          let serviceKey: keyof typeof healthData;
          if (service.name === SERVICE_NAMES.MAIN_ORCHESTRATOR) {
            serviceKey = "assistant";
          } else if (service.name === SERVICE_NAMES.WHISPER_SERVICE) {
            serviceKey = "whisper_service";
          } else if (service.name === SERVICE_NAMES.MCP_ORCHESTRATOR) {
            serviceKey = "mcp_orchestrator";
          } else {
            serviceKey = "assistant"; // fallback
          }

          const health = healthData[serviceKey];

          return {
            ...service,
            health,
            loading: false,
            error: health?.status === "error" ? health.error || null : null,
          };
        }),
      }));

      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to check services health:", error);
      setState((prev) => ({
        ...prev,
        services: prev.services.map((service) => ({
          ...service,
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        })),
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [setIsRefreshing, setLastUpdated]);

  // ============================================================================
  // Tools Functions
  // ============================================================================

  const loadAvailableTools = useCallback(async () => {
    setToolsLoading(true);
    try {
      const tools = await serviceManager.listAvailableTools();
      setAvailableTools(tools);
    } catch (error) {
      console.error("Failed to load tools:", error);
    } finally {
      setToolsLoading(false);
    }
  }, [setAvailableTools, setToolsLoading]);

  // ============================================================================
  // Utility Functions
  // ============================================================================

  const getServiceStatusText = useCallback((service: ServiceInfo): string => {
    if (service.loading) return "Checking...";
    if (service.error) return "Error";
    if (service.health?.status === "healthy") return "Healthy";
    if (service.health?.status === "error") return "Error";
    return "Unknown";
  }, []);

  const getServiceStatusColor = useCallback((service: ServiceInfo): string => {
    if (service.loading) return "text-blue-400";
    if (service.error || service.health?.status === "error")
      return "text-red-400";
    if (service.health?.status === "healthy") return "text-green-400";
    return "text-yellow-400";
  }, []);

  const getServiceIcon = useCallback((service: ServiceInfo) => {
    // This will be handled by the component that uses this hook
    return service.icon;
  }, []);

  const allHealthy = getAllServicesHealthy(state.services);

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    checkServicesHealth();
    loadAvailableTools();

    // Check health every 10 seconds
    const interval = setInterval(
      checkServicesHealth,
      UI_CONSTANTS.REFRESH_INTERVAL
    );
    return () => clearInterval(interval);
  }, [checkServicesHealth, loadAvailableTools]);

  // ============================================================================
  // Return Hook Interface
  // ============================================================================

  return {
    // State
    ...state,

    // Setters
    setServices,
    setIsRefreshing,
    setLastUpdated,
    setAvailableTools,
    setToolsLoading,

    // Functions
    checkServicesHealth,
    loadAvailableTools,
    getServiceStatusText,
    getServiceStatusColor,
    getServiceIcon,

    // Computed
    allHealthy,
  };
};
