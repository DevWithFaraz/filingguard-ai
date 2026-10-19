import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, User } from 'lucide-react';
import { getCurrentIdentity } from '../../lib/api/intake';
import { IdentityModal } from './IdentityModal';
import './identity.css';

export function IdentityBadge() {
  const [modalOpen, setModalOpen] = useState(false);

  const query = useQuery({
    queryKey: ['current-identity'],
    queryFn: ({ signal }) => getCurrentIdentity(signal),
    retry: false,
    staleTime: 60000,
  });

  const identity = query.data;

  return (
    <>
      <button
        type="button"
        className={`identity-badge-btn ${identity?.bound ? 'claimed' : 'guest'}`}
        onClick={() => setModalOpen(true)}
        aria-label={identity?.bound ? `Signed in as ${identity.username}` : 'Guest session. Click to claim or sign in.'}
        title={identity?.bound ? `Reviewer: ${identity.username}` : 'Guest Session (Temporary)'}
      >
        {identity?.bound ? <Shield size={14} className="badge-icon" /> : <User size={14} className="badge-icon" />}
        <span className="badge-label">{identity?.bound ? identity.username : 'Guest'}</span>
      </button>

      <IdentityModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
