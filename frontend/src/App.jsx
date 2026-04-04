import { useEffect, useMemo, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

async function request(path, options = {}) {
  const token = sessionStorage.getItem("access_token") || "";
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Unexpected error" }));
    throw new Error(payload.detail || "Request failed");
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export default function App() {
  const [tokenInput, setTokenInput] = useState("");
  const [tokenReady, setTokenReady] = useState(Boolean(sessionStorage.getItem("access_token")));
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const canSubmit = useMemo(() => title.trim().length > 0 && description.trim().length > 0, [title, description]);

  async function loadItems() {
    setError("");
    try {
      const data = await request("/api/items");
      setItems(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    if (tokenReady) {
      loadItems();
    }
  }, [tokenReady]);

  async function onLogin(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await request("/api/login", {
        method: "POST",
        body: JSON.stringify({ token: tokenInput.trim() })
      });
      sessionStorage.setItem("access_token", data.access_token);
      setTokenReady(true);
      setTokenInput("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onCreate(e) {
    e.preventDefault();
    if (!canSubmit) {
      return;
    }

    setBusy(true);
    setError("");
    try {
      await request("/api/items", {
        method: "POST",
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim()
        })
      });
      setTitle("");
      setDescription("");
      await loadItems();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(itemId) {
    setBusy(true);
    setError("");
    try {
      await request(`/api/items/${itemId}`, { method: "DELETE" });
      await loadItems();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function onLogout() {
    sessionStorage.removeItem("access_token");
    setTokenReady(false);
    setItems([]);
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Secure CRUD Demo</h1>
        <p>This starter intentionally prioritizes secure defaults and explicit auth.</p>

        {!tokenReady ? (
          <form className="stack" onSubmit={onLogin}>
            <label htmlFor="token">API token</label>
            <input
              id="token"
              type="password"
              autoComplete="off"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              minLength={16}
              required
            />
            <button disabled={busy} type="submit">
              {busy ? "Checking..." : "Login"}
            </button>
          </form>
        ) : (
          <>
            <div className="row">
              <strong>Authenticated</strong>
              <button className="ghost" onClick={onLogout} type="button">Logout</button>
            </div>

            <form className="stack" onSubmit={onCreate}>
              <label htmlFor="title">Title</label>
              <input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={120}
                required
              />

              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={2000}
                rows={5}
                required
              />

              <button disabled={busy || !canSubmit} type="submit">
                {busy ? "Saving..." : "Create Item"}
              </button>
            </form>

            <ul className="stack list">
              {items.map((item) => (
                <li key={item.id}>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                  <button className="danger" disabled={busy} onClick={() => onDelete(item.id)} type="button">
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        {error && <p className="error">{error}</p>}
      </section>
    </main>
  );
}
