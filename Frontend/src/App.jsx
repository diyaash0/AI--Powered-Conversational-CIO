import { useState } from "react";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
 
export default function App() {
  const [role, setRole] = useState(null);
 
  if (!role) return <Login onLogin={setRole} />;
  return <Dashboard role={role} onLogout={() => setRole(null)} />;
}
 