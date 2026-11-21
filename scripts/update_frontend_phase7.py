import os

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update lucide-react imports
if "EyeOff" not in text:
    text = text.replace("  Users,", "  EyeOff,\n  Copy,\n  Send,\n  Zap,\n  Network,\n  HelpCircle,\n  Users,", 1)

# 2. Add state hooks for Phase 7
old_state = "  const [selectedCandidate, setSelectedCandidate] = useState(null);"
new_state = """  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [blindReviewMode, setBlindReviewMode] = useState(false);
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
  const [emailLoading, setEmailLoading] = useState(false);"""

if "blindReviewMode" not in text:
    text = text.replace(old_state, new_state, 1)

# 3. Add fetching methods for duplicates, skill gap, and intelligence when opening candidate
old_select_cand = """  const handleCandidateClick = (cand) => {
    setSelectedCandidate(cand);
    setProfileDrawerOpen(true);
    setEditMode(false);
    fetchAuditHistory(cand.id);
  };"""

new_select_cand = """  const handleCandidateClick = (cand) => {
    setSelectedCandidate(cand);
    setProfileDrawerOpen(true);
    setEditMode(false);
    setActiveCandidateDetailTab("overview");
    fetchAuditHistory(cand.id);
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
        if (selectedCandidate) fetchAuditHistory(selectedCandidate.id);
        alert(`Candidate marked as duplicate successfully.`);
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
        : candidates.slice(0, 5); // default preview first 5
        
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
  };"""

if "fetchCandidateDuplicates" not in text:
    text = text.replace(old_select_cand, new_select_cand, 1)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated App.jsx with phase 7 handler functions successfully!")
