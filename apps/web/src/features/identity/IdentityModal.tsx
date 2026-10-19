import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { LogIn, LogOut, ShieldCheck, UserCheck, X } from 'lucide-react';
import {
  claimIdentity,
  getCurrentIdentity,
  getSavedSessionToken,
  loginIdentity,
  logoutIdentity,
  migrateAnalyses,
} from '../../lib/api/intake';
import './identity.css';

interface IdentityModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function IdentityModal({ isOpen, onClose }: IdentityModalProps) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<'claim' | 'login'>('claim');
  const [username, setUsername] = useState('');
  const [secret, setSecret] = useState('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const identityQuery = useQuery({
    queryKey: ['current-identity'],
    queryFn: ({ signal }) => getCurrentIdentity(signal),
    retry: false,
  });

  const claimMutation = useMutation({
    mutationFn: () => claimIdentity(username, secret),
    onSuccess: () => {
      setStatusMessage('Account claimed successfully.');
      queryClient.invalidateQueries({ queryKey: ['current-identity'] });
      queryClient.invalidateQueries({ queryKey: ['private-activity'] });
      setUsername('');
      setSecret('');
    },
    onError: (err: Error) => {
      setStatusMessage(`Claim failed: ${err.message}`);
    },
  });

  const loginMutation = useMutation({
    mutationFn: async () => {
      const priorToken = getSavedSessionToken();
      await loginIdentity(username, secret);
      if (priorToken) {
        try {
          await migrateAnalyses(priorToken);
        } catch {
          /* optional migration */
        }
      }
    },
    onSuccess: () => {
      setStatusMessage('Signed in successfully.');
      queryClient.invalidateQueries({ queryKey: ['current-identity'] });
      queryClient.invalidateQueries({ queryKey: ['private-activity'] });
      setUsername('');
      setSecret('');
      onClose();
    },
    onError: (err: Error) => {
      setStatusMessage(`Sign in failed: ${err.message}`);
    },
  });

  if (!isOpen || typeof document === 'undefined') return null;

  const current = identityQuery.data;

  return createPortal(
    <div
      className="identity-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="identity-modal-title"
      onClick={e => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="identity-modal-card" onClick={e => e.stopPropagation()}>
        <div className="identity-modal-header">
          <div className="identity-modal-title-row">
            <UserCheck size={20} className="identity-icon" />
            <h2 id="identity-modal-title">
              {current?.bound ? `Account: ${current.username}` : 'Sign In / Sign Up (Optional)'}
            </h2>
          </div>
          <button
            type="button"
            className="identity-close-btn"
            onClick={onClose}
            aria-label="Close identity dialog"
          >
            <X size={16} />
          </button>
        </div>

        {current?.bound ? (
          <div className="identity-signed-in-view">
            <p className="identity-status-note">
              <ShieldCheck size={16} />
              You are signed in as <strong>{current.username}</strong>. Your legal matters and review history are saved to this identity.
            </p>
            <div className="identity-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  logoutIdentity();
                  queryClient.invalidateQueries({ queryKey: ['current-identity'] });
                  queryClient.invalidateQueries({ queryKey: ['private-activity'] });
                  onClose();
                }}
              >
                <LogOut size={14} />
                Sign Out (Return to Guest Session)
              </button>
            </div>
          </div>
        ) : (
          <div className="identity-form-container">
            <div className="identity-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'claim'}
                className={`identity-tab-btn ${mode === 'claim' ? 'active' : ''}`}
                onClick={() => {
                  setMode('claim');
                  setStatusMessage(null);
                }}
              >
                Sign Up / Claim
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'login'}
                className={`identity-tab-btn ${mode === 'login' ? 'active' : ''}`}
                onClick={() => {
                  setMode('login');
                  setStatusMessage(null);
                }}
              >
                Sign In
              </button>
            </div>

            <p className="identity-description">
              {mode === 'claim'
                ? 'Accounts are completely optional. FilingGuard works 100% as an anonymous guest. If you want to save and access your matters across sessions and devices, choose a username and passphrase.'
                : 'Sign in to access your previously saved legal matters, filings, and reviewer history.'}
            </p>

            <form
              className="identity-form"
              onSubmit={e => {
                e.preventDefault();
                if (mode === 'claim') claimMutation.mutate();
                else loginMutation.mutate();
              }}
            >
              <label className="identity-input-label">
                <span>Username</span>
                <input
                  type="text"
                  required
                  minLength={3}
                  maxLength={64}
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="e.g. jdoe_esq"
                  autoComplete="username"
                />
              </label>

              <label className="identity-input-label">
                <span>Passphrase (Secret)</span>
                <input
                  type="password"
                  required
                  minLength={12}
                  value={secret}
                  onChange={e => setSecret(e.target.value)}
                  placeholder="At least 12 characters"
                  autoComplete={mode === 'claim' ? 'new-password' : 'current-password'}
                />
              </label>

              {statusMessage && (
                <p className="identity-status-message" role="status" aria-live="polite">
                  {statusMessage}
                </p>
              )}

              <div className="identity-form-actions">
                <button
                  type="submit"
                  className="primary-button"
                  disabled={claimMutation.isPending || loginMutation.isPending}
                >
                  <LogIn size={14} />
                  {mode === 'claim' ? 'Create Account' : 'Sign In'}
                </button>
                <button type="button" className="secondary-button" onClick={onClose}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}
