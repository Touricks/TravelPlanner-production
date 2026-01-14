import { Outlet } from "react-router-dom";
import MapsProvider from "../components/maps/MapsProvider";

export default function MapsLayout() {
  return <MapsProvider>
    <Outlet />
  </MapsProvider>;
}