$path = 'src\pages\POS.jsx'
$abs = (Resolve-Path $path).Path
Copy-Item $abs "$abs.bakpaydlg" -Force

$enc = New-Object System.Text.UTF8Encoding $false
$t = [System.IO.File]::ReadAllText($abs, [System.Text.Encoding]::UTF8)

# 1) Add lucide icons (Sparkles, Wallet, Zap, ArrowRight)
$oldImp = 'Banknote,'
$newImp = 'Banknote, Sparkles, Wallet, Zap, ArrowRight,'
if ($t.IndexOf($newImp) -lt 0) {
    $cnt = ([regex]::Matches($t, [regex]::Escape($oldImp))).Count
    Write-Host ("Import: {0}x" -f $cnt)
    $t = $t.Replace($oldImp, $newImp)
} else {
    Write-Host "Import: tashme i shtuar"
}

# 2) Replace whole Payment Dialog block
$startMarker = '{/* Payment Dialog */}'
$endMarker = '{/* Product Search Dialog */}'
$startIdx = $t.IndexOf($startMarker)
if ($startIdx -lt 0) { throw "Start marker not found" }
$endIdx = $t.IndexOf($endMarker, $startIdx)
if ($endIdx -lt 0) { throw "End marker not found" }

$newDialog = @'
{/* Payment Dialog */}
      <Dialog open={showPayment} onOpenChange={setShowPayment}>
        <DialogContent className="sm:max-w-md p-0 overflow-hidden border-0 bg-transparent shadow-none">
          <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 border border-white/10 shadow-2xl shadow-black/40">
            <div aria-hidden="true" className="pointer-events-none absolute -top-24 -left-24 w-64 h-64 rounded-full bg-[#00a79d]/30 blur-3xl animate-pulse"></div>
            <div aria-hidden="true" className="pointer-events-none absolute -bottom-24 -right-24 w-72 h-72 rounded-full bg-cyan-500/25 blur-3xl animate-pulse" style= animationDelay: '1s' ></div>
            <div aria-hidden="true" className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-emerald-500/10 blur-3xl"></div>
            <div aria-hidden="true" className="pointer-events-none absolute inset-0 opacity-[0.04]" style= backgroundImage: 'linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)', backgroundSize: '24px 24px' ></div>

            <div className="relative p-6 space-y-5">
              <DialogHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                  <div className="relative h-10 w-10 rounded-2xl bg-gradient-to-br from-[#00a79d] to-cyan-400 flex items-center justify-center shadow-lg shadow-[#00a79d]/40">
                    <Sparkles className="h-5 w-5 text-white relative z-10" />
                    <span aria-hidden="true" className="absolute inset-0 rounded-2xl bg-white/20 blur-md"></span>
                  </div>
                  <div className="text-left">
                    <DialogTitle className="text-base font-bold text-white tracking-tight m-0">{'P\u00EBrfundimi i Pages\u00EBs'}</DialogTitle>
                    <p className="text-[10px] text-cyan-300/80 uppercase tracking-[0.2em] font-semibold mt-0.5">AI-powered checkout</p>
                  </div>
                </div>
                <button type="button" onClick={() => setShowPayment(false)} className="h-9 w-9 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 hover:text-white flex items-center justify-center transition">
                  <X className="h-4 w-4" />
                </button>
              </DialogHeader>

              <div className="relative rounded-2xl bg-gradient-to-br from-white/[0.08] to-white/[0.02] border border-white/10 p-5 text-center backdrop-blur-xl">
                <div className="text-[10px] uppercase tracking-[0.3em] text-cyan-300/70 font-semibold mb-1">{'Totali p\u00EBr Pages\u00EB'}</div>
                <div className="text-5xl font-extrabold tabular-nums text-transparent bg-clip-text bg-gradient-to-br from-white via-cyan-100 to-[#00a79d] drop-shadow-[0_0_20px_rgba(0,167,157,0.4)]">{`\u20AC${cartTotals.total.toFixed(2)}`}</div>
                <Zap className="absolute top-3 right-3 h-4 w-4 text-cyan-300/60" />
              </div>

              <div className="grid grid-cols-2 gap-2 p-1 rounded-2xl bg-white/[0.04] border border-white/10">
                <button type="button" onClick={() => setPaymentMethod('cash')} data-testid="payment-cash-btn" className={`relative h-11 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm transition-all ${paymentMethod === 'cash' ? 'bg-gradient-to-br from-[#00a79d] to-cyan-500 text-white shadow-lg shadow-[#00a79d]/40' : 'text-white/60 hover:text-white/90'}`}>
                  <Banknote className="h-4 w-4" /> Cash
                </button>
                <button type="button" onClick={() => setPaymentMethod('bank')} data-testid="payment-bank-btn" className={`relative h-11 rounded-xl flex items-center justify-center gap-2 font-semibold text-sm transition-all ${paymentMethod === 'bank' ? 'bg-gradient-to-br from-[#00a79d] to-cyan-500 text-white shadow-lg shadow-[#00a79d]/40' : 'text-white/60 hover:text-white/90'}`}>
                  <CreditCard className="h-4 w-4" /> Bank
                </button>
              </div>

              {paymentMethod === 'cash' && (
                <div className="space-y-4">
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-300 font-bold text-lg pointer-events-none">{'\u20AC'}</span>
                    <input
                      ref={cashInputRef}
                      type="text"
                      value={cashAmount}
                      onChange={(e) => setCashAmount(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter' && parseFloat(cashAmount) >= cartTotals.total) { e.preventDefault(); handlePayment(); } }}
                      placeholder={'Shkruaj shum\u00EBn e paguar...'}
                      autoFocus
                      data-testid="cash-amount-input"
                      className="w-full h-14 pl-10 pr-4 rounded-2xl bg-white/[0.05] border border-white/10 text-white text-xl font-bold tabular-nums placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-cyan-400/60 focus:border-cyan-400/40 transition"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div className="rounded-xl bg-white/[0.04] border border-white/10 p-3">
                      <div className="text-[9px] uppercase tracking-widest text-white/50 font-semibold">Total</div>
                      <div className="text-base font-bold text-white tabular-nums mt-0.5">{`\u20AC${cartTotals.total.toFixed(2)}`}</div>
                    </div>
                    <div className="rounded-xl bg-white/[0.04] border border-white/10 p-3">
                      <div className="text-[9px] uppercase tracking-widest text-white/50 font-semibold">Paguar</div>
                      <div className="text-base font-bold text-cyan-300 tabular-nums mt-0.5">{`\u20AC${(parseFloat(cashAmount) || 0).toFixed(2)}`}</div>
                    </div>
                    <div className={`rounded-xl border p-3 transition ${changeAmount > 0 ? 'bg-emerald-500/15 border-emerald-400/40 shadow-lg shadow-emerald-500/20' : 'bg-white/[0.04] border-white/10'}`}>
                      <div className="text-[9px] uppercase tracking-widest text-white/50 font-semibold">Kusuri</div>
                      <div className={`text-base font-bold tabular-nums mt-0.5 ${changeAmount > 0 ? 'text-emerald-300' : 'text-white/70'}`}>{`\u20AC${changeAmount.toFixed(2)}`}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {['7','8','9','4','5','6','1','2','3','.','0'].map((num) => (
                      <button key={num} type="button" onClick={() => handleNumpad(num)} className="h-12 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] border border-white/10 text-white text-lg font-bold tabular-nums transition active:scale-95">
                        {num}
                      </button>
                    ))}
                    <button type="button" onClick={() => handleNumpad('backspace')} className="h-12 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-400/30 text-rose-300 transition active:scale-95 flex items-center justify-center">
                      <Delete className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              )}

              {paymentMethod === 'bank' && (
                <div className="rounded-2xl bg-gradient-to-br from-cyan-500/10 to-[#00a79d]/10 border border-cyan-400/20 p-6 text-center">
                  <CreditCard className="h-8 w-8 mx-auto text-cyan-300 mb-2" />
                  <p className="text-xs uppercase tracking-widest text-cyan-300/80 font-semibold mb-1">{'Pagesa me Kart\u00EB / Bank'}</p>
                  <p className="text-3xl font-extrabold text-white tabular-nums">{`\u20AC${cartTotals.total.toFixed(2)}`}</p>
                </div>
              )}

              <div className="space-y-2">
                <button type="button" onClick={() => setPrintReceipt(!printReceipt)} data-testid="print-receipt-checkbox" className={`w-full flex items-center gap-3 p-3 rounded-2xl border transition ${printReceipt ? 'bg-cyan-500/10 border-cyan-400/30' : 'bg-white/[0.04] border-white/10 hover:bg-white/[0.06]'}`}>
                  <div className={`relative h-5 w-9 rounded-full transition ${printReceipt ? 'bg-cyan-400' : 'bg-white/20'}`}>
                    <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${printReceipt ? 'left-4' : 'left-0.5'}`}></div>
                  </div>
                  <span className={`text-sm font-medium flex-1 text-left ${printReceipt ? 'text-cyan-200' : 'text-white/70'}`}>{'Shtyp kupon p\u00EBr klientin'}</span>
                  <Printer className={`h-4 w-4 ${printReceipt ? 'text-cyan-300' : 'text-white/40'}`} />
                </button>

                <button type="button" onClick={() => { const next = !isDebt; setIsDebt(next); if (!next) setDebtorName(''); }} data-testid="debt-checkbox" className={`w-full flex items-center gap-3 p-3 rounded-2xl border transition ${isDebt ? 'bg-amber-500/10 border-amber-400/40' : 'bg-white/[0.04] border-white/10 hover:bg-white/[0.06]'}`}>
                  <div className={`relative h-5 w-9 rounded-full transition ${isDebt ? 'bg-amber-400' : 'bg-white/20'}`}>
                    <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${isDebt ? 'left-4' : 'left-0.5'}`}></div>
                  </div>
                  <span className={`text-sm font-medium flex-1 text-left ${isDebt ? 'text-amber-200' : 'text-white/70'}`}>Borgj (Shitje me Borxh)</span>
                  <Wallet className={`h-4 w-4 ${isDebt ? 'text-amber-300' : 'text-white/40'}`} />
                </button>

                {isDebt && (
                  <div className="rounded-2xl bg-amber-500/5 border border-amber-400/30 p-4 space-y-3">
                    <div>
                      <label className="text-[10px] font-bold text-amber-200 uppercase tracking-wider">Emri i Debitorit <span className="text-rose-400">*</span></label>
                      <input type="text" value={debtorName} onChange={(e) => setDebtorName(e.target.value)} placeholder="Shkruaj emrin e debitorit..." autoFocus data-testid="debtor-name-input" className="mt-1.5 w-full h-10 px-3 rounded-xl bg-white/[0.06] border border-amber-400/30 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-amber-400/50 transition" />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-amber-200 uppercase tracking-wider">Paguar Tani (opsional)</label>
                      <div className="relative mt-1.5">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-amber-300 font-bold pointer-events-none">{'\u20AC'}</span>
                        <input type="number" step="0.01" min="0" max={cartTotals.total} value={cashAmount} onChange={(e) => setCashAmount(e.target.value)} placeholder="0.00" data-testid="debt-paid-amount-input" className="w-full h-10 pl-8 pr-3 rounded-xl bg-white/[0.06] border border-amber-400/30 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-amber-400/50 transition" />
                      </div>
                    </div>
                    <div className="rounded-xl bg-white/[0.04] border border-amber-400/20 p-3 space-y-1.5">
                      <div className="flex justify-between text-xs"><span className="text-white/60">Total Fatura:</span><span className="font-bold text-white tabular-nums">{`\u20AC${cartTotals.total.toFixed(2)}`}</span></div>
                      <div className="flex justify-between text-xs"><span className="text-white/60">Paguar Tani:</span><span className="font-bold text-emerald-300 tabular-nums">{`\u20AC${(parseFloat(cashAmount) || 0).toFixed(2)}`}</span></div>
                      <div className="flex justify-between text-sm font-bold border-t border-amber-400/20 pt-1.5 mt-1"><span className="text-amber-200">Borgj i Mbetur:</span><span className="text-amber-300 tabular-nums">{`\u20AC${Math.max(0, cartTotals.total - (parseFloat(cashAmount) || 0)).toFixed(2)}`}</span></div>
                    </div>
                  </div>
                )}

                {printReceipt && !isDebt && (
                  <div className="rounded-2xl bg-white/[0.04] border border-white/10 p-3">
                    <label className="text-[10px] font-bold text-white/70 uppercase tracking-wider">Emri i Klientit (opsional)</label>
                    <input type="text" value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Shkruaj emrin e klientit..." data-testid="receipt-customer-name-input" className="mt-1.5 w-full h-9 px-3 rounded-xl bg-white/[0.06] border border-white/10 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-cyan-400/40 transition" />
                  </div>
                )}

                {printReceipt && !isDebt && (
                  <button type="button" onClick={() => toggleDirectPrint(!directPrintEnabled)} data-testid="direct-print-checkbox" className={`w-full flex items-center gap-3 p-3 rounded-2xl border transition ${directPrintEnabled ? 'bg-blue-500/10 border-blue-400/30' : 'bg-white/[0.04] border-white/10'}`}>
                    <div className={`relative h-5 w-9 rounded-full transition ${directPrintEnabled ? 'bg-blue-400' : 'bg-white/20'}`}>
                      <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all ${directPrintEnabled ? 'left-4' : 'left-0.5'}`}></div>
                    </div>
                    <span className={`text-sm font-medium flex-1 text-left ${directPrintEnabled ? 'text-blue-200' : 'text-white/70'}`}>Printim direkt (pa parapamje)</span>
                  </button>
                )}
              </div>

              <button type="button" onClick={handlePayment} disabled={isDebt && !debtorName.trim()} data-testid="confirm-payment-btn" className={`group relative w-full h-14 rounded-2xl font-bold text-base text-white shadow-2xl transition-all overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01] active:scale-[0.99] ${isDebt ? 'bg-gradient-to-br from-amber-500 to-orange-500 shadow-amber-500/40 hover:shadow-amber-500/60' : 'bg-gradient-to-br from-[#00a79d] via-cyan-500 to-emerald-500 shadow-[#00a79d]/40 hover:shadow-[#00a79d]/60'}`}>
                <span aria-hidden="true" className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out"></span>
                <span className="relative flex items-center justify-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  {isDebt ? 'Regjistro Borgj' : (printReceipt ? 'Shtyp & P\u00EBrfundo' : 'P\u00EBrfundo pa Shtypur')}
                  <ArrowRight className="h-4 w-4" />
                </span>
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      
'@

$before = $t.Substring(0, $startIdx)
$after = $t.Substring($endIdx)
$t = $before + $newDialog + $after

[System.IO.File]::WriteAllText($abs, $t, $enc)
Write-Host "OK: Payment Dialog u redizajnua (AI-futuristic)" -ForegroundColor Green