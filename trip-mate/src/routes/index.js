
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { useAuth } from "../auth/AuthContext";

import MapsLayout from "./MapsLayout";
// pages
import Home from "../pages/Home";
import Chat from "../pages/Chat";
import ItineraryList from "../pages/ItineraryList";
import PlanList from "../pages/PlanList";
import PlanDetail from "../pages/PlanDetail";
import Setup from "../pages/Setup";
import ResetPassword from "../pages/ResetPassword";


function RequireAuth({ children }) {

  const { isAuthed, loading } = useAuth();
  const location = useLocation();

  if (loading) return null; // TODO: show a global Loading component here

  // Redirect to home if not logged in, preserving the original URL (for post-login redirect)
  if (!isAuthed) return <Navigate to="/" replace state={{ from: location }} />;
  return children;
}

/** Centralized routing configuration */
export default function AppRouter() {
  return (
    <Routes>
      <Route element={<MainLayout />}>

        <Route index element={<Home />} />

        <Route element={<MapsLayout />}>

          <Route
            path="chat"
            element={
              <RequireAuth>
                <Chat />
              </RequireAuth>
            }
          />

          <Route path="setup"
            element={
              <RequireAuth>
                <Setup />
              </RequireAuth>
            } />

          <Route
            path="plan/:id"
            element={
              <RequireAuth>
                <PlanDetail />
              </RequireAuth>
            }
          />

          <Route
            path="itinerary"
            element={
              <RequireAuth>
                <ItineraryList />
              </RequireAuth>
            }
          />
        </Route>

        <Route
          path="plan"
          element={
            <RequireAuth>
              <PlanList />
            </RequireAuth>
          }
        />

        <Route path="reset-password" element={<ResetPassword />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
