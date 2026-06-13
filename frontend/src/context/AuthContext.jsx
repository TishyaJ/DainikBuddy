import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "../lib/api";

const AuthContext = createContext({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    login: async () => { },
    register: async () => { },
    logout: () => { },
    refreshToken: async () => { },
});

const TOKEN_KEY = "pb_access_token";
const REFRESH_KEY = "pb_refresh_token";

function decodeJwtPayload(token) {
    try {
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split("")
                .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
                .join("")
        );
        return JSON.parse(jsonPayload);
    } catch {
        return null;
    }
}

function isTokenExpired(token) {
    const payload = decodeJwtPayload(token);
    if (!payload || !payload.exp) return true;
    return Date.now() >= payload.exp * 1000;
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const isAuthenticated = !!user;

    const storeTokens = (accessToken, refreshToken) => {
        localStorage.setItem(TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(REFRESH_KEY, refreshToken);
        }
    };

    const clearTokens = () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
    };

    const setUserFromToken = (token) => {
        const payload = decodeJwtPayload(token);
        if (payload) {
            setUser({ email: payload.email || payload.sub, ...payload });
        }
    };

    const login = useCallback(async (email, password) => {
        const response = await api.post("/auth/login", { email, password });
        const { access_token, refresh_token } = response.data;
        storeTokens(access_token, refresh_token);
        setUserFromToken(access_token);
        return response.data;
    }, []);

    const register = useCallback(async (email, password) => {
        const response = await api.post("/auth/register", { email, password });
        const { access_token, refresh_token } = response.data;
        storeTokens(access_token, refresh_token);
        setUserFromToken(access_token);
        return response.data;
    }, []);

    const logout = useCallback(() => {
        clearTokens();
        setUser(null);
    }, []);

    const refreshToken = useCallback(async () => {
        const storedRefresh = localStorage.getItem(REFRESH_KEY);
        if (!storedRefresh) {
            logout();
            return;
        }
        try {
            const response = await api.post("/auth/refresh", {
                refresh_token: storedRefresh,
            });
            const { access_token, refresh_token: newRefresh } = response.data;
            storeTokens(access_token, newRefresh || storedRefresh);
            setUserFromToken(access_token);
        } catch {
            logout();
        }
    }, [logout]);

    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem(TOKEN_KEY);
            if (!token) {
                setIsLoading(false);
                return;
            }
            if (isTokenExpired(token)) {
                await refreshToken();
            } else {
                setUserFromToken(token);
            }
            setIsLoading(false);
        };
        initAuth();
    }, [refreshToken]);

    return (
        <AuthContext.Provider
            value={{ user, isAuthenticated, isLoading, login, register, logout, refreshToken }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
