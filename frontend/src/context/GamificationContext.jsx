import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { api } from "../lib/api";

const GamificationContext = createContext({
    status: null,
    achievements: null,
    loading: true,
    error: null,
    refresh: () => { },
    showLevelUp: false,
    dismissLevelUp: () => { },
});

export const GamificationProvider = ({ children }) => {
    const [status, setStatus] = useState(null);
    const [achievements, setAchievements] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showLevelUp, setShowLevelUp] = useState(false);
    const prevLevelRef = useRef(null);

    const fetchStatus = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const [statusRes, achievementsRes] = await Promise.all([
                api.get("/gamification/status"),
                api.get("/gamification/achievements"),
            ]);

            const newStatus = statusRes.data;
            const newAchievements = achievementsRes.data;

            // Detect level-up transition
            if (prevLevelRef.current !== null && newStatus.level > prevLevelRef.current) {
                setShowLevelUp(true);
            }
            prevLevelRef.current = newStatus.level;

            setStatus(newStatus);
            setAchievements(newAchievements);
        } catch (err) {
            setError(err?.response?.data?.detail || "Failed to load gamification data");
        } finally {
            setLoading(false);
        }
    }, []);

    const dismissLevelUp = useCallback(() => {
        setShowLevelUp(false);
    }, []);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    // Auto-dismiss level-up overlay after 3 seconds
    useEffect(() => {
        if (showLevelUp) {
            const timer = setTimeout(() => {
                setShowLevelUp(false);
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [showLevelUp]);

    return (
        <GamificationContext.Provider
            value={{
                status,
                achievements,
                loading,
                error,
                refresh: fetchStatus,
                showLevelUp,
                dismissLevelUp,
            }}
        >
            {children}
        </GamificationContext.Provider>
    );
};

export const useGamification = () => useContext(GamificationContext);
