import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PencilLine } from 'lucide-react';
import { useId, useState } from 'react';
import {
  submitClaimCorrection,
  type ResultClaim,
} from '../../lib/api/results';
import './claim-correction.css';

interface ClaimCorrectionFormProps {
  analysisId: string;
  claim: ResultClaim;
}

export function ClaimCorrectionForm({ analysisId, claim }: ClaimCorrectionFormProps) {
  const queryClient = useQueryClient();
  const fieldId = useId();
  const historyId = useId();
  const [draft, setDraft] = useState(claim.corrected_text ?? claim.text);
  const mutation = useMutation({
    mutationFn: (correctedText: string) => submitClaimCorrection(analysisId, claim.id, correctedText),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['review-results', analysisId] });
    },
  });
  const history = claim.correction_history ?? [];
  const corrected = Boolean(claim.corrected_text);
  const submit = () => {
    const value = draft.trim();
    if (!value || mutation.isPending) return;
    mutation.mutate(value);
  };

  return (
    <div className="claim-correction">
      <p>
        <span className="claim-correction-label">Original extraction</span>
        {claim.text}
      </p>
      {corrected && (
        <p>
          <span className="claim-correction-label">User-corrected extraction</span>
          {claim.corrected_text}
        </p>
      )}
      {claim.propositions_stale && (
        <p className="claim-correction-stale" role="status">
          Proposition support is stale after this correction. Full re-run clones a new
          analysis and re-extracts claims without the correction.
        </p>
      )}
      <div className="claim-correction-form">
        <label htmlFor={fieldId}>Correct extracted claim</label>
        <textarea
          id={fieldId}
          value={draft}
          onChange={event => setDraft(event.target.value)}
          onKeyDown={event => {
            if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              submit();
            }
          }}
          maxLength={8000}
          rows={3}
          disabled={mutation.isPending}
        />
        <button
          type="button"
          className="secondary-button"
          onClick={submit}
          disabled={mutation.isPending || !draft.trim()}
        >
          <PencilLine size={16} />
          Save correction
        </button>
      </div>
      {mutation.isError && <p role="alert">Correction could not be saved for this session.</p>}
      {history.length > 0 && (
        <div>
          <h3 id={historyId}>Correction history</h3>
          <ol className="claim-correction-history" aria-labelledby={historyId}>
            {history.map(entry => (
              <li key={entry.id}>
                <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time>
                <span className="claim-correction-label">User-corrected extraction</span>
                {entry.corrected_text}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
