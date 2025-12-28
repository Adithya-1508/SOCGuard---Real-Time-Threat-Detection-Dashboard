import { createContext, useState, useContext, useEffect } from "react";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem("token"));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            setLoading(true);
            // Verify token and get user details
            fetch("http://localhost:8000/auth/me", {
                headers: { Authorization: `Bearer ${token}` },
            })
                .then((res) => {
                    if (res.ok) return res.json();
                    throw new Error("Invalid token");
                })
                .then((data) => setUser(data))
                .catch(() => {
                    logout();
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, [token]);

    const login = async (email, password) => {
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);

        const res = await fetch("http://localhost:8000/auth/token", {
            method: "POST",
            body: formData,
        });

        if (!res.ok) throw new Error("Login failed");

        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);
    };

    const logout = () => {
        localStorage.removeItem("token");
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, setToken, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
