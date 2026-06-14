import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

/**
 * User-friendly error display with retry capability.
 * Never shows raw HTTP codes or stack traces.
 */
export default function ErrorCard({
    message = "Something went wrong. Please try again.",
    onRetry,
    testid = "error-card",
}) {
    return (
        <div
            data-testid={testid}
            className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 flex flex-col items-center text-center gap-3"
        >
            <div className="w-11 h-11 rounded-full bg-rose-50 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-rose-500" />
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">{message}</p>
            {onRetry && (
                <button
                    onClick={onRetry}
                    data-testid={`${testid}-retry`}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bdy-bg text-white active:scale-95 transition"
                >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Retry
                </button>
            )}
        </div>
    );
}
