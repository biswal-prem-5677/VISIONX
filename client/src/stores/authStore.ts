/**
 * VisionX — Auth Store
 * Authentication state: user session, tokens, role
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'viewer' | 'operator' | 'admin' | 'superadmin';

interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  plan: 'free' | 'pro' | 'enterprise';
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: (user, token) => set({
        user, token, isAuthenticated: true, isLoading: false,
      }),

      logout: () => set({
        user: null, token: null, isAuthenticated: false,
      }),

      updateUser: (updates) => set((s) => ({
        user: s.user ? { ...s.user, ...updates } : null,
      })),

      setLoading: (isLoading) => set({ isLoading }),
    }),
    { name: 'vx-auth' }
  )
);
