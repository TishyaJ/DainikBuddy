import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { api } from "../lib/api";

const NotificationContext = createContext({
    notifications: [],
    unreadCount: 0,
    loading: true,
    error: null,
    refresh: () => { },
    markDismissed: () => { },
    preferences: null,
    updatePreferences: () => { },
});

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [preferences, setPreferences] = useState(null);
    const pollRef = useRef(null);

    const fetchNotifications = useCallback(async () => {
        try {
            setError(null);
            const res = await api.get("/notifications");
            setNotifications(res.data.notifications || []);
            setUnreadCount(res.data.count || 0);
        } catch (err) {
            setError(err?.response?.data?.detail || "Failed to load notifications");
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchPreferences = useCallback(async () => {
        try {
            const res = await api.get("/notifications/preferences");
            setPreferences(res.data);
        } catch (err) {
            // Silently fail for preferences fetch
        }
    }, []);

    const markDismissed = useCallback(async (id) => {
        try {
            await api.post(`/notifications/${id}/dismiss`);
            setNotifications((prev) => prev.filter((n) => n.id !== id));
            setUnreadCount((prev) => Math.max(0, prev - 1));
        } catch (err) {
            // Silently fail
        }
    }, []);

    const updatePreferences = useCallback(async (newPrefs) => {
        try {
            const res = await api.patch("/notifications/preferences", newPrefs);
            setPreferences(res.data);
        } catch (err) {
            setError(err?.response?.data?.detail || "Failed to update preferences");
        }
    }, []);

    const subscribePush = useCallback(async () => {
        try {
            if (!("serviceWorker" in navigator) || !("PushManager" in window)) return;

            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisuallyOnly: true,
                applicationServerKey: process.env.REACT_APP_VAPID_PUBLIC_KEY,
            });

            const subJson = subscription.toJSON();
            await api.post("/notifications/subscribe", {
                endpoint: subJson.endpoint,
                keys: subJson.keys,
            });
        } catch (err) {
            // Push subscription failed silently
        }
    }, []);

    const requestPermission = useCallback(async () => {
        if (!("Notification" in window)) return;

        const alreadyAsked = sessionStorage.getItem("pb_notification_permission_asked");
        if (alreadyAsked) return;

        if (Notification.permission === "granted") {
            subscribePush();
        } else if (Notification.permission === "default") {
            sessionStorage.setItem("pb_notification_permission_asked", "true");
            const result = await Notification.requestPermission();
            if (result === "granted") {
                subscribePush();
            }
        }
    }, [subscribePush]);

    // Initial fetch
    useEffect(() => {
        fetchNotifications();
        fetchPreferences();
        requestPermission();
    }, [fetchNotifications, fetchPreferences, requestPermission]);

    // Poll every 60 seconds
    useEffect(() => {
        pollRef.current = setInterval(() => {
            fetchNotifications();
        }, 60000);

        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
            }
        };
    }, [fetchNotifications]);

    return (
        <NotificationContext.Provider
            value={{
                notifications,
                unreadCount,
                loading,
                error,
                refresh: fetchNotifications,
                markDismissed,
                preferences,
                updatePreferences,
            }}
        >
            {children}
        </NotificationContext.Provider>
    );
};

export const useNotifications = () => useContext(NotificationContext);
