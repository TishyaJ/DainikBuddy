import React, { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { DomainProvider, useDomain } from "./context/DomainContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { PhoneFrame } from "./components/PhoneFrame";
import { BottomNav } from "./components/BottomNav";
import DailyHub from "./pages/DailyHub";
import FinanceBuddy from "./pages/FinanceBuddy";
import WellnessBuddy from "./pages/WellnessBuddy";
import DiscoverBuddy from "./pages/DiscoverBuddy";
import ChatCenter from "./pages/ChatCenter";
import BuddyChat from "./pages/BuddyChat";
import Profile from "./pages/Profile";
import Onboarding from "./pages/Onboarding";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import { api } from "./lib/api";
import { Loader2 } from "lucide-react";

const ROUTE_DOMAIN = {
  "/": "daily",
  "/finance": "finance",
  "/wellness": "wellness",
  "/discover": "discover",
  "/chat": "helper",
  "/profile": "helper",
};

/** Wrapper that redirects unauthenticated users to /login */
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-full">
        <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

/** Wrapper that redirects authenticated users away from auth pages */
const GuestRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-full">
        <Loader2 className="h-6 w-6 animate-spin text-purple-500" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

const Shell = () => {
  const loc = useLocation();
  const { setDomain } = useDomain();
  const isChat = loc.pathname.startsWith("/chat/");
  const isProfile = loc.pathname === "/profile";
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (isChat || isProfile) return;
    const d = ROUTE_DOMAIN[loc.pathname] || "daily";
    setDomain(d);
  }, [loc.pathname, isChat, isProfile, setDomain]);

  useEffect(() => {
    api.get("/profile").then((r) => setProfile(r.data)).catch(() => setProfile({ onboarded: true }));
  }, []);

  const showOnboarding = profile && !profile.onboarded;
  const showNav = !isChat && !isProfile && !showOnboarding;

  return (
    <>
      {showOnboarding ? (
        <Onboarding onDone={() => api.get("/profile").then((r) => setProfile(r.data))} />
      ) : (
        <Routes>
          <Route path="/" element={<DailyHub />} />
          <Route path="/finance" element={<FinanceBuddy />} />
          <Route path="/wellness" element={<WellnessBuddy />} />
          <Route path="/discover" element={<DiscoverBuddy />} />
          <Route path="/chat" element={<ChatCenter />} />
          <Route path="/chat/:buddy" element={<BuddyChat />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      )}
      {showNav && <BottomNav />}
    </>
  );
};

const AuthLoadingScreen = () => (
  <PhoneFrame>
    <div className="flex items-center justify-center min-h-full">
      <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
    </div>
  </PhoneFrame>
);

function App() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return <AuthLoadingScreen />;
  }

  return (
    <Routes>
      {/* Auth pages — standalone, no Shell/BottomNav */}
      <Route
        path="/login"
        element={
          <GuestRoute>
            <PhoneFrame>
              <LoginPage />
            </PhoneFrame>
          </GuestRoute>
        }
      />
      <Route
        path="/register"
        element={
          <GuestRoute>
            <PhoneFrame>
              <RegisterPage />
            </PhoneFrame>
          </GuestRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <GuestRoute>
            <PhoneFrame>
              <ForgotPasswordPage />
            </PhoneFrame>
          </GuestRoute>
        }
      />

      {/* Protected app routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <PhoneFrame>
              <Shell />
            </PhoneFrame>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function AppWrapper() {
  return (
    <AuthProvider>
      <DomainProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </DomainProvider>
    </AuthProvider>
  );
}

export default AppWrapper;
