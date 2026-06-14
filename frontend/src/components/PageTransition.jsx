import React from "react";
import { motion } from "framer-motion";

/**
 * Wrapper that applies a subtle fade-in + upward slide animation to page content.
 * Duration: 250ms with easeOut easing.
 * Forwards all extra props (data-testid, data-domain, etc.) to the motion.div.
 */
export default function PageTransition({ children, className = "", ...rest }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className={className}
            {...rest}
        >
            {children}
        </motion.div>
    );
}
