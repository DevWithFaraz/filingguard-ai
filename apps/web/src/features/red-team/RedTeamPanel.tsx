import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  Crosshair,
  Gavel,
  RotateCw,
  Sparkles,
} from 'lucide-react';
import { useState } from 'react';
import { getRedTeam, runRedTeam, type RedTeamResponse } from '../../lib/api/results';
import './red-team.css';

interface RedTeamPanelProps {
  analysisId: string;
  onSelectFinding: (findingId: string) => void;
}

function label(value: string) {
  return value.replaceAll('_', ' ');
}

export function RedTeamPanel({ analysisId, onSelectFinding }: RedTeamPanelProps) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['red-team', analysisId],
    queryFn: ({ signal }) => getRedTeam(analysisId, signal),
    retry: false,
    gcTime: 0,
  });

  const mutation = useMutation({
    mutationFn: () => runRedTeam(analysisId),
    onSuccess: (data) => {
      queryClient.setQueryData(['red-team', analysisId], data);
    },
  });

  const data: RedTeamResponse | undefined = query.data;

  const [userToggled, setUserToggled] = useState<Record<string, boolean>>({});

  const isCardExpanded = (id: string, index: number) => {
    if (id in userToggled) {
      return userToggled[id] === true;
    }
    return index === 0;
  };

  const toggleExpand = (id: string, index: number) => {
    const current = isCardExpanded(id, index);
    setUserToggled(prev => ({ ...prev, [id]: !current }));
  };

  return (
    <section id="result-red-team" className="red-team-section" aria-labelledby="red-team-title">
      <div className="red-team-header">
        <div className="red-team-title-group">
          <div className="red-team-kicker-row">
            <span className="red-team-kicker-pill">
              <Crosshair size={13} className="red-team-kicker-icon" />
              Adversarial Stress-Test
            </span>
          </div>
          <h2 id="red-team-title">Legal Red-Team Mode</h2>
          <p className="red-team-subtitle">
            Anticipate how opposing counsel or a skeptical court will challenge this filing.
            Synthesized exclusively from verified findings and evidence.
          </p>
        </div>

        <div className="red-team-actions">
          <button
            type="button"
            className="red-team-refresh-btn"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || query.isPending}
            aria-label="Re-run red team analysis"
          >
            <RotateCw size={14} className={mutation.isPending ? 'spin' : ''} />
            {mutation.isPending ? 'Analyzing challenges…' : 'Re-run Red Team'}
          </button>
        </div>
      </div>

      <div className="red-team-disclaimer" role="note">
        <span className="disclaimer-icon-pill" aria-hidden="true">
          <Gavel size={14} />
        </span>
        <div className="disclaimer-text">
          <strong>Strict Review Boundary:</strong> {data?.limitation ?? (
            'Red-Team Mode synthesizes review vulnerabilities exclusively from existing findings and evidence. ' +
            'It identifies adversarial risks to assist human review, not legal strategy or legal advice.'
          )}
        </div>
      </div>

      {query.isPending && (
        <p className="workflow-notice" role="status" aria-live="polite">
          Loading adversarial review critiques…
        </p>
      )}

      {mutation.isPending && (
        <p className="workflow-notice" role="status" aria-live="polite">
          Analyzing adversarial challenges…
        </p>
      )}

      {query.isError && (
        <div className="workflow-notice error" role="alert">
          Red-team critiques currently unavailable.
          <button
            type="button"
            className="secondary-button"
            onClick={() => void query.refetch()}
            style={{ marginLeft: '1rem' }}
          >
            Retry
          </button>
        </div>
      )}

      {data && (
        <div className="red-team-content">
          <div className="red-team-summary-banner" role="status" aria-live="polite">
            <div className="red-team-metric-group">
              <div className="red-team-metric critical" title="Critical vulnerabilities">
                <span className="metric-count-circle">{data.critical_count}</span>
                <span className="metric-label">Critical</span>
              </div>
              <div className="red-team-metric high" title="High vulnerabilities">
                <span className="metric-count-circle">{data.high_count}</span>
                <span className="metric-label">High</span>
              </div>
              <div className="red-team-metric medium" title="Medium vulnerabilities">
                <span className="metric-count-circle">{data.medium_count}</span>
                <span className="metric-label">Medium</span>
              </div>
              <div className="red-team-metric low" title="Low vulnerabilities">
                <span className="metric-count-circle">{data.low_count}</span>
                <span className="metric-label">Low</span>
              </div>
            </div>
            <p className="red-team-summary-text">{data.summary}</p>
          </div>

          {data.weaknesses.length === 0 ? (
            <div className="red-team-clean-card">
              <div className="clean-icon-pill">
                <CheckCircle2 size={24} className="clean-icon" />
              </div>
              <h3>No High-Risk Vulnerabilities Detected</h3>
              <p>
                No critical precedent misrepresentations, non-existent citations, unredacted PII,
                or procedural defects were detected in evaluated checks.
              </p>
            </div>
          ) : (
            <ul className="red-team-weakness-list" aria-label="Ranked filing vulnerabilities">
              {data.weaknesses.map((weakness, index) => {
                const isExpanded = isCardExpanded(weakness.id, index);
                return (
                  <li key={weakness.id} className={`red-team-card severity-${weakness.severity}`}>
                    <div className="red-team-card-header">
                      <div className="red-team-card-badge-row">
                        <span className={`result-badge severity-${weakness.severity}`}>
                          {weakness.severity}
                        </span>
                        <span className="vulnerability-type-label">
                          {label(weakness.vulnerability_type)}
                        </span>
                      </div>

                      <button
                        type="button"
                        className="red-team-expand-toggle"
                        onClick={() => toggleExpand(weakness.id, index)}
                        aria-expanded={isExpanded}
                        aria-controls={`weakness-detail-${weakness.id}`}
                      >
                        <h3 className="red-team-weakness-title">{weakness.title}</h3>
                        <span
                          className={`red-team-toggle-icon ${isExpanded ? 'is-expanded' : ''}`}
                          aria-hidden="true"
                        >
                          <ChevronDown size={17} />
                        </span>
                      </button>
                    </div>

                    {isExpanded && (
                      <div
                        id={`weakness-detail-${weakness.id}`}
                        className="red-team-card-body"
                      >
                        <div className="challenge-theory-block">
                          <h4>
                            <Gavel size={15} />
                            Adversarial Challenge Theory
                          </h4>
                          <p>{weakness.challenge_theory}</p>
                        </div>

                        <div className="impact-block">
                          <h4>
                            <AlertCircle size={14} />
                            Procedural & Legal Impact
                          </h4>
                          <p>{weakness.impact_summary}</p>
                        </div>

                        <div className="remediation-block">
                          <h4>
                            <Sparkles size={14} />
                            Recommended Pre-Filing Review
                          </h4>
                          <p>{weakness.remediation_recommendation}</p>
                        </div>

                        {weakness.linked_finding_ids.length > 0 && (
                          <div className="linked-findings-actions">
                            <span className="linked-label">Substantiating Evidence:</span>
                            {weakness.linked_finding_ids.map(fId => (
                              <button
                                key={fId}
                                type="button"
                                className="linked-finding-jump"
                                onClick={() => onSelectFinding(fId)}
                              >
                                Jump to Finding
                                <ArrowRight size={13} />
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
