"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  ArrowLeft,
  Server,
  Mic,
  Settings,
  Mail,
  Calendar,
  Bell,
  Lightbulb,
  Code,
} from "lucide-react";
import Link from "next/link";
import { ServiceHealth } from "@/types";
import { serviceManager } from "@/services/ServiceManager";

interface ServiceInfo {
  name: string;
  port: number;
  description: string;
  icon: React.ReactNode;
  health: ServiceHealth | null;
  loading: boolean;
  error: string | null;
}

export default function StatusPage() {
  const [services, setServices] = useState<ServiceInfo[]>([
    {
      name: "Main Orchestrator",
      port: 3002,
      description: "Coordinates all services and handles chat requests",
      icon: <Server className="w-5 h-5" />,
      health: null,
      loading: true,
      error: null,
    },
    {
      name: "Whisper Service",
      port: 3001,
      description: "Speech-to-text and text-to-speech functionality",
      icon: <Mic className="w-5 h-5" />,
      health: null,
      loading: true,
      error: null,
    },
    {
      name: "MCP Orchestrator",
      port: 3000,
      description: "Gmail, Calendar, and Notification tools",
      icon: <Settings className="w-5 h-5" />,
      health: null,
      loading: true,
      error: null,
    },
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [availableTools, setAvailableTools] = useState<any[]>([]);
  const [toolsLoading, setToolsLoading] = useState(false);

  // Helper function to group tools by category
  const groupToolsByCategory = (tools: any[]) => {
    return tools.reduce((acc: { [key: string]: any[] }, tool) => {
      const category = getToolCategory(tool.name);
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(tool);
      return acc;
    }, {});
  };

  // Helper function to determine tool category
  const getToolCategory = (toolName: string) => {
    if (toolName.includes("gmail") || toolName.includes("email")) {
      return "Gmail";
    } else if (toolName.includes("calendar")) {
      return "Calendar";
    } else if (
      toolName.includes("notification") ||
      toolName.includes("reminder")
    ) {
      return "Notifications";
    } else if (toolName.includes("hue")) {
      return "Hue";
    }
    return "Other";
  };

  // Helper function to get category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Gmail":
        return <Mail className="w-5 h-5 text-red-400" />;
      case "Calendar":
        return <Calendar className="w-5 h-5 text-blue-400" />;
      case "Notifications":
        return <Bell className="w-5 h-5 text-yellow-400" />;
      case "Hue":
        return <Lightbulb className="w-5 h-5 text-green-400" />;
      default:
        return <Settings className="w-5 h-5 text-gray-400" />;
    }
  };

  const checkServicesHealth = async () => {
    setIsRefreshing(true);

    try {
      const healthData = await serviceManager.status.getServicesStatus();
      console.log("Health data received:", healthData);

      setServices((prev) =>
        prev.map((service) => {
          // Map service names to health data keys
          let serviceKey: keyof typeof healthData;
          if (service.name === "Main Orchestrator") {
            serviceKey = "assistant";
          } else if (service.name === "Whisper Service") {
            serviceKey = "whisper_service";
          } else if (service.name === "MCP Orchestrator") {
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
        })
      );

      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to check services health:", error);
      setServices((prev) =>
        prev.map((service) => ({
          ...service,
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        }))
      );
    } finally {
      setIsRefreshing(false);
    }
  };

  const loadAvailableTools = async () => {
    setToolsLoading(true);
    try {
      const tools = await serviceManager.listAvailableTools();
      setAvailableTools(tools);
    } catch (error) {
      console.error("Failed to load tools:", error);
    } finally {
      setToolsLoading(false);
    }
  };

  useEffect(() => {
    checkServicesHealth();
    loadAvailableTools();

    // Check health every 10 seconds
    const interval = setInterval(checkServicesHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (service: ServiceInfo) => {
    if (service.loading) {
      return <RefreshCw className="w-5 h-5 animate-spin text-blue-400" />;
    }

    if (service.error || service.health?.status === "error") {
      return <XCircle className="w-5 h-5 text-red-400" />;
    }

    if (service.health?.status === "healthy") {
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    }

    return <AlertCircle className="w-5 h-5 text-yellow-400" />;
  };

  const getStatusText = (service: ServiceInfo) => {
    if (service.loading) return "Checking...";
    if (service.error) return "Error";
    if (service.health?.status === "healthy") return "Healthy";
    if (service.health?.status === "error") return "Error";
    return "Unknown";
  };

  const getStatusColor = (service: ServiceInfo) => {
    if (service.loading) return "text-blue-400";
    if (service.error || service.health?.status === "error")
      return "text-red-400";
    if (service.health?.status === "healthy") return "text-green-400";
    return "text-yellow-400";
  };

  const allHealthy = services.every(
    (service) => service.health?.status === "healthy" && !service.error
  );

  const formatLastUpdated = (date: Date) => {
    return date.toLocaleTimeString();
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-300" />
              </Link>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8">
                  <img
                    src="/logo.svg"
                    alt="Jarvis Logo"
                    className="w-full h-full object-contain"
                  />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    System Status
                  </h1>
                  <p className="text-gray-400">
                    Real-time monitoring of all Jarvis services
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {lastUpdated && (
                <span className="text-sm text-gray-400">
                  Last updated: {formatLastUpdated(lastUpdated)}
                </span>
              )}
              <Link
                href="/routes"
                className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
                title="View API Routes"
              >
                <Code className="w-5 h-5 text-gray-300" />
              </Link>
              <button
                onClick={checkServicesHealth}
                disabled={isRefreshing}
                className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-50 transition-colors"
              >
                <RefreshCw
                  className={`w-5 h-5 text-gray-300 ${
                    isRefreshing ? "animate-spin" : ""
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Overall Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">
                  Overall System Status
                </h2>
                <p className="text-gray-400">
                  {allHealthy
                    ? "All services are running normally"
                    : "Some services may have issues"}
                </p>
              </div>
              <div className="flex items-center space-x-3">
                {allHealthy ? (
                  <>
                    <CheckCircle className="w-8 h-8 text-green-400" />
                    <span className="text-green-400 font-semibold text-lg">
                      All Systems Operational
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-8 h-8 text-yellow-400" />
                    <span className="text-yellow-400 font-semibold text-lg">
                      Issues Detected
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence>
            {services.map((service, index) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-gray-700/50">
                      {service.icon}
                    </div>
                    <div>
                      <h3 className="font-semibold text-white">
                        {service.name}
                      </h3>
                      <p className="text-sm text-gray-400">
                        Port {service.port}
                      </p>
                    </div>
                  </div>
                  {getStatusIcon(service)}
                </div>

                <p className="text-sm text-gray-300 mb-4">
                  {service.description}
                </p>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Status:</span>
                    <span
                      className={`text-sm font-medium ${getStatusColor(
                        service
                      )}`}
                    >
                      {getStatusText(service)}
                    </span>
                  </div>

                  {service.error && (
                    <div className="text-xs text-red-400 bg-red-900/20 p-2 rounded">
                      {service.error}
                    </div>
                  )}

                  {service.health?.status === "healthy" && (
                    <div className="space-y-1">
                      {service.health.tools_count && (
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>Tools:</span>
                          <span className="text-green-400">
                            {service.health.tools_count}
                          </span>
                        </div>
                      )}
                      {service.health.auth_initialized && (
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>Auth:</span>
                          <span className="text-green-400">Ready</span>
                        </div>
                      )}
                      {service.health.google_authenticated && (
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>Google:</span>
                          <span className="text-green-400">Connected</span>
                        </div>
                      )}
                      {service.health.assistant_initialized && (
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>Assistant:</span>
                          <span className="text-green-400">Ready</span>
                        </div>
                      )}
                      {service.health.stt && (
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>STT:</span>
                          <span className="text-green-400">
                            {service.health.stt.status}
                          </span>
                        </div>
                      )}
                      {service.health.tts && (
                        <div className="flex justify-between text-xs text-gray-400">
                          <span>TTS:</span>
                          <span className="text-green-400">
                            {service.health.tts.status}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Available Tools */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">
                Available Tools{" "}
                <span className="text-gray-400 text-sm font-normal">
                  ({availableTools.length} tools)
                </span>
              </h2>
              <button
                onClick={loadAvailableTools}
                disabled={toolsLoading}
                className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 disabled:opacity-50 transition-colors"
              >
                <RefreshCw
                  className={`w-4 h-4 text-gray-300 ${
                    toolsLoading ? "animate-spin" : ""
                  }`}
                />
              </button>
            </div>

            {toolsLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
                <span className="ml-2 text-gray-400">Loading tools...</span>
              </div>
            ) : availableTools.length > 0 ? (
              <div className="space-y-6">
                {Object.entries(groupToolsByCategory(availableTools)).map(
                  ([category, tools], categoryIndex) => (
                    <motion.div
                      key={category}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: categoryIndex * 0.1 }}
                      className="space-y-4"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-gray-700/50">
                          {getCategoryIcon(category)}
                        </div>
                        <h3 className="text-lg font-semibold text-white">
                          {category}
                        </h3>
                        <span className="text-sm text-gray-400">
                          ({tools.length} tool{tools.length !== 1 ? "s" : ""})
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {tools.map((tool, toolIndex) => (
                          <motion.div
                            key={tool.name}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                              delay: categoryIndex * 0.1 + toolIndex * 0.05,
                            }}
                            className="bg-gray-900/30 rounded-lg p-4 border border-gray-700"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <h4 className="font-medium text-white text-sm">
                                {tool.name}
                              </h4>
                              <div className="w-2 h-2 bg-green-400 rounded-full" />
                            </div>
                            <p className="text-xs text-gray-400 mb-3">
                              {tool.description}
                            </p>
                            {tool.inputSchema &&
                              tool.inputSchema.properties && (
                                <div className="space-y-1">
                                  <p className="text-xs text-gray-500 font-medium">
                                    Parameters:
                                  </p>
                                  <div className="space-y-1">
                                    {Object.entries(
                                      tool.inputSchema.properties
                                    ).map(([key, prop]: [string, any]) => (
                                      <div
                                        key={key}
                                        className="text-xs text-gray-400"
                                      >
                                        <span className="font-mono text-blue-400">
                                          {key}
                                        </span>
                                        <span className="text-gray-500">
                                          : {prop.type}
                                        </span>
                                        {prop.description && (
                                          <span className="text-gray-600 ml-1">
                                            - {prop.description}
                                          </span>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-400">No tools available</p>
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-600">
              <p className="text-xs text-gray-500 text-center">
                {availableTools.length} tool
                {availableTools.length !== 1 ? "s" : ""} available
              </p>
            </div>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <p className="text-sm text-gray-500">
            Services are automatically checked every 10 seconds
          </p>
        </motion.div>
      </div>
    </div>
  );
}
