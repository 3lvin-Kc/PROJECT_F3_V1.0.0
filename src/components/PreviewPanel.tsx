import { useState, useEffect } from "react";
import { Smartphone, Wifi, Signal, Battery, Bluetooth } from "lucide-react";
import { cn } from "@/lib/utils";

interface PreviewPanelProps {
  code?: string;
  theme?: "light" | "dark";
  onPreviewLoad?: (success: boolean) => void;
}

export function PreviewPanel({
  code,
  theme: initialTheme = "light",
  onPreviewLoad,
}: PreviewPanelProps) {
  const [theme, setTheme] = useState<"light" | "dark">(initialTheme);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!code) return;
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
      onPreviewLoad?.(true);
    }, 1500);
    return () => clearTimeout(timer);
  }, [code, onPreviewLoad]);

  return (
    <div className="flex flex-col h-full bg-muted/30">
      {/* Header */}
      

      {/* Centered Mobile Emulator */}
      <div className="flex-1 flex items-center justify-center p-6 overflow-auto">
        {!code ? (
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-pink-500 to-rose-500 rounded-xl flex items-center justify-center mx-auto mb-3">
              <Smartphone className="w-8 h-8 text-white" />
            </div>
            <p className="text-sm text-muted-foreground mb-1">
              No widget to preview yet
            </p>
            <p className="text-xs text-muted-foreground">
              Generate a Flutter widget to see preview
            </p>
          </div>
        ) : (
          <div
            className={cn(
              "relative flex flex-col rounded-[32px] border-[5px] border-gray-800 shadow-2xl overflow-hidden",
              "bg-gradient-to-b from-gray-800 to-gray-900"
            )}
            style={{
              width: "255px", // Smaller width to fit in preview
              height: "460px", // Smaller height to fit completely
            }}
          >
            {/* Android Status Bar */}
            <div className={cn(
              "h-7 px-4 flex items-center justify-between text-xs font-medium",
              theme === "light" ? "bg-white text-gray-900" : "bg-gray-900 text-white"
            )}>
              {/* Left side - Time */}
              <div className="flex items-center">
                <span className="font-mono">9:41</span>
              </div>
              
              {/* Right side - Status icons */}
              <div className="flex items-center gap-1">
                <Signal className="w-3 h-3" />
                <Wifi className="w-3 h-3" />
                <Bluetooth className="w-3 h-3" />
                <Battery className="w-3 h-3" />
                <span className="text-xs ml-1">87%</span>
              </div>
            </div>

            {/* Main Screen Area */}
            <div className={cn(
              "flex-1 relative overflow-hidden",
              theme === "light" ? "bg-white" : "bg-gray-900"
            )}>
              {isLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-sm text-muted-foreground">
                      Loading Preview...
                    </p>
                  </div>
                </div>
              ) : (
                // 👇 Yaha tera actual render aayega
                <div className="w-full h-full bg-white text-gray-900 flex items-center justify-center">
                  <p className="text-xs text-muted-foreground text-center p-4">
                    👇 Replace this with your live Flutter render iframe or
                    component
                  </p>
                </div>
              )}
            </div>

            {/* Android Navigation Bar */}
            
          </div>
        )}
      </div>
    </div>
  );
}
