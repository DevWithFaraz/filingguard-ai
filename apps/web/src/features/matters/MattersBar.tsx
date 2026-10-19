import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Briefcase, FolderPlus, Plus, X } from 'lucide-react';
import { createMatter, listMatters, type MatterSummary } from '../../lib/api/intake';
import './matters.css';

interface MattersBarProps {
  selectedMatterId: string | null;
  onSelectMatter: (matterId: string | null) => void;
}

export function MattersBar({ selectedMatterId, onSelectMatter }: MattersBarProps) {
  const queryClient = useQueryClient();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [caseNumber, setCaseNumber] = useState('');
  const [clientId, setClientId] = useState('');
  const [description, setDescription] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ['matters-list'],
    queryFn: ({ signal }) => listMatters(signal),
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: () => createMatter(name, caseNumber, clientId, description),
    onSuccess: (newMatter: MatterSummary) => {
      queryClient.invalidateQueries({ queryKey: ['matters-list'] });
      setCreateModalOpen(false);
      setName('');
      setCaseNumber('');
      setClientId('');
      setDescription('');
      setErrorMessage(null);
      onSelectMatter(newMatter.id);
    },
    onError: (err: Error) => {
      setErrorMessage(`Failed to create matter: ${err.message}`);
    },
  });

  const matters = query.data ?? [];

  return (
    <div className="matters-bar-container">
      <div className="matters-bar-header">
        <div className="matters-bar-title">
          <Briefcase size={16} />
          <span>Matters & Workspaces</span>
        </div>
        <button
          type="button"
          className="matters-new-btn"
          onClick={() => setCreateModalOpen(true)}
          aria-label="Create new matter"
        >
          <Plus size={14} />
          New Matter
        </button>
      </div>

      <div className="matters-pill-list" role="tablist" aria-label="Filter documents by matter">
        <button
          type="button"
          role="tab"
          aria-selected={selectedMatterId === null}
          className={`matter-pill ${selectedMatterId === null ? 'active' : ''}`}
          onClick={() => onSelectMatter(null)}
        >
          All Filings
        </button>

        {matters.map(m => (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={selectedMatterId === m.id}
            className={`matter-pill ${selectedMatterId === m.id ? 'active' : ''}`}
            onClick={() => onSelectMatter(m.id)}
            title={m.case_number ? `Case: ${m.case_number}` : undefined}
          >
            {m.name}
            {m.case_number && <span className="matter-pill-case">({m.case_number})</span>}
          </button>
        ))}
      </div>

      {createModalOpen && (
        <div className="matter-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="create-matter-title">
          <div className="matter-modal-card">
            <div className="matter-modal-header">
              <div className="matter-modal-title">
                <FolderPlus size={18} />
                <h3 id="create-matter-title">Create Legal Matter</h3>
              </div>
              <button
                type="button"
                className="matter-close-btn"
                onClick={() => setCreateModalOpen(false)}
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            <form
              className="matter-form"
              onSubmit={e => {
                e.preventDefault();
                createMutation.mutate();
              }}
            >
              <label className="matter-input-label">
                <span>Matter Name *</span>
                <input
                  type="text"
                  required
                  maxLength={255}
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. Acme Corp v. Beta Ltd"
                />
              </label>

              <div className="matter-input-row">
                <label className="matter-input-label">
                  <span>Case Number</span>
                  <input
                    type="text"
                    maxLength={100}
                    value={caseNumber}
                    onChange={e => setCaseNumber(e.target.value)}
                    placeholder="e.g. 3:24-cv-01234"
                  />
                </label>

                <label className="matter-input-label">
                  <span>Client ID</span>
                  <input
                    type="text"
                    maxLength={100}
                    value={clientId}
                    onChange={e => setClientId(e.target.value)}
                    placeholder="e.g. CLI-9921"
                  />
                </label>
              </div>

              <label className="matter-input-label">
                <span>Description / Scope</span>
                <textarea
                  maxLength={1000}
                  rows={3}
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="Summary of matter context or relevant court standing orders..."
                />
              </label>

              {errorMessage && <p className="matter-error-note" role="alert">{errorMessage}</p>}

              <div className="matter-form-actions">
                <button
                  type="submit"
                  className="primary-button"
                  disabled={createMutation.isPending || !name.trim()}
                >
                  Create Matter
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setCreateModalOpen(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
