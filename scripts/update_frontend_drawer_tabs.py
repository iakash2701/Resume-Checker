with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# Target the inner drawer content
drawer_header_target = """              <div>
                <h3 className="text-base font-bold text-slate-900">{selectedCandidate.name}</h3>
                <p className="text-xs text-slate-500">ID #{selectedCandidate.id} • {selectedCandidate.pipeline_stage}</p>
              </div>"""

drawer_header_replacement = """              <div>
                <h3 className="text-base font-bold text-slate-900">
                  {blindReviewMode ? `Candidate #${selectedCandidate.id} [Protected Review]` : selectedCandidate.name}
                </h3>
                <p className="text-xs text-slate-500">
                  ID #{selectedCandidate.id} • Stage: <span className="font-semibold text-indigo-600">{selectedCandidate.pipeline_stage}</span>
                  {selectedCandidate.is_duplicate && (
                    <span className="ml-2 px-1.5 py-0.5 bg-rose-100 text-rose-800 rounded font-bold text-[10px]">
                      Duplicate of #{selectedCandidate.duplicate_of_id}
                    </span>
                  )}
                </p>
              </div>"""

if "Protected Review" not in text:
    text = text.replace(drawer_header_target, drawer_header_replacement, 1)

# Add sub-navigation tabs in the candidate drawer: Overview, Hiring Intelligence, Skill Gap, Duplicates
drawer_nav_target = """            <div className="flex-1 overflow-y-auto p-6 space-y-6">"""

drawer_nav_replacement = """            {/* Sub-tabs in Candidate Drawer */}
            <div className="flex border-b border-slate-200 px-6 pt-2 bg-white">
              <button
                onClick={() => setActiveCandidateDetailTab("overview")}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors ${
                  activeCandidateDetailTab === "overview"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                Overview & Evidence
              </button>
              <button
                onClick={() => setActiveCandidateDetailTab("intelligence")}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center ${
                  activeCandidateDetailTab === "intelligence"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                <Zap className="h-3.5 w-3.5 mr-1 text-amber-500" />
                Hiring Intelligence
              </button>
              <button
                onClick={() => setActiveCandidateDetailTab("gap")}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center ${
                  activeCandidateDetailTab === "gap"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                <Sparkles className="h-3.5 w-3.5 mr-1 text-indigo-500" />
                Skill Gap
              </button>
              <button
                onClick={() => setActiveCandidateDetailTab("duplicates")}
                className={`pb-2.5 px-3 text-xs font-bold border-b-2 transition-colors flex items-center relative ${
                  activeCandidateDetailTab === "duplicates"
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                <Copy className="h-3.5 w-3.5 mr-1 text-rose-500" />
                Duplicates
                {candidateDuplicates && candidateDuplicates.matches && candidateDuplicates.matches.length > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.2 bg-rose-500 text-white rounded-full text-[10px] font-extrabold">
                    {candidateDuplicates.matches.length}
                  </span>
                )}
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">"""

if "activeCandidateDetailTab" not in text:
    text = text.replace(drawer_nav_target, drawer_nav_replacement, 1)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated drawer headers and sub-tabs!")
