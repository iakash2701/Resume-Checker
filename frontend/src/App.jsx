import React, { useState, useEffect, useRef } from 'react';
import { 
  Upload,
  EyeOff,
  Copy,
  Send,
  Zap,
  Network,
  HelpCircle,
  Users, 
  Briefcase, 
  GitPullRequest, 
  Settings, 
  Search, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  X, 
  Phone, 
  Mail, 
  MapPin, 
  Check, 
  Edit2, 
  Filter, 
  Sparkles, 
  TrendingDown, 
  AlertTriangle, 
  ArrowRight, 
  RotateCcw,
  Sliders,
  Eye,
  Kanban,
  ClipboardList,
  History,
  Save,
  CheckCheck,
  Scale,
  Download,
  BookmarkPlus,
  Trash2,
  FolderOpen
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend
} from 'recharts';

const API_BASE = import.meta.env.VITE_API_BASE || "/api";
const STAGES = ["Applied", "Shortlisted", "Interview", "Offer", "Rejected"];

export default function App() {
  const [candidates, setCandidates] = useState([]);
  const [jds, setJds] = useState([]);
  const [stats, setStats] = useState({
    total_candidates: 0,
    applied: 0,
    shortlisted: 0,
    interview: 0,
    offers: 0,
    rejected: 0,
    total_jds: 0,
    average_jd_match: 0.0,
    candidates_with_confidence_issues: 0,
    candidates_requiring_review: 0,
    fields_needing_verification: 0
  });

  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [blindReviewMode, setBlindReviewMode] = useState(false);
  const [isUploadingResume, setIsUploadingResume] = useState(false);
  const [candidateDuplicates, setCandidateDuplicates] = useState(null);
  const [candidateSkillGap, setCandidateSkillGap] = useState(null);
  const [candidateIntelligence, setCandidateIntelligence] = useState(null);
  const [activeCandidateDetailTab, setActiveCandidateDetailTab] = useState("overview"); // overview, intelligence, gap, duplicates
  
  // Bulk Email State
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailTemplates, setEmailTemplates] = useState({});
  const [selectedEmailTemplate, setSelectedEmailTemplate] = useState("interview_invitation");
  const [emailRole, setEmailRole] = useState("Software Engineer");
  const [emailDryRun, setEmailDryRun] = useState(true);
  const [emailQueueResult, setEmailQueueResult] = useState(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeTab, setActiveTab] = useState("dashboard"); // dashboard, candidates, kanban, reviewQueue, whatif, jds, presets
  const [selectedStageFilter, setSelectedStageFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [reviewQueue, setReviewQueue] = useState([]);
  const [loading, setLoading] = useState(true);

  // Phase 6 Comparison State
  const [selectedForCompare, setSelectedForCompare] = useState([]); // candidate IDs (max 3)
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // Phase 6 Filter Presets State
  const [presets, setPresets] = useState([]);
  const [presetNameInput, setPresetNameInput] = useState("");
  const [presetModalOpen, setPresetModalOpen] = useState(false);

  // Editable candidate profile state
  const [editMode, setEditMode] = useState(false);
  const [editFormData, setEditFormData] = useState({});

  // What-If Funnel State
  const [whatifFilters, setWhatifFilters] = useState({
    tenth_pct: 70,
    twelfth_pct: 70,
    cgpa: 7.5,
    skills: ["Python"],
    skill_mode: "AND",
    years_experience: 1.0,
    location: "",
    grad_year: "",
    min_match_score: 75,
    jd_id: 1
  });

  const [activeEnabled, setActiveEnabled] = useState({
    tenth_pct: true,
    twelfth_pct: true,
    cgpa: true,
    skills: true,
    years_experience: true,
    location: false,
    grad_year: false,
    min_match_score: true
  });

  const [whatifData, setWhatifData] = useState(null);
  const [whatifLoading, setWhatifLoading] = useState(false);
  const [previewDelta, setPreviewDelta] = useState(null);
  const [skillInput, setSkillInput] = useState("");

  const debounceTimer = useRef(null);

  useEffect(() => {
    fetchStats();
    fetchCandidates();
    fetchJDs();
    fetchReviewQueue();
    fetchPresets();
  }, [selectedStageFilter]);

  useEffect(() => {
    if (activeTab === "whatif") {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      debounceTimer.current = setTimeout(() => {
        runWhatIfSimulation();
      }, 250);
    }
  }, [whatifFilters, activeEnabled, activeTab]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (res.ok) setStats(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCandidates = async (query = searchQuery, stage = selectedStageFilter) => {
    try {
      let url = `${API_BASE}/candidates?page_size=100`;
      if (query) url += `&search=${encodeURIComponent(query)}`;
      if (stage) url += `&stage=${encodeURIComponent(stage)}`;
      if (whatifFilters.jd_id) url += `&jd_id=${whatifFilters.jd_id}`;

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setCandidates(data.items || data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchReviewQueue = async () => {
    try {
      const res = await fetch(`${API_BASE}/candidates/review-queue`);
      if (res.ok) setReviewQueue(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchJDs = async () => {
    try {
      const res = await fetch(`${API_BASE}/jds`);
      if (res.ok) setJds(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchPresets = async () => {
    try {
      const res = await fetch(`${API_BASE}/presets`);
      if (res.ok) setPresets(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    fetchCandidates(val, selectedStageFilter);
  };

  const handleStageCardClick = (stage) => {
    const nextStage = selectedStageFilter === stage ? "" : stage;
    setSelectedStageFilter(nextStage);
    setActiveTab("candidates");
    fetchCandidates(searchQuery, nextStage);
  };

  // Selection for comparison
  const toggleSelectForCompare = (candId) => {
    setSelectedForCompare(prev => {
      if (prev.includes(candId)) {
        return prev.filter(id => id !== candId);
      } else {
        if (prev.length >= 3) {
          alert("Maximum 3 candidates can be compared simultaneously.");
          return prev;
        }
        return [...prev, candId];
      }
    });
  };

  const openComparisonModal = async () => {
    if (selectedForCompare.length < 2) {
      alert("Please select at least 2 candidates to compare.");
      return;
    }
    setCompareLoading(true);
    setComparisonModalOpen(true);
    try {
      const res = await fetch(`${API_BASE}/candidates/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: selectedForCompare,
          jd_id: whatifFilters.jd_id ? parseInt(whatifFilters.jd_id, 10) : null
        })
      });
      if (res.ok) {
        const data = await res.json();
        setComparisonData(data);
      } else {
        const err = await res.json();
        alert(err.detail || "Comparison failed");
      }
    } catch (e) {
      console.error("Comparison request failed:", e);
    } finally {
      setCompareLoading(false);
    }
  };

  // CSV Export Trigger
  const handleResumeUpload = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setIsUploadingResume(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/resumes/upload`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const createdCand = await res.json();
        await fetchCandidates();
        await fetchStats();
        openCandidateDrawer(createdCand);
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(`Failed to upload resume: ${errData.detail || res.statusText}`);
      }
    } catch (err) {
      alert(`Network error uploading resume: ${err.message}`);
    } finally {
      setIsUploadingResume(false);
      e.target.value = "";
    }
  };

  const handleExportCSV = () => {
    let url = `${API_BASE}/candidates/export?`;
    const params = [];
    if (searchQuery) params.push(`search=${encodeURIComponent(searchQuery)}`);
    if (selectedStageFilter) params.push(`stage=${encodeURIComponent(selectedStageFilter)}`);
    if (whatifFilters.jd_id) params.push(`jd_id=${whatifFilters.jd_id}`);
    if (activeEnabled.cgpa && whatifFilters.cgpa) params.push(`cgpa_min=${whatifFilters.cgpa}`);
    if (activeEnabled.tenth_pct && whatifFilters.tenth_pct) params.push(`tenth_min=${whatifFilters.tenth_pct}`);
    if (activeEnabled.twelfth_pct && whatifFilters.twelfth_pct) params.push(`twelfth_min=${whatifFilters.twelfth_pct}`);
    if (activeEnabled.years_experience && whatifFilters.years_experience) params.push(`exp_min=${whatifFilters.years_experience}`);
    if (activeEnabled.skills && whatifFilters.skills.length > 0) {
      params.push(`skills=${encodeURIComponent(whatifFilters.skills.join(","))}`);
      params.push(`skills_mode=${whatifFilters.skill_mode.toLowerCase()}`);
    }

    url += params.join("&");
    window.open(url, "_blank");
  };

  // Presets Save / Load / Delete
  const handleSaveCurrentAsPreset = async () => {
    if (!presetNameInput.trim()) {
      alert("Please enter a preset name.");
      return;
    }
    const filterState = {
      whatifFilters,
      activeEnabled,
      searchQuery,
      selectedStageFilter
    };

    try {
      const res = await fetch(`${API_BASE}/presets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: presetNameInput.trim(),
          filters_json: JSON.stringify(filterState)
        })
      });
      if (res.ok) {
        setPresetNameInput("");
        setPresetModalOpen(false);
        fetchPresets();
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to save preset");
      }
    } catch (e) {
      console.error("Failed to save preset:", e);
    }
  };

  const handleLoadPreset = (preset) => {
    try {
      const loaded = JSON.parse(preset.filters_json);
      if (loaded.whatifFilters) setWhatifFilters(loaded.whatifFilters);
      if (loaded.activeEnabled) setActiveEnabled(loaded.activeEnabled);
      if (loaded.searchQuery !== undefined) setSearchQuery(loaded.searchQuery);
      if (loaded.selectedStageFilter !== undefined) setSelectedStageFilter(loaded.selectedStageFilter);
      fetchCandidates(loaded.searchQuery || "", loaded.selectedStageFilter || "");
      alert(`Loaded filter preset: "${preset.name}"`);
    } catch (e) {
      console.error("Failed to parse preset filters:", e);
    }
  };

  const handleDeletePreset = async (presetId) => {
    if (!confirm("Are you sure you want to delete this preset?")) return;
    try {
      const res = await fetch(`${API_BASE}/presets/${presetId}`, { method: "DELETE" });
      if (res.ok) fetchPresets();
    } catch (e) {
      console.error(e);
    }
  };

  const openCandidateDrawer = async (cand) => {
    setSelectedCandidate(cand);
    setEditMode(false);
    setActiveCandidateDetailTab("overview");
    setCandidateDuplicates(null);
    setCandidateSkillGap(null);
    setCandidateIntelligence(null);

    setEditFormData({
      name: cand.name || "",
      email: cand.email || "",
      phone: cand.phone || "",
      location: cand.location || "",
      college: cand.college || "",
      degree: cand.degree || "",
      cgpa_10: cand.cgpa_10 ?? "",
      tenth_pct: cand.tenth_pct ?? "",
      twelfth_pct: cand.twelfth_pct ?? "",
      grad_year: cand.grad_year ?? "",
      years_experience: cand.years_experience ?? 0.0
    });

    try {
      const res = await fetch(`${API_BASE}/candidates/${cand.id}/audit`);
      if (res.ok) setAuditLogs(await res.json());
    } catch (err) {
      console.error(err);
    }

    fetchCandidateDuplicates(cand.id);
    fetchCandidateSkillGap(cand.id);
    fetchCandidateIntelligence(cand.id);
  };

  const fetchCandidateDuplicates = async (candId) => {
    try {
      const res = await fetch(`${API_BASE}/candidates/${candId}/duplicates?threshold=65`);
      if (res.ok) setCandidateDuplicates(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCandidateSkillGap = async (candId) => {
    try {
      const jdId = whatifFilters.jd_id || 1;
      const res = await fetch(`${API_BASE}/candidates/${candId}/skill-gap?jd_id=${jdId}`);
      if (res.ok) setCandidateSkillGap(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCandidateIntelligence = async (candId) => {
    try {
      const jdId = whatifFilters.jd_id || 1;
      const res = await fetch(`${API_BASE}/candidates/${candId}/intelligence?jd_id=${jdId}`);
      if (res.ok) setCandidateIntelligence(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkDuplicate = async (candId, targetId) => {
    try {
      const res = await fetch(`${API_BASE}/candidates/${candId}/mark-duplicate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ duplicate_of_id: targetId })
      });
      if (res.ok) {
        fetchCandidates();
        fetchStats();
        if (selectedCandidate) {
          const aRes = await fetch(`${API_BASE}/candidates/${candId}/audit`);
          if (aRes.ok) setAuditLogs(await aRes.json());
        }
        alert("Candidate marked as duplicate successfully.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchEmailTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE}/email/templates`);
      if (res.ok) setEmailTemplates(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenBulkEmail = () => {
    fetchEmailTemplates();
    setEmailQueueResult(null);
    setEmailModalOpen(true);
  };

  const handleSendBulkEmail = async () => {
    setEmailLoading(true);
    try {
      const targetCandidates = selectedForCompare.length > 0
        ? candidates.filter(c => selectedForCompare.includes(c.id))
        : candidates.slice(0, 5);
        
      const res = await fetch(`${API_BASE}/email/bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidates: targetCandidates.map(c => ({
            id: c.id,
            name: c.name,
            email: c.email || `${c.id}@candidate.internal`,
            skills: c.skills ? c.skills.join(", ") : "core competencies"
          })),
          template_key: selectedEmailTemplate,
          role: emailRole,
          dry_run: emailDryRun
        })
      });
      if (res.ok) {
        setEmailQueueResult(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setEmailLoading(false);
    }
  };

  const handleStageTransition = async (candId, newStage) => {
    try {
      const res = await fetch(`${API_BASE}/candidates/${candId}/stage`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: newStage })
      });
      if (res.ok) {
        const updated = await res.json();
        setCandidates(prev => prev.map(c => c.id === candId ? { ...c, pipeline_stage: newStage } : c));
        if (selectedCandidate && selectedCandidate.id === candId) {
          setSelectedCandidate(prev => ({ ...prev, pipeline_stage: newStage }));
          const aRes = await fetch(`${API_BASE}/candidates/${candId}/audit`);
          if (aRes.ok) setAuditLogs(await aRes.json());
        }
        fetchStats();
      }
    } catch (err) {
      console.error("Failed to transition candidate stage:", err);
    }
  };

  const handleVerifyEvidence = async (fieldName, val = null) => {
    if (!selectedCandidate) return;
    try {
      const res = await fetch(`${API_BASE}/candidates/${selectedCandidate.id}/verify-evidence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          field_name: fieldName,
          value: val !== null ? String(val) : String(selectedCandidate[fieldName] || ""),
          confirmed: true
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedCandidate(updated);
        setCandidates(prev => prev.map(c => c.id === updated.id ? updated : c));
        const aRes = await fetch(`${API_BASE}/candidates/${updated.id}/audit`);
        if (aRes.ok) setAuditLogs(await aRes.json());
        fetchStats();
        fetchReviewQueue();
      }
    } catch (err) {
      console.error("Verification failed:", err);
    }
  };

  const handleSaveProfileEdit = async () => {
    if (!selectedCandidate) return;
    const payload = {};
    if (editFormData.name) payload.name = editFormData.name;
    if (editFormData.email) payload.email = editFormData.email;
    if (editFormData.phone) payload.phone = editFormData.phone;
    if (editFormData.location) payload.location = editFormData.location;
    if (editFormData.college) payload.college = editFormData.college;
    if (editFormData.degree) payload.degree = editFormData.degree;
    if (editFormData.cgpa_10 !== "") payload.cgpa_10 = parseFloat(editFormData.cgpa_10);
    if (editFormData.tenth_pct !== "") payload.tenth_pct = parseFloat(editFormData.tenth_pct);
    if (editFormData.twelfth_pct !== "") payload.twelfth_pct = parseFloat(editFormData.twelfth_pct);
    if (editFormData.grad_year !== "") payload.grad_year = parseInt(editFormData.grad_year, 10);
    if (editFormData.years_experience !== "") payload.years_experience = parseFloat(editFormData.years_experience);

    try {
      const res = await fetch(`${API_BASE}/candidates/${selectedCandidate.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedCandidate(updated);
        setCandidates(prev => prev.map(c => c.id === updated.id ? updated : c));
        setEditMode(false);
        const aRes = await fetch(`${API_BASE}/candidates/${updated.id}/audit`);
        if (aRes.ok) setAuditLogs(await aRes.json());
        fetchStats();
      }
    } catch (err) {
      console.error("Save edit failed:", err);
    }
  };

  const runWhatIfSimulation = async (customFilters = null) => {
    setWhatifLoading(true);
    const targetFilters = customFilters || whatifFilters;
    const payload = {};

    if (activeEnabled.tenth_pct && targetFilters.tenth_pct !== "") payload.tenth_pct = parseFloat(targetFilters.tenth_pct);
    if (activeEnabled.twelfth_pct && targetFilters.twelfth_pct !== "") payload.twelfth_pct = parseFloat(targetFilters.twelfth_pct);
    if (activeEnabled.cgpa && targetFilters.cgpa !== "") payload.cgpa = parseFloat(targetFilters.cgpa);
    if (activeEnabled.skills && targetFilters.skills.length > 0) {
      payload.skills = targetFilters.skills;
      payload.skill_mode = targetFilters.skill_mode;
    }
    if (activeEnabled.years_experience && targetFilters.years_experience !== "") payload.years_experience = parseFloat(targetFilters.years_experience);
    if (activeEnabled.location && targetFilters.location) payload.location = targetFilters.location;
    if (activeEnabled.grad_year && targetFilters.grad_year) payload.grad_year = parseInt(targetFilters.grad_year);
    if (activeEnabled.min_match_score && targetFilters.min_match_score !== "") payload.min_match_score = parseFloat(targetFilters.min_match_score);
    if (targetFilters.jd_id) payload.jd_id = parseInt(targetFilters.jd_id);

    try {
      const res = await fetch(`${API_BASE}/whatif`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setWhatifData(data);
      }
    } catch (err) {
      console.error("Failed to run What-If simulation:", err);
    } finally {
      setWhatifLoading(false);
    }
  };

  const renderConfidenceBadge = (confidence) => {
    if (confidence === "verified") {
      return (
        <span className="inline-flex items-center text-xs font-semibold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
          <CheckCheck className="h-3 w-3 mr-1 text-emerald-600" />
          Verified
        </span>
      );
    } else if (confidence === "high") {
      return (
        <span className="inline-flex items-center text-xs font-semibold text-emerald-700">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
          High confidence
        </span>
      );
    } else if (confidence === "medium") {
      return (
        <span className="inline-flex items-center text-xs font-semibold text-amber-700">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500 mr-1.5"></span>
          Medium confidence
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center text-xs font-semibold text-rose-700">
          <span className="h-1.5 w-1.5 rounded-full bg-rose-500 mr-1.5"></span>
          Low confidence
        </span>
      );
    }
  };

  const getStageBadge = (stage) => {
    switch (stage) {
      case "Applied":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">Applied</span>;
      case "Shortlisted":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">Shortlisted</span>;
      case "Interview":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">Interview</span>;
      case "Offer":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">Offer</span>;
      case "Rejected":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">Rejected</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">{stage}</span>;
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col flex-shrink-0">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white tracking-wider">
              HS
            </div>
            <span className="text-xl font-bold tracking-tight text-white">HireSwift</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Smart Recruiter ATS</p>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1">
          <button 
            onClick={() => setActiveTab("dashboard")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "dashboard" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <GitPullRequest className="mr-3 h-4 w-4" />
            Dashboard
          </button>

          <button 
            onClick={() => setActiveTab("candidates")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "candidates" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Users className="mr-3 h-4 w-4" />
            Candidates Directory
          </button>

          <button 
            onClick={() => setActiveTab("kanban")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "kanban" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Kanban className="mr-3 h-4 w-4 text-emerald-400" />
            Kanban Pipeline
          </button>

          <button 
            onClick={() => setActiveTab("reviewQueue")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors relative ${
              activeTab === "reviewQueue" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <ClipboardList className="mr-3 h-4 w-4 text-amber-400" />
            Review Queue
            {stats.candidates_requiring_review > 0 && (
              <span className="ml-auto bg-amber-500 text-slate-900 font-extrabold text-[10px] px-2 py-0.5 rounded-full">
                {stats.candidates_requiring_review}
              </span>
            )}
          </button>

          <button 
            onClick={() => setActiveTab("whatif")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "whatif" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Filter className="mr-3 h-4 w-4 text-indigo-400" />
            What-If Funnel
          </button>

          <button 
            onClick={() => setActiveTab("presets")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "presets" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <BookmarkPlus className="mr-3 h-4 w-4 text-cyan-400" />
            Filter Presets
          </button>

          <button 
            onClick={() => setActiveTab("jds")}
            className={`w-full flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors ${
              activeTab === "jds" ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Briefcase className="mr-3 h-4 w-4" />
            Job Descriptions
          </button>
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-800/60 rounded-lg p-3 text-xs text-slate-400">
            <p className="font-semibold text-cyan-300 flex items-center">
              <Scale className="h-3.5 w-3.5 mr-1" /> Phase 6 Active
            </p>
            <p className="mt-0.5 text-[11px]">Compare 2-3 Candidates, CSV Export & Presets</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar with Universal Search & Comparison / Export action bar */}
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between">
          <div className="relative w-[450px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search across Name, Email, Phone, Skills, College, Degree, Location..."
              value={searchQuery}
              onChange={handleSearch}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center space-x-3">
            {/* Compare Candidates button */}
            <button
              onClick={openComparisonModal}
              disabled={selectedForCompare.length < 2}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center transition-colors ${
                selectedForCompare.length >= 2 
                  ? "bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs" 
                  : "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
              }`}
            >
              <Scale className="h-3.5 w-3.5 mr-1.5" />
              Compare Selected ({selectedForCompare.length}/3)
            </button>

            {/* Resume Upload input */}
            <label className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors flex items-center cursor-pointer shadow-xs ${
              isUploadingResume 
                ? "bg-slate-100 text-slate-400 border-slate-200 cursor-wait" 
                : "bg-white border-slate-200 hover:bg-slate-50 text-slate-700"
            }`}>
              <Upload className={`h-3.5 w-3.5 mr-1.5 ${isUploadingResume ? "animate-bounce text-indigo-600" : "text-slate-500"}`} />
              {isUploadingResume ? "Uploading..." : "Upload Resume"}
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                disabled={isUploadingResume}
                className="hidden"
                onChange={handleResumeUpload}
              />
            </label>

            {/* Export CSV button */}
            <button
              onClick={handleExportCSV}
              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 flex items-center shadow-2xs"
            >
              <Download className="h-3.5 w-3.5 mr-1.5 text-slate-500" />
              Export CSV
            </button>

            {/* Bulk Email Dry-Run button */}
            <button
              onClick={handleOpenBulkEmail}
              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 flex items-center shadow-2xs"
            >
              <Send className="h-3.5 w-3.5 mr-1.5 text-emerald-600" />
              Bulk Email
            </button>

            {/* Blind Review Mode Toggle */}
            <button
              onClick={() => setBlindReviewMode(!blindReviewMode)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center transition-colors border ${
                blindReviewMode 
                  ? "bg-purple-600 text-white border-purple-700 shadow-xs" 
                  : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
              }`}
            >
              {blindReviewMode ? <EyeOff className="h-3.5 w-3.5 mr-1.5" /> : <Eye className="h-3.5 w-3.5 mr-1.5 text-purple-600" />}
              {blindReviewMode ? "Exit Blind Review" : "Blind Review Mode"}
            </button>

            {/* Save Filter Preset button */}
            <button
              onClick={() => setPresetModalOpen(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 flex items-center shadow-2xs"
            >
              <BookmarkPlus className="h-3.5 w-3.5 mr-1.5 text-cyan-600" />
              Save Preset
            </button>
          </div>
        </header>

        {/* Workspace Body */}
        <main className="flex-1 overflow-y-auto p-8">
          {/* TAB 1: DASHBOARD OVERVIEW */}
          {activeTab === "dashboard" && (
            <div className="space-y-8">
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Recruiter Pipeline Overview</h2>
                <div className="grid grid-cols-6 gap-4">
                  <div onClick={() => handleStageCardClick("")} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm cursor-pointer hover:border-indigo-400 transition-colors">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Candidates</span>
                    <div className="text-2xl font-bold mt-1 text-slate-900">{stats.total_candidates}</div>
                    <span className="text-[11px] text-slate-400">All registered profiles</span>
                  </div>
                  <div onClick={() => handleStageCardClick("Applied")} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm border-l-4 border-l-blue-500 cursor-pointer hover:border-blue-400 transition-colors">
                    <span className="text-xs font-semibold uppercase tracking-wider text-blue-600">Applied</span>
                    <div className="text-2xl font-bold mt-1 text-blue-900">{stats.applied}</div>
                    <span className="text-[11px] text-slate-400">Click to filter table</span>
                  </div>
                  <div onClick={() => handleStageCardClick("Shortlisted")} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm border-l-4 border-l-emerald-500 cursor-pointer hover:border-emerald-400 transition-colors">
                    <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600">Shortlisted</span>
                    <div className="text-2xl font-bold mt-1 text-emerald-900">{stats.shortlisted}</div>
                    <span className="text-[11px] text-slate-400">Click to filter table</span>
                  </div>
                  <div onClick={() => handleStageCardClick("Interview")} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm border-l-4 border-l-amber-500 cursor-pointer hover:border-amber-400 transition-colors">
                    <span className="text-xs font-semibold uppercase tracking-wider text-amber-600">Interview</span>
                    <div className="text-2xl font-bold mt-1 text-amber-900">{stats.interview}</div>
                    <span className="text-[11px] text-slate-400">Click to filter table</span>
                  </div>
                  <div onClick={() => handleStageCardClick("Offer")} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm border-l-4 border-l-purple-500 cursor-pointer hover:border-purple-400 transition-colors">
                    <span className="text-xs font-semibold uppercase tracking-wider text-purple-600">Offer</span>
                    <div className="text-2xl font-bold mt-1 text-purple-900">{stats.offers}</div>
                    <span className="text-[11px] text-slate-400">Click to filter table</span>
                  </div>
                  <div onClick={() => handleStageCardClick("Rejected")} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm border-l-4 border-l-rose-500 cursor-pointer hover:border-rose-400 transition-colors">
                    <span className="text-xs font-semibold uppercase tracking-wider text-rose-600">Rejected</span>
                    <div className="text-2xl font-bold mt-1 text-rose-900">{stats.rejected}</div>
                    <span className="text-[11px] text-slate-400">Click to filter table</span>
                  </div>
                </div>
              </div>

              {/* Data Quality & Match */}
              <div className="grid grid-cols-3 gap-6">
                <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
                  <span className="text-xs font-semibold uppercase text-slate-400">Average Match Score</span>
                  <div className="text-3xl font-extrabold text-slate-900 mt-2">{stats.average_jd_match}%</div>
                  <p className="text-xs text-slate-500 mt-1">Primary Job Description Match</p>
                </div>
                <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm">
                  <span className="text-xs font-semibold uppercase text-amber-600">Parsing Confidence Issues</span>
                  <div className="text-3xl font-extrabold text-amber-700 mt-2">{stats.candidates_with_confidence_issues}</div>
                  <p className="text-xs text-slate-500 mt-1">Unverified low/medium confidence records</p>
                </div>
                <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-semibold uppercase text-indigo-600">Review Queue</span>
                    <div className="text-3xl font-extrabold text-indigo-700 mt-2">{stats.candidates_requiring_review}</div>
                    <p className="text-xs text-slate-500 mt-1">{stats.fields_needing_verification} unverified fields</p>
                  </div>
                  <button onClick={() => setActiveTab("reviewQueue")} className="mt-4 px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-bold hover:bg-indigo-100 flex items-center justify-center w-full">
                    Open Review Queue <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: CANDIDATES DIRECTORY */}
          {activeTab === "candidates" && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
                <div>
                  <h2 className="font-bold text-slate-800">Candidates Directory ({candidates.length})</h2>
                  <p className="text-xs text-slate-400">Select checkboxes to compare up to 3 candidates side-by-side</p>
                </div>
                <div className="flex items-center space-x-2">
                  {selectedForCompare.length > 0 && (
                    <button 
                      onClick={() => setSelectedForCompare([])} 
                      className="text-xs text-slate-500 hover:underline mr-2"
                    >
                      Clear Selection ({selectedForCompare.length})
                    </button>
                  )}
                  {selectedStageFilter && (
                    <button onClick={() => setSelectedStageFilter("")} className="text-xs text-indigo-600 font-bold hover:underline">
                      Clear Stage Filter
                    </button>
                  )}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50/80 text-xs uppercase text-slate-500 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3.5 w-10 text-center">
                        <Scale className="h-3.5 w-3.5 mx-auto text-slate-400" />
                      </th>
                      <th className="px-6 py-3.5">Candidate</th>
                      <th className="px-6 py-3.5">Location</th>
                      <th className="px-6 py-3.5">Degree</th>
                      <th className="px-6 py-3.5">College</th>
                      <th className="px-6 py-3.5">CGPA</th>
                      <th className="px-6 py-3.5">10th %</th>
                      <th className="px-6 py-3.5">12th %</th>
                      <th className="px-6 py-3.5">Experience</th>
                      <th className="px-6 py-3.5">Current Stage</th>
                      <th className="px-6 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {candidates.map(cand => (
                      <tr 
                        key={cand.id} 
                        onClick={() => openCandidateDrawer(cand)}
                        className={`hover:bg-slate-50/80 cursor-pointer transition-colors ${selectedForCompare.includes(cand.id) ? "bg-indigo-50/40" : ""}`}
                      >
                        <td className="px-4 py-4 text-center" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="checkbox"
                            checked={selectedForCompare.includes(cand.id)}
                            onChange={() => toggleSelectForCompare(cand.id)}
                            className="rounded text-indigo-600 focus:ring-0"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <div className="font-bold text-slate-900">{cand.name}</div>
                          <div className="text-xs text-slate-400">{cand.email}</div>
                        </td>
                        <td className="px-6 py-4 text-xs">{cand.location || "—"}</td>
                        <td className="px-6 py-4 text-xs max-w-xs truncate">{cand.degree || "—"}</td>
                        <td className="px-6 py-4 text-xs max-w-xs truncate">{cand.college || "—"}</td>
                        <td className="px-6 py-4 font-bold text-slate-800">{cand.cgpa_10 ?? "—"}</td>
                        <td className="px-6 py-4 text-xs">{cand.tenth_pct ? `${cand.tenth_pct}%` : "—"}</td>
                        <td className="px-6 py-4 text-xs">{cand.twelfth_pct ? `${cand.twelfth_pct}%` : "—"}</td>
                        <td className="px-6 py-4 text-xs">{cand.years_experience} yrs</td>
                        <td className="px-6 py-4 text-xs">{getStageBadge(cand.pipeline_stage)}</td>
                        <td className="px-6 py-4 text-right">
                          <select
                            value={cand.pipeline_stage}
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => handleStageTransition(cand.id, e.target.value)}
                            className="text-xs border border-slate-300 rounded p-1 bg-white font-medium"
                          >
                            {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                          </select>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: KANBAN PIPELINE */}
          {activeTab === "kanban" && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Interactive Hiring Kanban</h2>
                  <p className="text-xs text-slate-400">Drag and drop candidate cards across stages to automatically track status & audit log</p>
                </div>
                <span className="text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-md font-medium">
                  {candidates.length} active records
                </span>
              </div>

              <div className="grid grid-cols-5 gap-4 overflow-x-auto pb-4">
                {STAGES.map(stage => {
                  const stageCandidates = candidates.filter(c => c.pipeline_stage === stage);
                  return (
                    <div 
                      key={stage}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => {
                        e.preventDefault();
                        const candId = parseInt(e.dataTransfer.getData("text/plain"), 10);
                        if (candId) handleStageTransition(candId, stage);
                      }}
                      className="bg-slate-100/70 border border-slate-200 rounded-xl p-3 flex flex-col h-[700px]"
                    >
                      <div className="flex justify-between items-center pb-2.5 mb-2.5 border-b border-slate-200">
                        <span className="font-bold text-xs uppercase tracking-wider text-slate-700">{stage}</span>
                        <span className="h-5 w-5 rounded-full bg-slate-200 text-slate-700 text-[11px] font-bold flex items-center justify-center">
                          {stageCandidates.length}
                        </span>
                      </div>
                      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
                        {stageCandidates.map(c => (
                          <div
                            key={c.id}
                            draggable
                            onDragStart={(e) => e.dataTransfer.setData("text/plain", c.id)}
                            onClick={() => openCandidateDrawer(c)}
                            className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs hover:border-indigo-300 cursor-grab active:cursor-grabbing transition-all space-y-2"
                          >
                            <div className="flex justify-between items-start">
                              <span className="font-bold text-slate-900 text-sm">{c.name}</span>
                              {c.match_score && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">
                                  {c.match_score}%
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-500 line-clamp-1">{c.degree || "—"}</div>
                            <div className="flex justify-between items-center pt-2 border-t border-slate-100 text-[11px]">
                              <span className="text-slate-400">{c.years_experience} yrs exp</span>
                              {c.needs_review && (
                                <span className="text-amber-600 font-bold flex items-center">
                                  <AlertTriangle className="h-3 w-3 mr-1" /> Review
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: FILTER PRESETS VIEW */}
          {activeTab === "presets" && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Saved Filter Presets</h2>
                  <p className="text-xs text-slate-400">Load or manage reusable hiring search presets</p>
                </div>
                <button
                  onClick={() => setPresetModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 flex items-center"
                >
                  <BookmarkPlus className="h-3.5 w-3.5 mr-1" /> Save New Preset
                </button>
              </div>

              <div className="grid grid-cols-3 gap-6">
                {presets.length === 0 ? (
                  <div className="col-span-3 text-center py-12 text-xs text-slate-400 italic bg-white rounded-xl border border-dashed border-slate-200">
                    No presets saved yet. Click "Save Preset" in the top bar to store your active filter criteria.
                  </div>
                ) : (
                  presets.map(p => {
                    let parsedJson = {};
                    try { parsedJson = JSON.parse(p.filters_json); } catch (e) {}
                    return (
                      <div key={p.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
                        <div>
                          <div className="flex justify-between items-start">
                            <h3 className="font-bold text-slate-900 text-sm">{p.name}</h3>
                            <button onClick={() => handleDeletePreset(p.id)} className="text-slate-400 hover:text-rose-600">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                          <div className="text-[11px] text-slate-400 mt-1">
                            Updated {new Date(p.updated_at).toLocaleDateString()}
                          </div>
                          <div className="mt-3 p-3 bg-slate-50 rounded-lg text-xs text-slate-600 space-y-1 font-mono">
                            {parsedJson.whatifFilters?.cgpa && <div>CGPA ≥ {parsedJson.whatifFilters.cgpa}</div>}
                            {parsedJson.whatifFilters?.tenth_pct && <div>10th ≥ {parsedJson.whatifFilters.tenth_pct}%</div>}
                            {parsedJson.whatifFilters?.years_experience && <div>Exp ≥ {parsedJson.whatifFilters.years_experience} yrs</div>}
                            {parsedJson.whatifFilters?.skills?.length > 0 && <div>Skills: {parsedJson.whatifFilters.skills.join(", ")}</div>}
                          </div>
                        </div>

                        <button
                          onClick={() => handleLoadPreset(p)}
                          className="mt-4 w-full py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg text-xs font-bold flex items-center justify-center"
                        >
                          <FolderOpen className="h-3.5 w-3.5 mr-1.5" /> Load Preset
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* TAB 5: REVIEW QUEUE */}
          {activeTab === "reviewQueue" && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Recruiter Confidence Review Queue</h2>
                  <p className="text-xs text-slate-400">Candidates with unverified parsing evidence or missing critical fields</p>
                </div>
                <span className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1.5 rounded-full font-bold">
                  {reviewQueue.length} candidates pending
                </span>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
                    <tr>
                      <th className="px-6 py-3.5">Candidate</th>
                      <th className="px-6 py-3.5">Degree & College</th>
                      <th className="px-6 py-3.5">Flagged Items</th>
                      <th className="px-6 py-3.5">Stage</th>
                      <th className="px-6 py-3.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {reviewQueue.map(c => (
                      <tr key={c.id} className="hover:bg-slate-50">
                        <td className="px-6 py-4 font-bold text-slate-900">{c.name}</td>
                        <td className="px-6 py-4 text-xs">{c.degree || "—"}</td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
                            Confidence Review
                          </span>
                        </td>
                        <td className="px-6 py-4">{getStageBadge(c.pipeline_stage)}</td>
                        <td className="px-6 py-4 text-right">
                          <button onClick={() => openCandidateDrawer(c)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-xs font-bold hover:bg-indigo-700">
                            Review & Verify
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: WHAT-IF FUNNEL */}
          {activeTab === "whatif" && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <h2 className="font-bold text-slate-800 text-base mb-2">Sequential What-If Drop-off</h2>
                <div className="space-y-2">
                  {whatifData?.filters?.map((stage, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 rounded-lg flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-800">{stage.filter}</span>
                      <span className="text-rose-600 font-bold">-{stage.removed} ({stage.after} left)</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: JOB DESCRIPTIONS */}
          {activeTab === "jds" && (
            <div className="grid grid-cols-3 gap-6">
              {jds.map(jd => (
                <div key={jd.id} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                  <h3 className="font-bold text-slate-900 text-base">{jd.title}</h3>
                  <p className="text-xs text-slate-600 mt-2">{jd.description}</p>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* CANDIDATE COMPARISON MODAL */}
      {comparisonModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-8 py-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
                  <Scale className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">Candidate Side-by-Side Comparison</h3>
                  <p className="text-xs text-slate-400">Comparing {comparisonData?.candidates?.length || 0} candidates across normalized metrics</p>
                </div>
              </div>
              <button onClick={() => setComparisonModalOpen(false)} className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              {compareLoading ? (
                <div className="text-center py-20 text-slate-400">Loading comparison metrics...</div>
              ) : comparisonData ? (
                <>
                  {/* Dynamic Verdict Banner */}
                  <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 flex items-start space-x-3">
                    <Sparkles className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">Dynamic Decision Verdict</span>
                      <p className="text-sm font-semibold text-slate-800 mt-0.5">{comparisonData.verdict}</p>
                    </div>
                  </div>

                  {/* Side-by-Side Scorecard Table */}
                  <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                    <table className="w-full text-left text-xs text-slate-700">
                      <thead className="bg-slate-50 border-b border-slate-200 uppercase text-[11px] font-bold text-slate-500">
                        <tr>
                          <th className="px-5 py-3 w-40">Metric / Category</th>
                          {comparisonData.candidates.map(c => (
                            <th key={c.candidate_id} className="px-5 py-3">
                              <div className="font-bold text-slate-900 text-sm">{c.name}</div>
                              <div className="text-[10px] text-slate-400 lowercase">{c.pipeline_stage}</div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {/* JD Match */}
                        <tr>
                          <td className="px-5 py-3 font-bold bg-slate-50/50">JD Match Score</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3 font-extrabold text-sm text-indigo-700">
                              {c.jd_match_score ? `${c.jd_match_score}%` : "—"}
                            </td>
                          ))}
                        </tr>
                        {/* CGPA */}
                        <tr>
                          <td className="px-5 py-3 font-semibold bg-slate-50/50">CGPA (10-Scale)</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3 font-bold">
                              {c.cgpa_10 ?? "—"}
                            </td>
                          ))}
                        </tr>
                        {/* 10th & 12th */}
                        <tr>
                          <td className="px-5 py-3 font-semibold bg-slate-50/50">10th / 12th %</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3">
                              {c.tenth_pct ? `${c.tenth_pct}%` : "—"} / {c.twelfth_pct ? `${c.twelfth_pct}%` : "—"}
                            </td>
                          ))}
                        </tr>
                        {/* Experience */}
                        <tr>
                          <td className="px-5 py-3 font-semibold bg-slate-50/50">Experience</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3 font-medium">
                              {c.years_experience} yrs
                            </td>
                          ))}
                        </tr>
                        {/* Location */}
                        <tr>
                          <td className="px-5 py-3 font-semibold bg-slate-50/50">Location</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3">
                              {c.location || "—"}
                            </td>
                          ))}
                        </tr>
                        {/* Degree & College */}
                        <tr>
                          <td className="px-5 py-3 font-semibold bg-slate-50/50">Education</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3 max-w-xs">
                              <div className="font-medium text-slate-800">{c.degree || "—"}</div>
                              <div className="text-[11px] text-slate-400">{c.college || "—"} ({c.grad_year})</div>
                            </td>
                          ))}
                        </tr>
                        {/* Verification & Confidence */}
                        <tr>
                          <td className="px-5 py-3 font-semibold bg-slate-50/50">Confidence State</td>
                          {comparisonData.candidates.map(c => (
                            <td key={c.candidate_id} className="px-5 py-3">
                              {c.confidence_issues.length > 0 ? (
                                <span className="text-amber-700 bg-amber-50 px-2 py-0.5 rounded text-[11px] font-bold border border-amber-200">
                                  ⚠ {c.confidence_issues.join(", ")}
                                </span>
                              ) : (
                                <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px] font-bold border border-emerald-200">
                                  ✓ Verified
                                </span>
                              )}
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Radar Chart & Skills Breakdown Grid */}
                  <div className="grid grid-cols-2 gap-6">
                    {/* Recharts Radar Chart */}
                    <div className="border border-slate-200 rounded-xl p-5 shadow-2xs flex flex-col items-center">
                      <h4 className="text-xs font-bold uppercase text-slate-700 mb-2">Normalized Radar Comparison (0-100)</h4>
                      <div className="w-full h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart data={comparisonData.radar_data}>
                            <PolarGrid stroke="#e2e8f0" />
                            <PolarAngleAxis dataKey="dimension" stroke="#64748b" tick={{ fontSize: 11 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
                            {comparisonData.candidates.map((c, i) => {
                              const colors = ["#4f46e5", "#059669", "#d97706"];
                              const keyLabel = `${c.name} (#${c.candidate_id})`;
                              return (
                                <Radar
                                  key={c.candidate_id}
                                  name={c.name}
                                  dataKey={keyLabel}
                                  stroke={colors[i % colors.length]}
                                  fill={colors[i % colors.length]}
                                  fillOpacity={0.25}
                                />
                              );
                            })}
                            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Shared vs Unique Skills Details */}
                    <div className="border border-slate-200 rounded-xl p-5 shadow-2xs space-y-4">
                      <div>
                        <h4 className="text-xs font-bold uppercase text-slate-700 mb-2">Shared Skills Across All</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {comparisonData.shared_skills.length > 0 ? (
                            comparisonData.shared_skills.map((s, idx) => (
                              <span key={idx} className="bg-slate-100 text-slate-800 px-2 py-0.5 rounded text-xs font-medium">
                                ✓ {s}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-400 italic">No common skills shared by all selected.</span>
                          )}
                        </div>
                      </div>

                      <div className="border-t border-slate-100 pt-3 space-y-2">
                        <h4 className="text-xs font-bold uppercase text-slate-700">Unique Skills per Candidate</h4>
                        {comparisonData.candidates.map(c => (
                          <div key={c.candidate_id} className="text-xs">
                            <span className="font-bold text-slate-900">{c.name}: </span>
                            {c.unique_skills.length > 0 ? (
                              <span className="text-indigo-600 font-medium">{c.unique_skills.join(", ")}</span>
                            ) : (
                              <span className="text-slate-400 italic">None</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="px-8 py-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={() => setComparisonModalOpen(false)}
                className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                Close Comparison
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SAVE PRESET MODAL */}
      {presetModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-slate-900 text-base">Save Current Filter Preset</h3>
            <p className="text-xs text-slate-500">Save active filters, search criteria, and stage selections for one-click reuse.</p>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Preset Name</label>
              <input
                type="text"
                placeholder="e.g. Senior Full Stack — Bangalore"
                value={presetNameInput}
                onChange={(e) => setPresetNameInput(e.target.value)}
                className="w-full border border-slate-300 rounded-lg p-2 text-xs focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setPresetModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveCurrentAsPreset}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700"
              >
                Save Preset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CANDIDATE PROFILE & EVIDENCE REVIEW DRAWER */}
      {selectedCandidate && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-[580px] bg-white h-full shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-200">
            <div className="p-6 border-b border-slate-200 flex justify-between items-start bg-slate-50">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600">Candidate Dossier</span>
                <h3 className="text-xl font-bold text-slate-900 mt-1">{selectedCandidate.name}</h3>
                <div className="flex items-center space-x-2 mt-2">
                  {getStageBadge(selectedCandidate.pipeline_stage)}
                  <span className="text-xs text-slate-400">ID: #{selectedCandidate.id}</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setEditMode(!editMode)}
                  className="px-2.5 py-1 text-xs font-bold border border-slate-300 rounded-md bg-white hover:bg-slate-50 text-slate-700 flex items-center"
                >
                  <Edit2 className="h-3 w-3 mr-1" /> {editMode ? "Cancel" : "Edit Profile"}
                </button>
                <button onClick={() => setSelectedCandidate(null)} className="text-slate-400 hover:text-slate-600 p-1">
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* DOSSIER SUB-TABS */}
            <div className="px-6 pt-3 border-b border-slate-200 bg-white flex space-x-1">
              <button
                onClick={() => setActiveCandidateDetailTab("overview")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeCandidateDetailTab === "overview"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                Overview & Evidence
              </button>
              <button
                onClick={() => setActiveCandidateDetailTab("intelligence")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeCandidateDetailTab === "intelligence"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                Hiring Intelligence
              </button>
              <button
                onClick={() => setActiveCandidateDetailTab("skillGap")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeCandidateDetailTab === "skillGap"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                Skill Gap
              </button>
              <button
                onClick={() => setActiveCandidateDetailTab("duplicates")}
                className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeCandidateDetailTab === "duplicates"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                Duplicates
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* TAB A: OVERVIEW & EVIDENCE */}
              {activeCandidateDetailTab === "overview" && (
                <>
                  {editMode ? (
                    <div className="bg-indigo-50/50 border border-indigo-200 rounded-xl p-4 space-y-3">
                      <div className="font-bold text-xs uppercase text-indigo-900">Edit Candidate Attributes</div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-[11px] font-semibold text-slate-500">Full Name</label>
                          <input
                            type="text"
                            value={editFormData.name}
                            onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                            className="w-full text-xs border rounded p-1.5 bg-white"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] font-semibold text-slate-500">Location</label>
                          <input
                            type="text"
                            value={editFormData.location}
                            onChange={(e) => setEditFormData({ ...editFormData, location: e.target.value })}
                            className="w-full text-xs border rounded p-1.5 bg-white"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] font-semibold text-slate-500">CGPA (0 - 10)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={editFormData.cgpa_10}
                            onChange={(e) => setEditFormData({ ...editFormData, cgpa_10: e.target.value })}
                            className="w-full text-xs border rounded p-1.5 bg-white"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] font-semibold text-slate-500">Experience (Years)</label>
                          <input
                            type="number"
                            step="0.1"
                            value={editFormData.years_experience}
                            onChange={(e) => setEditFormData({ ...editFormData, years_experience: e.target.value })}
                            className="w-full text-xs border rounded p-1.5 bg-white"
                          />
                        </div>
                      </div>
                      <button
                        onClick={handleSaveProfileEdit}
                        className="w-full mt-2 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 flex items-center justify-center"
                      >
                        <Save className="h-3.5 w-3.5 mr-1" /> Save Changes
                      </button>
                    </div>
                  ) : (
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div><span className="text-slate-400">Email:</span> {blindReviewMode ? "[Hidden]" : (selectedCandidate.email || "—")}</div>
                        <div><span className="text-slate-400">Phone:</span> {blindReviewMode ? "[Hidden]" : (selectedCandidate.phone || "—")}</div>
                        <div><span className="text-slate-400">Location:</span> {selectedCandidate.location || "—"}</div>
                        <div><span className="text-slate-400">Grad Year:</span> {selectedCandidate.grad_year || "—"}</div>
                        <div><span className="text-slate-400">College:</span> {selectedCandidate.college || "—"}</div>
                        <div><span className="text-slate-400">Degree:</span> {selectedCandidate.degree || "—"}</div>
                      </div>
                    </div>
                  )}

                  {/* Parsing Evidence */}
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                      Parsed Evidence & Verification
                    </h4>
                    <div className="space-y-3">
                      {(selectedCandidate.evidence_fields || []).map(ev => (
                        <div key={ev.id} className="border border-slate-200 rounded-lg p-3 bg-white space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-xs font-bold uppercase text-slate-700">{ev.field_name}</span>
                            {renderConfidenceBadge(ev.confidence)}
                          </div>
                          <div className="text-sm font-bold text-slate-900">{ev.value}</div>
                          {!ev.human_verified && (
                            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                              <button
                                onClick={() => handleVerifyEvidence(ev.field_name, ev.value)}
                                className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded text-xs font-bold hover:bg-emerald-100 flex items-center"
                              >
                                <Check className="h-3 w-3 mr-1" /> Confirm
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* TAB B: EVIDENCE-BASED HIRING INTELLIGENCE */}
              {activeCandidateDetailTab === "intelligence" && (
                <div className="space-y-6">
                  {candidateIntelligence ? (
                    <>
                      {/* Evidence Score Header */}
                      <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-900 to-slate-900 text-white flex items-center justify-between">
                        <div>
                          <div className="text-xs font-bold uppercase tracking-wider text-indigo-300">Evidence Strength Score</div>
                          <div className="text-3xl font-extrabold mt-1">{candidateIntelligence.evidence_score}<span className="text-lg font-normal text-slate-400">/100</span></div>
                        </div>
                        <div className="text-right text-xs space-y-1">
                          <div className="text-emerald-400 font-bold">{candidateIntelligence.strong_evidence.length} Strong Claims</div>
                          <div className="text-amber-400 font-bold">{candidateIntelligence.weak_evidence.length} Weak / Need Probing</div>
                          <div className="text-rose-400 font-bold">{candidateIntelligence.missing_evidence.length} Missing Requirements</div>
                        </div>
                      </div>

                      {/* Evidence Items & Interview Probes */}
                      <div className="space-y-4">
                        <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider">
                          Skill Verification & Generated Interview Probes
                        </h4>
                        {candidateIntelligence.evidence_items.map((item, idx) => (
                          <div key={idx} className="border border-slate-200 rounded-xl p-4 bg-white shadow-2xs space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="font-bold text-sm text-slate-900">{item.skill}</span>
                              <div className="flex items-center space-x-2">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                  item.confidence === "HIGH" ? "bg-emerald-100 text-emerald-800" :
                                  item.confidence === "MEDIUM" ? "bg-blue-100 text-blue-800" : "bg-amber-100 text-amber-800"
                                }`}>
                                  {item.confidence} CONFIDENCE
                                </span>
                                <span className="text-xs text-slate-400">({item.source_type})</span>
                              </div>
                            </div>

                            {/* Snippet */}
                            <div className="bg-slate-50 p-2.5 rounded text-xs text-slate-700 italic border border-slate-100">
                              "{item.evidence_snippet}"
                            </div>

                            {/* Interview Probe */}
                            <div className="p-2.5 rounded bg-indigo-50/70 border border-indigo-100 text-xs">
                              <div className="font-bold text-indigo-900 flex items-center mb-1">
                                <HelpCircle className="h-3.5 w-3.5 mr-1 text-indigo-600" />
                                Recommended Interview Probe:
                              </div>
                              <p className="text-indigo-800 font-medium">{item.interview_probe}</p>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Evidence Graph Visual Chain */}
                      <div>
                        <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-3 flex items-center">
                          <Network className="h-3.5 w-3.5 mr-1 text-indigo-600" />
                          Evidence Chain Graph
                        </h4>
                        <div className="space-y-3">
                          {candidateIntelligence.evidence_graph.map((chain, cIdx) => (
                            <div key={cIdx} className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs">
                              <div className="font-bold text-slate-800 mb-2 flex items-center">
                                <span className="h-2 w-2 rounded-full bg-indigo-500 mr-2"></span>
                                {chain.skill} ({chain.status})
                              </div>
                              <div className="flex items-center space-x-2 overflow-x-auto pb-1">
                                {chain.nodes.map((node, nIdx) => (
                                  <React.Fragment key={nIdx}>
                                    <div className="p-2 rounded bg-white border border-slate-200 min-w-[130px] flex-shrink-0">
                                      <div className="text-[10px] uppercase font-bold text-slate-400">{node.label}</div>
                                      <div className="text-xs font-semibold text-slate-800 truncate" title={node.detail}>{node.detail}</div>
                                    </div>
                                    {nIdx < chain.nodes.length - 1 && (
                                      <ArrowRight className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />
                                    )}
                                  </React.Fragment>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 text-slate-400 text-xs">Loading Hiring Intelligence...</div>
                  )}
                </div>
              )}

              {/* TAB C: SKILL GAP INSIGHTS */}
              {activeCandidateDetailTab === "gap" && (
                <div className="space-y-6">
                  {candidateSkillGap ? (
                    <>
                      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-bold uppercase text-slate-500">Required Skills Coverage</span>
                          <span className="text-xl font-extrabold text-indigo-600">{candidateSkillGap.skill_coverage_pct}%</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-3">
                          <div 
                            className="bg-indigo-600 h-3 rounded-full transition-all duration-300"
                            style={{ width: `${candidateSkillGap.skill_coverage_pct}%` }}
                          ></div>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Matched {candidateSkillGap.matched_required.length} of {candidateSkillGap.total_required} required competencies.
                        </div>
                      </div>

                      {/* Matched Required Skills */}
                      <div>
                        <h4 className="text-xs font-bold uppercase text-emerald-600 tracking-wider mb-2 flex items-center">
                          <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                          Matched Required Skills ({candidateSkillGap.matched_required.length})
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {candidateSkillGap.matched_required.map((s, idx) => (
                            <span key={idx} className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md font-bold text-xs">
                              {s} ✓
                            </span>
                          ))}
                          {candidateSkillGap.matched_required.length === 0 && (
                            <span className="text-xs text-slate-400 italic">No required skills matched</span>
                          )}
                        </div>
                      </div>

                      {/* Missing Required Skills */}
                      <div>
                        <h4 className="text-xs font-bold uppercase text-rose-600 tracking-wider mb-2 flex items-center">
                          <AlertTriangle className="h-3.5 w-3.5 mr-1" />
                          Missing Required Skills ({candidateSkillGap.missing_required.length})
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {candidateSkillGap.missing_required.map((s, idx) => (
                            <span key={idx} className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded-md font-bold text-xs">
                              {s} ✗
                            </span>
                          ))}
                          {candidateSkillGap.missing_required.length === 0 && (
                            <span className="text-xs text-emerald-600 font-bold">All required skills are fully satisfied!</span>
                          )}
                        </div>
                      </div>

                      {/* Nice-to-Have Skills */}
                      <div>
                        <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-2">
                          Nice-to-Have Competencies
                        </h4>
                        <div className="flex flex-wrap gap-1.5">
                          {candidateSkillGap.matched_nice.map((s, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded font-semibold text-xs">
                              {s} (Bonus ✓)
                            </span>
                          ))}
                          {candidateSkillGap.missing_nice.map((s, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-500 rounded text-xs">
                              {s} (Missing)
                            </span>
                          ))}
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="text-center py-8 text-slate-400 text-xs">Loading Skill Gap Insights...</div>
                  )}
                </div>
              )}

              {/* TAB D: DUPLICATE RESUME DETECTION */}
              {activeCandidateDetailTab === "duplicates" && (
                <div className="space-y-4">
                  {candidateDuplicates ? (
                    <>
                      <div className={`p-4 rounded-xl border ${
                        candidateDuplicates.has_duplicates ? "bg-amber-50 border-amber-200" : "bg-emerald-50 border-emerald-200"
                      }`}>
                        <div className="flex items-center space-x-2">
                          {candidateDuplicates.has_duplicates ? (
                            <AlertTriangle className="h-4 w-4 text-amber-600" />
                          ) : (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          )}
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                            {candidateDuplicates.has_duplicates
                              ? `Detected ${candidateDuplicates.duplicate_count} Potential Duplicates`
                              : "No Duplicate Profiles Detected"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">
                          Multi-signal comparison across normalized email, phone, name similarity, and resume text overlap.
                        </p>
                      </div>

                      {candidateDuplicates.matches.map((m, idx) => (
                        <div key={idx} className="border border-slate-200 rounded-xl p-4 bg-white shadow-2xs space-y-3">
                          <div className="flex justify-between items-center">
                            <div>
                              <div className="font-bold text-sm text-slate-900">{m.name}</div>
                              <div className="text-xs text-slate-400">Candidate #{m.candidate_id} • {m.email || "No email"}</div>
                            </div>
                            <div className="text-right">
                              <span className={`px-2 py-0.5 rounded text-xs font-extrabold ${
                                m.classification === "EXACT DUPLICATE" ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"
                              }`}>
                                {m.similarity_score}% {m.classification}
                              </span>
                            </div>
                          </div>

                          <div className="bg-slate-50 p-2.5 rounded border border-slate-100 text-xs space-y-1">
                            <span className="font-bold text-slate-500 uppercase text-[10px]">Matching Signals:</span>
                            <ul className="list-disc list-inside text-slate-700">
                              {m.reasons.map((r, rIdx) => (
                                <li key={rIdx}>{r}</li>
                              ))}
                            </ul>
                          </div>

                          <div className="flex space-x-2 pt-2">
                            <button
                              onClick={() => {
                                setSelectedForCompare([selectedCandidate.id, m.candidate_id]);
                                setProfileDrawerOpen(false);
                                setCompareModalOpen(true);
                              }}
                              className="px-3 py-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-bold hover:bg-indigo-100 flex items-center"
                            >
                              <Scale className="h-3 w-3 mr-1" /> Compare Both
                            </button>
                            <button
                              onClick={() => handleMarkDuplicate(selectedCandidate.id, m.candidate_id)}
                              className="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-bold hover:bg-rose-700 flex items-center"
                            >
                              <Copy className="h-3 w-3 mr-1" /> Mark as Duplicate
                            </button>
                          </div>
                        </div>
                      ))}
                    </>
                  ) : (
                    <div className="text-center py-8 text-slate-400 text-xs">Checking duplicate candidates...</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {/* BULK EMAIL SMTP DRY-RUN MODAL */}
      {emailModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="p-6 bg-slate-900 text-white flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold flex items-center">
                  <Send className="h-4 w-4 mr-2 text-emerald-400" />
                  Bulk Email Dispatch Engine
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automate candidate outreach with safe SMTP Dry-Run preview.
                </p>
              </div>
              <button onClick={() => setEmailModalOpen(false)} className="text-slate-400 hover:text-white p-1">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto space-y-5 flex-1 text-xs">
              {/* Security Alert: Dry-Run mode banner */}
              <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start space-x-3">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-bold text-emerald-900">Protected Mode: DRY RUN Active</div>
                  <div className="text-emerald-700 text-[11px] mt-0.5">
                    Messages are fully rendered, personalized, and validated without sending live emails. Credentials are never logged or stored.
                  </div>
                </div>
              </div>

              {/* Form Controls */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-700 font-bold mb-1">Email Template</label>
                  <select
                    value={selectedEmailTemplate}
                    onChange={(e) => setSelectedEmailTemplate(e.target.value)}
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs bg-white"
                  >
                    <option value="interview_invitation">Interview Invitation</option>
                    <option value="shortlist_notification">Shortlist Notification</option>
                    <option value="application_update">Application Update</option>
                    <option value="custom">Custom Recruiter Notice</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 font-bold mb-1">Job Role Title</label>
                  <input
                    type="text"
                    value={emailRole}
                    onChange={(e) => setEmailRole(e.target.value)}
                    className="w-full border border-slate-300 rounded-lg p-2 text-xs bg-white"
                    placeholder="e.g. Full Stack Engineer"
                  />
                </div>
              </div>

              {/* Candidates in queue preview */}
              <div>
                <div className="font-bold text-slate-800 mb-1.5 flex justify-between">
                  <span>Recipients in Dispatch Batch</span>
                  <span className="text-indigo-600 font-extrabold">
                    {selectedForCompare.length > 0 ? `${selectedForCompare.length} Selected Candidates` : "Top 5 Candidates Preview"}
                  </span>
                </div>
                <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-600 text-[11px]">
                  {selectedForCompare.length > 0
                    ? `Dispatching to selected candidate IDs: ${selectedForCompare.join(", ")}`
                    : "No specific candidates checked. Preparing preview for top 5 directory candidates."}
                </div>
              </div>

              {/* Output Preview */}
              {emailQueueResult && (
                <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-800">Generated Email Queue ({emailQueueResult.total_queued})</span>
                    <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-bold text-[10px]">
                      {emailQueueResult.mode} MODE
                    </span>
                  </div>

                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {emailQueueResult.queue.map((item, idx) => (
                      <div key={idx} className="p-3 bg-white border border-slate-200 rounded-lg space-y-1">
                        <div className="flex justify-between font-bold text-slate-800">
                          <span>To: {item.candidate_name} &lt;{item.to_email}&gt;</span>
                          <span className="text-[10px] text-emerald-600">{item.status}</span>
                        </div>
                        <div className="text-[11px] font-semibold text-indigo-700">Subject: {item.subject}</div>
                        <pre className="text-[10px] text-slate-600 whitespace-pre-wrap font-sans bg-slate-50 p-2 rounded border border-slate-100 mt-1">
                          {item.body}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end space-x-3">
              <button
                onClick={() => setEmailModalOpen(false)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-100"
              >
                Close
              </button>
              <button
                onClick={handleSendBulkEmail}
                disabled={emailLoading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 flex items-center shadow-xs"
              >
                <Send className="h-3.5 w-3.5 mr-1.5" />
                {emailLoading ? "Generating Queue..." : "Generate Dry-Run Queue"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
