import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Clock, MessageSquare, Send, ShieldAlert, UserCheck, XCircle } from 'lucide-react';
import {
  addFindingComment,
  listFindingComments,
  setFindingDisposition,
  type FindingComment,
} from '../../lib/api/intake';
import type { ResultFinding } from '../../lib/api/results';
import './collaboration.css';

const ROLES = [
  { id: 'lead_attorney', label: 'Lead Attorney' },
  { id: 'associate_reviewer', label: 'Associate Reviewer' },
  { id: 'paralegal', label: 'Paralegal' },
  { id: 'court_clerk', label: 'Court Clerk' },
  { id: 'auditor', label: 'Compliance Auditor' },
] as const;

interface FindingCollaborationProps {
  analysisId: string;
  finding: ResultFinding;
}

export function FindingCollaboration({ analysisId, finding }: FindingCollaborationProps) {
  const queryClient = useQueryClient();
  const [showSignoffModal, setShowSignoffModal] = useState(false);
  const [dispositionStatus, setDispositionStatus] = useState<'accepted' | 'dismissed' | 'needs_review'>('accepted');
  const [reviewerName, setReviewerName] = useState('');
  const [reviewerRole, setReviewerRole] = useState<string>('lead_attorney');
  const [rationale, setRationale] = useState('');
  const [dispositionError, setDispositionError] = useState<string | null>(null);

  // Comment form state
  const [commentAuthor, setCommentAuthor] = useState('');
  const [commentRole, setCommentRole] = useState<string>('associate_reviewer');
  const [commentContent, setCommentContent] = useState('');
  const [commentError, setCommentError] = useState<string | null>(null);

  const commentsQuery = useQuery({
    queryKey: ['finding-comments', analysisId, finding.id],
    queryFn: ({ signal }) => listFindingComments(analysisId, finding.id, signal),
    retry: false,
  });

  const dispositionMutation = useMutation({
    mutationFn: () =>
      setFindingDisposition(
        analysisId,
        finding.id,
        dispositionStatus,
        rationale,
        reviewerName,
        reviewerRole,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-results', analysisId] });
      setShowSignoffModal(false);
      setRationale('');
      setDispositionError(null);
    },
    onError: (err: Error) => {
      setDispositionError(`Sign-off failed: ${err.message}`);
    },
  });

  const commentMutation = useMutation({
    mutationFn: () =>
      addFindingComment(
        analysisId,
        finding.id,
        commentAuthor,
        commentRole,
        commentContent,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finding-comments', analysisId, finding.id] });
      setCommentContent('');
      setCommentError(null);
    },
    onError: (err: Error) => {
      setCommentError(`Failed to post comment: ${err.message}`);
    },
  });

  const comments: FindingComment[] = commentsQuery.data ?? [];
  const meta = (finding as { disposition_metadata?: Record<string, unknown> }).disposition_metadata;
  const currentStatus: string = (meta?.status as string) || finding.status || 'open';

  return (
    <section className="finding-collaboration" aria-labelledby="collaboration-title">
      <div className="collab-header">
        <div className="collab-status-display">
          <h3 id="collaboration-title">Review Sign-Off & Discussion</h3>
          <span className={`collab-status-pill status-${currentStatus}`}>
            {currentStatus === 'accepted' && <CheckCircle2 size={13} />}
            {currentStatus === 'dismissed' && <XCircle size={13} />}
            {currentStatus === 'needs_review' && <ShieldAlert size={13} />}
            {currentStatus === 'open' && <Clock size={13} />}
            <span>Status: {currentStatus.replaceAll('_', ' ')}</span>
          </span>
        </div>
        <button
          type="button"
          className="collab-signoff-btn"
          onClick={() => setShowSignoffModal(true)}
          aria-label="Record reviewer sign-off"
        >
          <UserCheck size={14} />
          Record Sign-Off
        </button>
      </div>

      {meta && typeof meta.reviewer_name === 'string' && (
        <div className="collab-audit-card">
          <div className="collab-audit-header">
            <strong>{meta.reviewer_name}</strong>
            <span className="collab-role-tag">{String(meta.reviewer_role ?? '').replaceAll('_', ' ')}</span>
            <small>{meta.signed_at ? new Date(String(meta.signed_at)).toLocaleString() : ''}</small>
          </div>
          {typeof meta.rationale === 'string' && <p className="collab-audit-rationale">{meta.rationale}</p>}
        </div>
      )}

      {showSignoffModal && (
        <div className="collab-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="signoff-modal-title">
          <div className="collab-modal-card">
            <h4 id="signoff-modal-title">Record Reviewer Sign-Off</h4>
            <p className="collab-modal-desc">
              Record a formal review disposition for this finding with auditable attribution.
            </p>

            <form
              onSubmit={e => {
                e.preventDefault();
                dispositionMutation.mutate();
              }}
            >
              <label className="collab-input-label">
                <span>Disposition Status</span>
                <select
                  value={dispositionStatus}
                  onChange={e => setDispositionStatus(e.target.value as 'accepted' | 'dismissed' | 'needs_review')}
                >
                  <option value="accepted">Accepted (Risk acknowledged / resolved)</option>
                  <option value="dismissed">Dismissed (Non-material / false positive)</option>
                  <option value="needs_review">Needs Review (Escalate to senior counsel)</option>
                </select>
              </label>

              <div className="collab-input-row">
                <label className="collab-input-label">
                  <span>Reviewer Name *</span>
                  <input
                    type="text"
                    required
                    maxLength={64}
                    value={reviewerName}
                    onChange={e => setReviewerName(e.target.value)}
                    placeholder="e.g. Sarah Jenkins"
                  />
                </label>

                <label className="collab-input-label">
                  <span>Reviewer Role</span>
                  <select value={reviewerRole} onChange={e => setReviewerRole(e.target.value)}>
                    {ROLES.map(r => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="collab-input-label">
                <span>Rationale & Assessment *</span>
                <textarea
                  required
                  rows={3}
                  maxLength={1000}
                  value={rationale}
                  onChange={e => setRationale(e.target.value)}
                  placeholder="Explain why this finding is accepted, dismissed, or flagged for further review..."
                />
              </label>

              {dispositionError && <p className="collab-error-note" role="alert">{dispositionError}</p>}

              <div className="collab-modal-actions">
                <button
                  type="submit"
                  className="primary-button"
                  disabled={dispositionMutation.isPending || !reviewerName.trim() || !rationale.trim()}
                >
                  Confirm Sign-Off
                </button>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowSignoffModal(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Discussion Thread */}
      <div className="collab-thread">
        <div className="collab-thread-heading">
          <MessageSquare size={15} />
          <h4>Comments ({comments.length})</h4>
        </div>

        {comments.length > 0 ? (
          <ul className="collab-comment-list">
            {comments.map(c => (
              <li key={c.id} className="collab-comment-item">
                <div className="collab-comment-header">
                  <strong>{c.author_name}</strong>
                  <span className="collab-role-tag">{c.author_role.replaceAll('_', ' ')}</span>
                  <small>{new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                </div>
                <p className="collab-comment-text">{c.content}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="collab-no-comments">No reviewer comments yet. Add the first note below.</p>
        )}

        {/* Comment Composer */}
        <form
          className="collab-composer"
          onSubmit={e => {
            e.preventDefault();
            commentMutation.mutate();
          }}
        >
          <div className="collab-composer-inputs">
            <input
              type="text"
              required
              maxLength={64}
              value={commentAuthor}
              onChange={e => setCommentAuthor(e.target.value)}
              placeholder="Your name"
              aria-label="Author name"
              className="collab-name-input"
            />
            <select
              value={commentRole}
              onChange={e => setCommentRole(e.target.value)}
              aria-label="Author role"
              className="collab-role-select"
            >
              {ROLES.map(r => (
                <option key={r.id} value={r.id}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div className="collab-composer-text-row">
            <input
              type="text"
              required
              maxLength={2000}
              value={commentContent}
              onChange={e => setCommentContent(e.target.value)}
              placeholder="Add a comment or verification note..."
              aria-label="Comment content"
              className="collab-content-input"
            />
            <button
              type="submit"
              className="collab-send-btn"
              disabled={commentMutation.isPending || !commentAuthor.trim() || !commentContent.trim()}
              aria-label="Send comment"
            >
              <Send size={14} />
            </button>
          </div>
          {commentError && <p className="collab-error-note" role="alert">{commentError}</p>}
        </form>
      </div>
    </section>
  );
}
