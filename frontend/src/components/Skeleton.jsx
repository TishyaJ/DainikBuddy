import React from "react";

/**
 * Pulsing line placeholder for text content.
 */
export function SkeletonLine({ width = "100%", height = "h-3", className = "" }) {
    return (
        <div
            data-testid="skeleton-line"
            className={`bg-slate-200 rounded animate-pulse ${height} ${className}`}
            style={{ width }}
        />
    );
}

/**
 * Circular placeholder for avatars or icons.
 */
export function SkeletonCircle({ size = "w-10 h-10", className = "" }) {
    return (
        <div
            data-testid="skeleton-circle"
            className={`bg-slate-200 rounded-full animate-pulse ${size} ${className}`}
        />
    );
}

/**
 * Card-shaped placeholder matching the Card component dimensions.
 */
export function SkeletonCard({ lines = 3, className = "" }) {
    return (
        <div
            data-testid="skeleton-card"
            className={`bg-white rounded-2xl p-4 shadow-sm border border-slate-100 space-y-3 ${className}`}
        >
            <SkeletonLine width="40%" height="h-4" />
            {Array.from({ length: lines }).map((_, i) => (
                <SkeletonLine key={i} width={i === lines - 1 ? "60%" : "100%"} />
            ))}
        </div>
    );
}

/**
 * Skeleton group for a list of items.
 */
export function SkeletonList({ count = 3, className = "" }) {
    return (
        <div className={`space-y-3 ${className}`} data-testid="skeleton-list">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white border border-slate-100">
                    <SkeletonCircle size="w-9 h-9" />
                    <div className="flex-1 space-y-2">
                        <SkeletonLine width="70%" height="h-3" />
                        <SkeletonLine width="40%" height="h-2.5" />
                    </div>
                </div>
            ))}
        </div>
    );
}
