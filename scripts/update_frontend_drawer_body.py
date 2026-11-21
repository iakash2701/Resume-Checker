with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# Replace the inner body of the drawer to conditionally render based on activeCandidateDetailTab
old_drawer_body = """            <div className="flex-1 overflow-y-auto p-6 space-y-6">
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
                    <div><span className="text-slate-400">Email:</span> {selectedCandidate.email || "—"}</div>
                    <div><span className="text-slate-400">Phone:</span> {selectedCandidate.phone || "—"}</div>
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
            </div>"""

new_drawer_body = """            <div className="flex-1 overflow-y-auto p-6 space-y-6">
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
            </div>"""

if "activeCandidateDetailTab === \"overview\"" not in text:
    text = text.replace(old_drawer_body, new_drawer_body, 1)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated drawer body with all 4 Phase 7 sub-tabs!")
