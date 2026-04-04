import { useEffect, useMemo, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");

const STORAGE_KEY = "access_token";
const STORAGE_TYPE = localStorage;

async function request(path, options = {}) {
  const token = STORAGE_TYPE.getItem(STORAGE_KEY) || "";
  
  const headers = {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include"
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
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [tokenReady, setTokenReady] = useState(Boolean(STORAGE_TYPE.getItem(STORAGE_KEY)));
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const canSubmit = title.length > 0 && description.length > 0;

  async function loadItems() {
    setError("");
    try {
      const data = await request("/api/items");
      if (data.items) {
        setItems(data.items);
      } else {
        setItems(data);
      }
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
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      STORAGE_TYPE.setItem(STORAGE_KEY, data.access_token);
      setTokenReady(true);
      setUsernameInput("");
      setPasswordInput("");
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
      const data = await request("/api/items", {
        method: "POST",
        body: JSON.stringify({
          title: title,
          description: description,
          user_id: 1
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
    STORAGE_TYPE.removeItem(STORAGE_KEY);
    setTokenReady(false);
    setItems([]);
  }

  return (
    <main className="page">
      <section className="card">
        <h1>CRUD Application</h1>

        {!tokenReady ? (
          <form className="stack" onSubmit={onLogin}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              autoComplete="off"
              value={usernameInput}
              onChange={(e) => setUsernameInput(e.target.value)}
              placeholder="Enter username"
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="off"
              value={passwordInput}
              onChange={(e) => setPasswordInput(e.target.value)}
              placeholder="Enter password"
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
                placeholder="Enter title"
              />

              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter description"
                rows={5}
              />

              <button disabled={busy || !canSubmit} type="submit">
                {busy ? "Saving..." : "Create Item"}
              </button>
            </form>

            <h3>Items:</h3>
            <ul className="stack list">
              {items && items.length > 0 ? (
                items.map((item) => (
                  <li key={item.id}>
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                    {item.password && (
                      <p>Password: {item.password}</p>
                    )}
                    <button className="danger" disabled={busy} onClick={() => onDelete(item.id)} type="button">
                      Delete
                    </button>
                  </li>
                ))
              ) : (
                <p>No items</p>
              )}
            </ul>
          </>
        )}

        {error && (
          <div className="error">
            <p><strong>Error:</strong> {error}</p>
          </div>
        )}
      </section>
    </main>
  );
}
