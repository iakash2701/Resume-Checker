with open("frontend/src/App.jsx", "r", encoding="utf-8") as f:
    text = f.read()

# Add Bulk Email Modal just before the closing </div> of the app
modal_markup = """      {/* BULK EMAIL SMTP DRY-RUN MODAL */}
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
}"""

old_footer = """    </div>
  );
}"""

if "BULK EMAIL SMTP DRY-RUN MODAL" not in text:
    text = text.replace(old_footer, modal_markup, 1)

with open("frontend/src/App.jsx", "w", encoding="utf-8") as f:
    f.write(text)

print("Injected Bulk Email Modal successfully!")
