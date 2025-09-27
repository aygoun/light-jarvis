"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { CheckCircle, AlertCircle, XCircle, RefreshCw } from "lucide-react";
import { ServiceHealth } from "@/types";
import { serviceManager } from "@/services/ServiceManager";

interface StatusIndicatorProps {
  className?: string;
  onStatusChange?: (allHealthy: boolean) => void;
}

export function StatusIndicator({
  className = "",
  onStatusChange,
}: StatusIndicatorProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [allHealthy, setAllHealthy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const healthData = await serviceManager.status.getServicesStatus();

      // Check if all services are healthy
      const servicesHealthy = Object.values(healthData).every(
        (service: ServiceHealth) => service.status === "healthy"
      );

      setAllHealthy(servicesHealthy);
      onStatusChange?.(servicesHealthy);
    } catch (error) {
      console.error("Status check failed:", error);
      setError(error instanceof Error ? error.message : "Status check failed");
      setAllHealthy(false);
      onStatusChange?.(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();

    // Check status every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = () => {
    if (isLoading) {
      return <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />;
    }

    if (error || !allHealthy) {
      return <XCircle className="w-4 h-4 text-red-400" />;
    }

    return <CheckCircle className="w-4 h-4 text-green-400" />;
  };

  const getStatusText = () => {
    if (isLoading) return "Checking...";
    if (error) return "Error";
    if (allHealthy) return "All Systems Operational";
    return "Some Issues Detected";
  };

  const getStatusColor = () => {
    if (isLoading) return "text-blue-400";
    if (error || !allHealthy) return "text-red-400";
    return "text-green-400";
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center space-x-2 ${className}`}
    >
      {getStatusIcon()}
      <span className={`text-sm font-medium ${getStatusColor()}`}>
        {getStatusText()}
      </span>
    </motion.div>
  );
}
