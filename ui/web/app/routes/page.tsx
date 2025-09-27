"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Server,
  RefreshCw,
  ExternalLink,
  Code,
  Globe,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { serviceManager } from "@/services/ServiceManager";
import { RoutesResponse, ServiceRoutes, RouteInfo } from "@/types";
import { SERVICE_NAMES } from "@/lib/constants";

export default function RoutesPage() {
  const [routesData, setRoutesData] = useState<RoutesResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadRoutes = async () => {
    try {
      setError(null);
      const data = await serviceManager.getServicesRoutes();
      setRoutesData(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load routes:", err);
      setError(err instanceof Error ? err.message : "Failed to load routes");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadRoutes();
  };

  useEffect(() => {
    loadRoutes();
  }, []);

  const getServiceIcon = (serviceName: string) => {
    switch (serviceName) {
      case "main_orchestrator":
        return <Server className="w-5 h-5 text-blue-400" />;
      case "whisper_service":
        return <Globe className="w-5 h-5 text-green-400" />;
      case "mcp_orchestrator":
        return <Code className="w-5 h-5 text-purple-400" />;
      default:
        return <Server className="w-5 h-5 text-gray-400" />;
    }
  };

  const getServiceName = (serviceName: string) => {
    switch (serviceName) {
      case "main_orchestrator":
        return SERVICE_NAMES.MAIN_ORCHESTRATOR;
      case "whisper_service":
        return SERVICE_NAMES.WHISPER_SERVICE;
      case "mcp_orchestrator":
        return SERVICE_NAMES.MCP_ORCHESTRATOR;
      default:
        return serviceName;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "available":
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case "no_openapi":
        return <AlertCircle className="w-4 h-4 text-yellow-400" />;
      case "error":
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "available":
        return "text-green-400";
      case "no_openapi":
        return "text-yellow-400";
      case "error":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  const getMethodColor = (method: string) => {
    switch (method) {
      case "GET":
        return "bg-green-600 text-white";
      case "POST":
        return "bg-blue-600 text-white";
      case "PUT":
        return "bg-yellow-600 text-white";
      case "DELETE":
        return "bg-red-600 text-white";
      case "PATCH":
        return "bg-purple-600 text-white";
      default:
        return "bg-gray-600 text-white";
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex items-center space-x-3">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
          <span className="text-gray-300">Loading routes...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">
            Error Loading Routes
          </h2>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

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
                  <h1 className="text-2xl font-bold text-white">API Routes</h1>
                  <p className="text-gray-400">
                    All available endpoints from Jarvis services
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {lastUpdated && (
                <span className="text-sm text-gray-400">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={handleRefresh}
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
        {/* Summary */}
        {routesData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-white mb-2">
                    Routes Summary
                  </h2>
                  <p className="text-gray-400">
                    {routesData.total_routes} routes across{" "}
                    {routesData.total_services} services
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-400">
                    {routesData.total_routes}
                  </div>
                  <div className="text-sm text-gray-400">Total Routes</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Services */}
        {routesData && (
          <div className="space-y-6">
            {Object.entries(routesData.services).map(
              ([serviceName, serviceData], index) => (
                <motion.div
                  key={serviceName}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6"
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-gray-700/50">
                        {getServiceIcon(serviceName)}
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">
                          {getServiceName(serviceName)}
                        </h3>
                        <p className="text-sm text-gray-400">
                          {serviceData.base_url}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(serviceData.status)}
                      <span
                        className={`text-sm font-medium ${getStatusColor(
                          serviceData.status
                        )}`}
                      >
                        {serviceData.status}
                      </span>
                      <span className="text-sm text-gray-400">
                        {serviceData.total_routes} routes
                      </span>
                    </div>
                  </div>

                  {serviceData.error && (
                    <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                      <p className="text-sm text-red-400">
                        {serviceData.error}
                      </p>
                    </div>
                  )}

                  {serviceData.routes.length > 0 ? (
                    <div className="space-y-3">
                      {serviceData.routes.map((route, routeIndex) => (
                        <motion.div
                          key={`${route.path}-${route.method}`}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{
                            delay: index * 0.1 + routeIndex * 0.05,
                          }}
                          className="bg-gray-900/30 border border-gray-600 rounded-lg p-4 hover:bg-gray-900/50 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <span
                                  className={`px-2 py-1 text-xs font-mono rounded ${getMethodColor(
                                    route.method
                                  )}`}
                                >
                                  {route.method}
                                </span>
                                <code className="text-blue-400 font-mono text-sm">
                                  {route.path}
                                </code>
                              </div>
                              {route.summary && (
                                <p className="text-sm text-gray-300 mb-1">
                                  {route.summary}
                                </p>
                              )}
                              {route.description && (
                                <p className="text-xs text-gray-500">
                                  {route.description}
                                </p>
                              )}
                              {route.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {route.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                            <a
                              href={route.full_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="ml-4 p-2 text-gray-400 hover:text-white transition-colors"
                              title="Open in new tab"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-400">No routes available</p>
                    </div>
                  )}
                </motion.div>
              )
            )}
          </div>
        )}

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 text-center"
        >
          <p className="text-sm text-gray-500">
            Routes are automatically discovered from OpenAPI schemas
          </p>
        </motion.div>
      </div>
    </div>
  );
}
