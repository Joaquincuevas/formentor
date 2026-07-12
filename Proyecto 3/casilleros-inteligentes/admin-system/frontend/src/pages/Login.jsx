import { useEffect, useRef, useState } from "react";
import api from "../api.js";

// Login con Google. Si el backend tiene configurado un Client ID (GET /auth/config/),
// se muestra el boton real de Google Identity Services y se envia el id_token
// (credential) al backend para verificarlo. Si no, se cae al modo desarrollo por email.
export default function Login({ onLogin }) {
  const [cfg, setCfg] = useState(null); // {google_client_id, dev_login}
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const btnRef = useRef(null);

  // 1. saber como mostrar el login
  useEffect(() => {
    api.get("/auth/config/")
      .then(({ data }) => setCfg(data))
      .catch(() => setCfg({ google_client_id: "", dev_login: true }));
  }, []);

  // envia el id_token de Google al backend
  const onGoogleCredential = async (response) => {
    setError("");
    try {
      const { data } = await api.post("/auth/google/", {
        credential: response.credential,
      });
      onLogin(data.token, data.user);
    } catch (err) {
      setError(err?.response?.data?.detail || "No se pudo iniciar sesion con Google");
    }
  };

  // 2. cargar Google Identity Services y renderizar el boton oficial
  useEffect(() => {
    if (!cfg?.google_client_id) return;
    const init = () => {
      if (!window.google || !btnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: cfg.google_client_id,
        callback: onGoogleCredential,
      });
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: "outline", size: "large", width: 280, text: "continue_with",
      });
    };
    if (window.google) { init(); return; }
    const s = document.createElement("script");
    s.src = "https://accounts.google.com/gsi/client";
    s.async = true;
    s.onload = init;
    document.body.appendChild(s);
  }, [cfg]);

  // login de desarrollo por email (solo si no hay OAuth configurado)
  const submitDev = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/auth/google/", { email });
      onLogin(data.token, data.user);
    } catch (err) {
      setError(err?.response?.data?.detail || "No se pudo iniciar sesion");
    }
  };

  return (
    <div className="login-wrap">
      <div className="card">
        <h2>Casilleros Inteligentes</h2>

        {cfg?.google_client_id ? (
          <>
            <p style={{ color: "var(--muted)" }}>
              Inicia sesion con tu cuenta de Google.
            </p>
            <div ref={btnRef} style={{ display: "flex", justifyContent: "center" }} />
          </>
        ) : cfg ? (
          <>
            <p style={{ color: "var(--muted)" }}>
              Inicia sesion con tu cuenta de Google (modo desarrollo: ingresa el email).
            </p>
            <form onSubmit={submitDev}>
              <label>Correo</label>
              <input type="email" value={email} required
                     onChange={(e) => setEmail(e.target.value)}
                     placeholder="tucorreo@uandes.cl" />
              <button className="btn" type="submit" style={{ width: "100%" }}>
                Continuar con Google
              </button>
            </form>
            <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 16 }}>
              Superusuario demo: <b>admin</b> · Usuario demo: <b>demo@uandes.cl</b>
            </p>
          </>
        ) : (
          <p style={{ color: "var(--muted)" }}>Cargando…</p>
        )}

        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      </div>
    </div>
  );
}
