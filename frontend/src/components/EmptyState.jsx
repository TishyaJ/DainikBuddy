import React from "react";
import { Card } from "./SubTabs";

/**
 * EmptyState — A reusable empty state component for zero-item views.
 * Provides a consistent pattern with icon, title, description, and optional CTA.
 *
 * Validates: Requirements 13.7
 *
 * @param {React.ElementType} icon - Lucide icon component to display
 * @param {string} title - Main heading text
 * @param {string} description - Descriptive text explaining what belongs here
 * @param {string} [ctaLabel] - Optional button label
 * @param {function} [onCta] - Optional button click handler
 * @param {string} [className] - Optional extra classes for the outer wrapper
 * @param {boolean} [useCard] - Whether to wrap in a Card component (default true)
 */
export const EmptyState = ({
    icon: Icon,
    title,
    description,
    ctaLabel,
    onCta,
    className = "",
    useCard = true,
    testid = "empty-state",
}) => {
    const content = (
        <div className={`flex flex-col items-center text-center py-8 px-4 ${className}`} data-testid={testid}>
            {Icon && (
                <div className="w-14 h-14 rounded-full bdy-soft flex items-center justify-center mb-3">
                    <Icon className="w-7 h-7 bdy-text opacity-60" />
                </div>
            )}
            <h4 className="font-display font-bold text-sm text-slate-700">{title}</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-[250px] leading-relaxed">{description}</p>
            {ctaLabel && onCta && (
                <button
                    onClick={onCta}
                    data-testid={`${testid}-cta`}
                    aria-label={ctaLabel}
                    className="mt-4 px-4 py-2 rounded-full text-xs font-semibold bdy-bg text-white active:scale-95 transition shadow-sm"
                >
                    {ctaLabel}
                </button>
            )}
        </div>
    );

    if (useCard) {
        return <Card>{content}</Card>;
    }

    return content;
};

export default EmptyState;
