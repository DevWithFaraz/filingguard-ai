import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, ArrowRight, CheckCircle2, HelpCircle, MessageSquare, Send } from 'lucide-react';
import {
  askFindingQuestion,
  getFindingQuestions,
  GroundedAnswerResponse,
  ResultFinding,
} from '../../lib/api/results';

interface FindingQAProps {
  analysisId: string;
  finding: ResultFinding;
}

const SUGGESTED_PROMPTS = [
  'Why was this flagged?',
  'What evidence was used?',
  'What source passage supports this?',
];

export function FindingQA({ analysisId, finding }: FindingQAProps) {
  const [questionText, setQuestionText] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const queryKey = ['finding-qa', analysisId, finding.id];

  const { data: history, isLoading } = useQuery({
    queryKey,
    queryFn: ({ signal }) => getFindingQuestions(analysisId, finding.id, signal),
    retry: false,
    gcTime: 0,
  });

  const mutation = useMutation({
    mutationFn: (text: string) => askFindingQuestion(analysisId, finding.id, text),
    onSuccess: (newAnswer: GroundedAnswerResponse) => {
      setQuestionText('');
      setErrorMessage(null);
      queryClient.setQueryData(queryKey, (old: { count: number; limit: number; questions: GroundedAnswerResponse[] } | undefined) => {
        if (!old) {
          return { analysis_id: analysisId, finding_id: finding.id, count: 1, limit: 20, questions: [newAnswer] };
        }
        return {
          ...old,
          count: old.count + 1,
          questions: [...old.questions, newAnswer],
        };
      });
    },
    onError: (err: unknown) => {
      if (err instanceof Error && err.message.includes('429')) {
        setErrorMessage('Question limit reached (maximum 20 questions per analysis session).');
      } else {
        setErrorMessage('Unable to process question. Please verify your connection and try again.');
      }
    },
  });

  const handleSubmit = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || mutation.isPending) return;
    setErrorMessage(null);
    mutation.mutate(trimmed);
  };

  const questions = history?.questions ?? [];

  return (
    <section className="finding-qa-section" aria-labelledby="finding-qa-heading">
      <div className="finding-qa-header">
        <div className="finding-qa-title-row">
          <MessageSquare size={16} className="qa-icon" />
          <h3 id="finding-qa-heading">Grounded Finding Q&A</h3>
          <span className="qa-badge-grounded">Strictly Grounded</span>
        </div>
        <p className="finding-qa-subtitle">
          Ask why this finding was flagged or explore its retrieved evidence records.
          Broad legal advice and general chat are refused.
        </p>
      </div>

      <div className="qa-suggested-prompts" aria-label="Suggested questions">
        <span className="qa-prompts-label">Suggested:</span>
        <div className="qa-chips">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="qa-chip-button"
              onClick={() => {
                setQuestionText(prompt);
                handleSubmit(prompt);
              }}
              disabled={mutation.isPending}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <form
        className="qa-input-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit(questionText);
        }}
      >
        <div className="qa-input-wrapper">
          <input
            type="text"
            className="qa-text-input"
            placeholder="Ask a question about this finding (e.g. Why was this flagged?)"
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
            maxLength={500}
            disabled={mutation.isPending}
            aria-label="Ask a question about this finding"
          />
          <button
            type="submit"
            className="qa-submit-button"
            disabled={!questionText.trim() || mutation.isPending}
            aria-label="Submit question"
          >
            {mutation.isPending ? 'Answering…' : <><Send size={14} /> Ask</>}
          </button>
        </div>
        <div className="qa-char-counter">
          <small>{questionText.length}/500 characters</small>
        </div>
      </form>

      {errorMessage && (
        <div className="qa-error-alert" role="alert">
          <AlertTriangle size={14} />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="qa-history" aria-live="polite">
        {isLoading && <p className="qa-loading" role="status" aria-live="polite">Loading previous questions…</p>}
        {mutation.isPending && <p className="sr-only" role="status" aria-live="polite">Answering question…</p>}
        {questions.length === 0 && !isLoading && !mutation.isPending && (
          <p className="qa-empty-state">No questions asked yet for this finding. Use a suggested prompt above or type your own question.</p>
        )}

        {questions.map((q, idx) => (
          <article key={`${q.created_at}-${idx}`} className={`qa-thread-card status-${q.status}`}>
            <div className="qa-user-question">
              <span className="qa-actor-label">Question:</span>
              <p className="qa-question-text">{q.question}</p>
            </div>

            <div className="qa-system-answer">
              <div className="qa-answer-header">
                <span className="qa-actor-label">Grounded Answer:</span>
                {q.status === 'answered' && (
                  <span className="qa-status-pill status-answered">
                    <CheckCircle2 size={12} /> Grounded
                  </span>
                )}
                {q.status === 'refused' && (
                  <span className="qa-status-pill status-refused">
                    <AlertTriangle size={12} /> Refused: {q.refusal_reason === 'broad_legal_advice' ? 'Legal Advice' : 'Out of Scope'}
                  </span>
                )}
                {q.status === 'no_evidence' && (
                  <span className="qa-status-pill status-no-evidence">
                    <HelpCircle size={12} /> Missing Source
                  </span>
                )}
              </div>

              <p className="qa-answer-text">{q.answer}</p>

              {q.status === 'refused' && q.refusal_reason === 'broad_legal_advice' && (
                <div className="qa-disclaimer-box">
                  <AlertTriangle size={14} className="qa-disclaimer-icon" />
                  <span>
                    <strong>Legal Advice Disclaimer:</strong> FilingGuard AI is an automated compliance
                    safety tool. It does not provide legal strategy or judicial counsel. Consult qualified
                    legal counsel for litigation advice.
                  </span>
                </div>
              )}

              {q.evidence_record_ids.length > 0 && (
                <div className="qa-citations-box">
                  <span className="qa-citations-label">Cited Evidence Records:</span>
                  <div className="qa-citations-list">
                    {q.evidence_record_ids.map((eid) => (
                      <span key={eid} className="qa-citation-pill" title={eid}>
                        Record {eid.slice(0, 8)}…
                      </span>
                    ))}
                    {q.source_authorities.map((auth, aIdx) => (
                      <span key={`${auth}-${aIdx}`} className="qa-auth-pill">
                        {auth}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {q.source_urls.length > 0 && (
                <div className="qa-source-links">
                  {q.source_urls.map((url, uIdx) => (
                    <a
                      key={`${url}-${uIdx}`}
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="qa-external-link"
                    >
                      View authentic opinion on CourtListener <ArrowRight size={12} />
                    </a>
                  ))}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
