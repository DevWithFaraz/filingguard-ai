import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, Briefcase, Clock3, FileText, RefreshCw } from 'lucide-react';
import { Link } from 'react-router';
import { assignMatter, getActivity, getCapabilities, listMatters } from '../../lib/api/intake';
import { StartReviewLink, WorkflowHero } from '../../components/layout/WorkflowShell';
import { MattersBar } from '../matters/MattersBar';

export function ActivityView() {
  const queryClient = useQueryClient();
  const [selectedMatterId, setSelectedMatterId] = useState<string | null>(null);

  const capabilities = useQuery({
    queryKey: ['capabilities'],
    queryFn: ({ signal }) => getCapabilities(signal),
    retry: false,
  });

  const query = useQuery({
    queryKey: ['private-activity', selectedMatterId],
    queryFn: ({ signal }) => getActivity(signal, selectedMatterId ?? undefined),
    enabled: capabilities.data?.intake_enabled === true,
    retry: false,
    staleTime: 0,
    gcTime: 0,
    refetchInterval: 60000,
  });

  const mattersQuery = useQuery({
    queryKey: ['matters-list'],
    queryFn: ({ signal }) => listMatters(signal),
    retry: false,
  });

  const assignMutation = useMutation({
    mutationFn: ({ mId, aId }: { mId: string; aId: string }) => assignMatter(mId, aId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['private-activity'] });
      queryClient.invalidateQueries({ queryKey: ['matters-list'] });
    },
  });

  const matters = mattersQuery.data ?? [];

  return (
    <section className="workflow-activity">
      <WorkflowHero
        eyebrow="THIS TAB’S DOCUMENTS"
        title="Activity"
        description="Pick up where you left off. Organize filings into client matters, manage review progress, and access saved results."
      >
        <div className="workflow-hero-note">
          <Clock3 size={28} />
          <strong>A secure workspace.</strong>
          <span>Filings are scoped to your authenticated identity or session.</span>
        </div>
      </WorkflowHero>

      <MattersBar
        selectedMatterId={selectedMatterId}
        onSelectMatter={setSelectedMatterId}
      />

      <div className="workflow-list-heading">
        <div>
          <h2>Your documents</h2>
          <p>
            {query.data?.length ?? 0} available{' '}
            {selectedMatterId ? 'in this matter' : 'in this session'}
          </p>
        </div>
        <StartReviewLink />
      </div>

      {capabilities.isError && (
        <div className="workflow-notice" role="alert">
          <p>Session availability could not be confirmed.</p>
          <button className="secondary-button" onClick={() => void capabilities.refetch()}>
            Retry availability
          </button>
        </div>
      )}
      {capabilities.isPending && (
        <p role="status" aria-live="polite">
          Checking private session availability
        </p>
      )}
      {query.isFetching && (
        <p role="status" aria-live="polite">
          Loading private session
        </p>
      )}
      {query.error && (
        <p role="alert">
          {query.error.message}
          <button className="secondary-button" onClick={() => void query.refetch()}>
            Retry
          </button>
        </p>
      )}

      {capabilities.data && (!query.data || !query.data.length) && !query.isFetching && !query.error && (
        <div className="workflow-empty">
          <FileText size={35} />
          <h2>No reviews yet</h2>
          <p>
            {capabilities.data.intake_enabled
              ? selectedMatterId
                ? 'No documents have been assigned to this legal matter yet.'
                : 'Prepare your first document to see it here. Try the synthetic demo to explore the workflow.'
              : 'Document preparation is currently disabled. You can still explore the reviewed sample.'}
          </p>
          <div className="workflow-actions">
            <Link className="secondary-button" to="/demo">
              Explore sample
              <ArrowRight size={16} />
            </Link>
            <Link to="/" className="document-text-link">
              New document
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      )}

      <ul className="activity-list">
        {!query.error &&
          query.data?.map(value => (
            <li key={value.analysis_id}>
              <div className="activity-document-icon">
                <FileText size={22} />
              </div>
              <div className="activity-document-body">
                <Link to={`/analyses/${value.analysis_id}`}>
                  {value.document_name}
                  <ArrowRight size={16} />
                </Link>
                <p>
                  {value.mode === 'demo' ? 'Synthetic demo' : 'Private document'} ·{' '}
                  {value.paragraph_count} paragraphs · Expires{' '}
                  {new Date(value.expires_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
                {matters.length > 0 && (
                  <div className="activity-matter-assign">
                    <Briefcase size={12} />
                    <label className="sr-only" htmlFor={`matter-select-${value.analysis_id}`}>
                      Assign legal matter
                    </label>
                    <select
                      id={`matter-select-${value.analysis_id}`}
                      defaultValue=""
                      onChange={e => {
                        const mId = e.target.value;
                        if (mId) {
                          assignMutation.mutate({ mId, aId: value.analysis_id });
                        }
                      }}
                    >
                      <option value="" disabled>
                        Assign to matter...
                      </option>
                      {matters.map(m => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <span className="workflow-status">
                {value.execution_status === 'not_run'
                  ? 'Prepared · checks not run'
                  : value.execution_status.replaceAll('_', ' ')}
              </span>
            </li>
          ))}
      </ul>

      {!!query.data?.length && (
        <button
          className="document-text-link"
          onClick={() => void query.refetch()}
          disabled={query.isFetching}
        >
          <RefreshCw size={15} />
          Refresh documents
        </button>
      )}
    </section>
  );
}
