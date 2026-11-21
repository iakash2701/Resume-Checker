import os

with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Target lines: "  const openCandidateDrawer = async (cand) => {" around line 351
target_idx = -1
for i, l in enumerate(lines):
    if "const openCandidateDrawer = async (cand) => {" in l:
        target_idx = i
        break

print("Found openCandidateDrawer at line:", target_idx)

# Find closing brace of openCandidateDrawer
close_idx = -1
for j in range(target_idx, target_idx + 35):
    if lines[j].strip() == "};":
        close_idx = j
        break

print("Found closing brace at line:", close_idx)

new_code = """  const openCandidateDrawer = async (cand) => {
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
"""

lines[target_idx:close_idx+1] = [new_code]

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Replacement complete!")
