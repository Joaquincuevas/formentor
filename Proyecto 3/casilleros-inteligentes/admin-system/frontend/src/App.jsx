import { useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import UserDashboard from "./pages/UserDashboard.jsx";
import SuperDashboard from "./pages/SuperDashboard.jsx";
import Controllers from "./pages/Controllers.jsx";
import Models from "./pages/Models.jsx";

function readUser() {
  try { return JSON.parse(localStorage.getItem("user")); }
  catch { return null; }
}

export default function App() {
  const [user, setUser] = useState(readUser());
  const navigate = useNavigate();

  const login = (token, u) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(u));
    setUser(u);
    navigate("/");
  };
  const logout = () => {
    localStorage.clear();
    setUser(null);
    navigate("/login");
  };

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={login} />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    );
  }

  return (
    <>
      <header className="topbar">
        <span className="brand">
          <span className="brand-mark">◩</span>
          Casilleros
        </span>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/controllers">Controladores</NavLink>
          {user.is_superuser && <NavLink to="/models">Modelos</NavLink>}
        </nav>
        <span className="user-area">
          <span className="user-email">{user.username}</span>
          <button className="btn secondary" onClick={logout}>Salir</button>
        </span>
      </header>
      <Routes>
        <Route
          path="/"
          element={user.is_superuser ? <SuperDashboard /> : <UserDashboard />}
        />
        <Route path="/controllers" element={<Controllers />} />
        {user.is_superuser && <Route path="/models" element={<Models />} />}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}
