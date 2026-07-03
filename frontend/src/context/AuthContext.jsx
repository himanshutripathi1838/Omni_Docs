import { createContext, useContext, useMemo, useState } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("omnidocs_user");
    return stored ? JSON.parse(stored) : null;
  });

  const value = useMemo(
    () => ({
      user,
      setUser: (nextUser) => {
        setUser(nextUser);
        if (nextUser) localStorage.setItem("omnidocs_user", JSON.stringify(nextUser));
        else localStorage.removeItem("omnidocs_user");
      },
    }),
    [user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
