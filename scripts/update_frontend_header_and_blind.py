with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add Blind Review Toggle & Bulk Email button to header action bar
old_header_actions = """            {/* Save Filter Preset button */}
            <button
              onClick={() => setPresetModalOpen(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 flex items-center shadow-2xs"
            >
              <BookmarkPlus className="h-3.5 w-3.5 mr-1.5 text-cyan-600" />
              Save Preset
            </button>"""

new_header_actions = """            {/* Bulk Email Dry-Run button */}
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
            </button>"""

if "Blind Review Mode" not in text:
    text = text.replace(old_header_actions, new_header_actions, 1)

# 2. In candidate directory table, honor Blind Review mode for Name, Email, Phone
old_candidate_table_row = """                        <div className="font-semibold text-slate-900">{c.name}</div>
                        <div className="text-[11px] text-slate-400">{c.email || "No email"}</div>"""

new_candidate_table_row = """                        <div className="font-semibold text-slate-900">
                          {blindReviewMode ? `Candidate #${c.id} [Protected]` : c.name}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {blindReviewMode ? "Identity protected in Blind Review" : (c.email || "No email")}
                        </div>"""

if "Candidate #[Protected]" not in text:
    text = text.replace(old_candidate_table_row, new_candidate_table_row, 1)

# 3. In Kanban board, honor Blind Review mode
old_kanban_card_name = """                    <h4 className="text-xs font-bold text-slate-900">{cand.name}</h4>"""
new_kanban_card_name = """                    <h4 className="text-xs font-bold text-slate-900">
                      {blindReviewMode ? `Candidate #${cand.id}` : cand.name}
                    </h4>"""

if "blindReviewMode ? `Candidate #${cand.id}`" not in text:
    text = text.replace(old_kanban_card_name, new_kanban_card_name, 1)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Injected Blind Review and Bulk Email buttons into header and tables!")
