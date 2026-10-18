import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowRight, FileText, FolderOpen, LockKeyhole, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { useNavigate } from 'react-router';
import { getCapabilities, prepareDemo, preparePDF, prepareText } from '../../lib/api/intake';

gsap.registerPlugin(useGSAP);

export function IntakeComposer() {
  const capabilities = useQuery({ queryKey: ['capabilities'], queryFn: ({ signal }) => getCapabilities(signal), retry: false });
  const enabled = capabilities.data?.intake_enabled === true;
  const [mode, setMode] = useState<'text' | 'pdf' | 'demo'>('text');
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');
  const [name, setName] = useState('Untitled filing');
  const [aiUsed, setAIUsed] = useState(false);
  const [courtProfile, setCourtProfile] = useState('unverified');
  const input = useRef<HTMLInputElement>(null);
  const composer = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const navigate = useNavigate();
  const count = Array.from(text).length;
  useGSAP(() => {
    const media = gsap.matchMedia();
    media.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.from('.composer-panel', { y: 5, opacity: 0.7, duration: 0.2, clearProps: 'transform,opacity' });
    }, composer);
    return () => media.revert();
  }, { scope: composer, dependencies: [mode], revertOnUpdate: true });
  function chooseFile(candidate?: File) {
    if (!candidate) return;
    if (candidate.size > 10485760 || !candidate.name.toLowerCase().endsWith('.pdf')) {
      setFileError('Choose a PDF up to 10 MiB.'); setFile(null); return;
    }
    setFile(candidate); setFileError('');
  }
  const preparation = useMutation({ mutationFn: () => mode === 'demo' ? prepareDemo(aiUsed, courtProfile)
    : mode === 'pdf' && file ? preparePDF(file, courtProfile, aiUsed)
      : prepareText(text, name, courtProfile, aiUsed), retry: false,
    onSuccess: result => { setText(''); setFile(null); navigate(`/analyses/${result.analysis_id}`); },
  });
  const ready = enabled && !preparation.isPending && (mode === 'demo' || (mode === 'pdf' ? !!file
    : !!text.trim() && count <= 100000 && !!name.trim()));
  return <div className="intake-composer" ref={composer}>
    <div className="composer-topline">
    <div className="intake-modes" role="group" aria-label="Document source">
      <span className="mode-indicator" aria-hidden="true" style={{ transform: `translateX(${(['text', 'pdf', 'demo'] as const).indexOf(mode) * 100}%)` }} />
      {(['text', 'pdf', 'demo'] as const).map(value => <button type="button" key={value}
        aria-pressed={mode === value} disabled={preparation.isPending} onClick={() => {
          setMode(value);
          setAIUsed(value === 'demo');
          setFileError('');
          if (value === 'demo') {
            setCourtProfile('synthetic-demo-v1');
          } else if (courtProfile === 'synthetic-demo-v1') {
            setCourtProfile('unverified');
          }
          preparation.reset();
        }}>
        {value === 'pdf' ? <Upload size={16} /> : value === 'demo' ? <FolderOpen size={16} /> : <FileText size={16} />}
        {value === 'pdf' ? 'PDF' : value === 'demo' ? 'Demo' : 'Text'}</button>)}
    </div><span className="composer-privacy"><LockKeyhole size={13} />{enabled ? 'Private session' : 'Submission disabled'}</span></div>
    <div className="composer-panel" key={mode}>
    {mode === 'text' && <><div className="composer-document-name"><label className="sr-only" htmlFor="document-name">Document name</label>
      <FileText size={16} /><input id="document-name" maxLength={255} value={name} disabled={!enabled || preparation.isPending}
        onChange={event => setName(event.target.value)} />
        <button className="composer-upload" title="Upload PDF" aria-label="Upload PDF" disabled={!enabled || preparation.isPending}
          onClick={() => setMode('pdf')}><Upload size={17} /></button></div>
      <label className="sr-only" htmlFor="filing">Filing text</label>
      <textarea id="filing" value={text} disabled={!enabled || preparation.isPending}
        placeholder={enabled ? 'Your filing starts here.\nPaste the text you want to prepare...' : 'Document intake is not available in this preview.'}
        onChange={event => setText(event.target.value)} /></>}
    {mode === 'pdf' && <div className={`pdf-drop ${dragging ? 'is-dragging' : ''}`}
      onDragOver={event => { event.preventDefault(); if (enabled && !preparation.isPending) setDragging(true); }}
      onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false); }}
      onDrop={event => { event.preventDefault(); setDragging(false); if (enabled && !preparation.isPending) chooseFile(event.dataTransfer.files[0]); }}>
      <input ref={input} className="sr-only" type="file" accept="application/pdf,.pdf" aria-label="PDF file"
        disabled={!enabled || preparation.isPending} onChange={event => chooseFile(event.target.files?.[0])} />
      <Upload className="drop-icon" size={30} aria-hidden="true" />
      <strong>{file ? 'Your PDF is ready to prepare' : 'Drop your filing here'}</strong>
      <button type="button" className="secondary-button" disabled={!enabled || preparation.isPending}
        onClick={() => input.current?.click()}><Upload size={16} />Upload PDF</button>
      <span>{file ? `${file.name} | ${(file.size / 1024).toFixed(1)} KiB` : 'PDF | 10 MiB | 20 pages'}</span>
      {file && <button type="button" className="icon-button" title="Remove PDF" aria-label="Remove PDF" disabled={preparation.isPending}
        onClick={() => { setFile(null); if (input.current) input.current.value = ''; }}><X size={16} /></button>}
    </div>}
    {mode === 'demo' && <div className="composer-demo"><FolderOpen size={30} /><strong>A filing with something to find.</strong>
      <p>Synthetic filing with cached public sources. Expected scenarios are not executed findings.</p><span>Curated sample / Text-based PDF</span></div>}
    </div>
    <div className="intake-options"><div className="court-option"><label htmlFor="court">Court profile</label>
      <select id="court" disabled={!enabled || preparation.isPending} value={courtProfile}
        onChange={event => setCourtProfile(event.target.value)}>
        <option value="unverified">Court rules not configured</option>
        <option value="us-txnd-lr7-2f-v1">N.D. Tex. Local Rule 7.2(f) (Generative AI Heading)</option>
        {mode === 'demo' && <option value="synthetic-demo-v1">Synthetic demo court (not a real court)</option>}</select></div>
      <label className="checkbox-label"><input type="checkbox" checked={aiUsed}
        disabled={!enabled || preparation.isPending} onChange={event => setAIUsed(event.target.checked)} />
        Generative AI used in this filing</label></div>
    {(fileError || preparation.isError) && <p role="alert">{fileError || preparation.error?.message || 'Preparation failed'}</p>}
    {preparation.isPending && <p className="sr-only" role="status" aria-live="polite">Preparing document for review…</p>}
    {capabilities.isError && <p role="status" aria-live="polite">Intake availability could not be checked.
      <button className="secondary-button" onClick={() => void capabilities.refetch()}>Retry availability</button></p>}
    <div className="document-bottom"><span>{mode === 'text' ? `${count.toLocaleString()} / 100,000 characters`
      : mode === 'demo' ? 'Synthetic demo' : file ? 'PDF selected' : 'No PDF selected'}</span>
      <button className="primary-button" disabled={!ready} onClick={() => preparation.mutate()}>
        {preparation.isPending ? 'Preparing document' : 'Prepare document'}<ArrowRight size={16} /></button></div>
    <div className="composer-review-status"><span>{mode === 'demo'
      ? 'Cached public sources; fresh local checks. Semantic review requires an enabled model provider.'
      : 'Local checks are available after preparation; external source and model stages require configuration.'}</span></div>
  </div>;
}
