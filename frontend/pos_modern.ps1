$ErrorActionPreference = "Stop"
$target = "C:/Users/urim5/Desktop/datapos12-main/frontend/src/pages/POS.jsx"
$utf8 = New-Object System.Text.UTF8Encoding $false

Copy-Item $target "$target.backup" -Force
Write-Host "Backup u krijua: POS.jsx.backup" -ForegroundColor Yellow

$content = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)

$startMarker = "const posContent = ("
$endMarker = "<Dialog open={showPayment}"
$startIdx = $content.IndexOf($startMarker)
$endIdx = $content.IndexOf($endMarker)

if ($startIdx -lt 0 -or $endIdx -lt 0 -or $endIdx -le $startIdx) {
  Write-Host "GABIM: nuk u gjeten anchor-et. Asgje nuk u ndryshua." -ForegroundColor Red
  return
}

$newBlock = @'
const posContent = (
    <div
      className={`${isCashierFullscreen ? 'h-[calc(100vh-5rem)]' : 'h-[calc(100vh-8rem)]'} flex flex-col lg:flex-row gap-3 ${responsiveClasses.container}`}
      style={{
        fontSize: `calc(1rem * ${scale})`,
        '--dynamic-scale': scale
      }}
      data-testid="pos-page"
    >
      {/* Left Side - Product Search & Cart */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header with search */}
        <div className="flex items-center gap-3 mb-3 lg:mb-4">
          <div className="hidden sm:flex items-center gap-2.5 px-3 py-2 rounded-2xl bg-white/70 backdrop-blur-md border border-gray-200/60 shadow-sm">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#00a79d] to-[#007a73] flex items-center justify-center text-white text-sm font-semibold">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden md:flex flex-col leading-tight">
              <span className="text-xs font-semibold text-gray-800">{user?.full_name}</span>
              <span className="text-[10px] text-gray-400">{currentTime.toLocaleTimeString('sq-AL', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>

          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#00a79d]" />
            <Input
              ref={searchRef}
              type="text"
              placeholder={'K\u00EBrko produkt ose skano barkod...'}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setShowSearchResults(e.target.value.trim().length > 0);
              }}
              onFocus={() => search.trim() && setShowSearchResults(true)}
              onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
              className="pl-12 h-12 text-base rounded-2xl border-gray-200/80 bg-white/80 backdrop-blur-md shadow-sm focus-visible:ring-2 focus-visible:ring-[#00a79d]/40 focus-visible:border-[#00a79d]"
              data-testid="pos-search-input"
            />

            {showSearchResults && mainSearchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white/95 backdrop-blur-xl border border-gray-200/70 rounded-2xl shadow-xl z-50 max-h-72 overflow-auto p-1.5">
                {mainSearchResults.map((product) => (
                  <div
                    key={product.id}
                    className={`p-3 rounded-xl cursor-pointer transition-colors ${product.current_stock > 0 ? 'hover:bg-[#00a79d]/10' : 'bg-gray-50 opacity-70'}`}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      addToCart(product);
                    }}
                  >
                    <div className="flex justify-between items-center gap-3">
                      <div className="min-w-0">
                        <p className="font-semibold text-gray-900 truncate">{product.name || 'Pa em\u00EBr'}</p>
                        <p className="text-xs text-gray-400">Barkod: {product.barcode || '-'}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="font-bold text-[#00a79d]">{`\u20AC${(product.sale_price || 0).toFixed(2)}`}</p>
                        <p className={`text-xs ${product.current_stock > 0 ? 'text-emerald-600' : 'text-red-500 font-semibold'}`}>
                          {product.current_stock > 0 ? `Stok: ${product.current_stock}` : 'Pa stok!'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {showSearchResults && search.trim() && mainSearchResults.length === 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white/95 backdrop-blur-xl border border-gray-200/70 rounded-2xl shadow-xl z-50 p-4 text-center text-gray-500">
                {`Nuk u gjet asnj\u00EB produkt p\u00EBr "${search}"`}
              </div>
            )}
          </div>
          {customerName && (
            <div className="flex items-center gap-2 px-3 py-2 bg-[#00a79d]/10 rounded-2xl border border-[#00a79d]/20">
              <User className="h-4 w-4 text-[#00a79d]" />
              <span className="text-sm font-semibold text-[#00a79d]">{customerName}</span>
            </div>
          )}
        </div>

        {/* Cart Table */}
        <Card className="flex-1 border border-gray-200/60 rounded-3xl shadow-sm overflow-hidden bg-white/80 backdrop-blur-md flex flex-col">
          <div className="bg-gradient-to-r from-[#00a79d]/15 to-[#00c4b8]/10 px-4 py-3 border-b border-[#00a79d]/15">
            <div className="grid grid-cols-12 gap-2 text-[11px] font-bold text-gray-600 uppercase tracking-wide">
              <div className="col-span-1">Nr</div>
              <div className="col-span-3">{'Em\u00EBrtimi'}</div>
              <div className="col-span-1 text-center">Sasia</div>
              <div className="col-span-2 text-right">{'\u00C7mimi'}</div>
              <div className="col-span-1 text-center">Zbritja %</div>
              <div className="col-span-1 text-center">Tvsh %</div>
              <div className="col-span-2 text-right">{'\u00C7mimi me tvsh'}</div>
              <div className="col-span-1 text-right">Total</div>
            </div>
          </div>
          <div className="overflow-auto flex-1" style= maxHeight: 'calc(100vh - 24rem)' >
            <Table>
              <TableBody>
                {cart.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={12} className="text-center py-16 text-gray-400">
                      <div className="h-16 w-16 mx-auto mb-3 rounded-2xl bg-gray-100 flex items-center justify-center">
                        <Package className="h-8 w-8 opacity-40" />
                      </div>
                      <p className="font-medium">{'Shtoni produkte n\u00EB shport\u00EB'}</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  cart.map((item, index) => {
                    const { subtotal, total } = calculateItemTotal(item);
                    const canEdit = user?.role === 'admin' || user?.role === 'manager';
                    return (
                      <TableRow
                        key={item.product_id}
                        className={`cursor-pointer transition-colors ${selectedItemIndex === index ? 'bg-[#00a79d]/10' : 'hover:bg-gray-50'}`}
                        onClick={() => setSelectedItemIndex(index)}
                      >
                        <TableCell className="w-12 text-gray-400 font-medium">{index + 1}</TableCell>
                        <TableCell>
                          {canEdit ? (
                            <Select
                              value={item.product_id}
                              onValueChange={(value) => {
                                const product = products.find(p => p.id === value);
                                if (product) {
                                  setCart(prev => prev.map((it, i) =>
                                    i === index ? {
                                      ...it,
                                      product_id: product.id,
                                      product_name: product.name,
                                      unit_price: product.sale_price || 0,
                                      vat_percent: applyNoVat ? 0 : (product.vat_rate || 0),
                                      max_stock: product.current_stock
                                    } : it
                                  ));
                                }
                              }}
                            >
                              <SelectTrigger className="border-gray-200 rounded-xl">
                                <SelectValue>{item.product_name || 'Zgjidh'}</SelectValue>
                              </SelectTrigger>
                              <SelectContent>
                                {products.filter(p => p.current_stock > 0).map(p => (
                                  <SelectItem key={p.id} value={p.id}>
                                    {p.name || p.barcode || p.id}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          ) : (
                            <span className="font-semibold text-gray-800">{item.product_name || 'Produkt'}</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 rounded-lg hover:bg-[#00a79d]/10 hover:text-[#00a79d]"
                              onClick={(e) => { e.stopPropagation(); updateQuantity(item.product_id, -1); }}
                            >
                              <Minus className="h-3 w-3" />
                            </Button>
                            <span className="w-8 text-center font-bold text-gray-800">{item.quantity}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 rounded-lg hover:bg-[#00a79d]/10 hover:text-[#00a79d]"
                              onClick={(e) => { e.stopPropagation(); updateQuantity(item.product_id, 1); }}
                            >
                              <Plus className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-gray-600">{`\u20AC${item.unit_price.toFixed(2)}`}</TableCell>
                        <TableCell>
                          {canEdit ? (
                            <Input
                              type="number"
                              min="0"
                              max="100"
                              value={item.discount_percent}
                              onChange={(e) => updateDiscount(item.product_id, e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-16 h-8 text-center rounded-lg"
                            />
                          ) : (
                            <span className="text-center">{item.discount_percent}%</span>
                          )}
                        </TableCell>
                        <TableCell className="text-center text-gray-600">{item.vat_percent}</TableCell>
                        <TableCell className="text-right text-gray-600">{`\u20AC${(item.unit_price * (1 + item.vat_percent / 100)).toFixed(2)}`}</TableCell>
                        <TableCell className="text-right font-bold text-gray-900">{`\u20AC${total.toFixed(2)}`}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 rounded-lg text-red-400 hover:text-red-600 hover:bg-red-50"
                            onClick={(e) => { e.stopPropagation(); removeFromCart(item.product_id); }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Cart Totals */}
          <div className="border-t border-[#00a79d]/15 bg-gradient-to-r from-[#00a79d] to-[#007a73] p-4">
            <div className="flex justify-between items-center gap-4 flex-wrap">
              <div className="flex gap-5 text-sm text-white/85">
                <span>Subtotal: <span className="font-semibold text-white">{`\u20AC${cartTotals.subtotal.toFixed(2)}`}</span></span>
                <span>Zbritja: <span className="font-semibold text-amber-200">{`-\u20AC${cartTotals.discount.toFixed(2)}`}</span></span>
                <span>TVSH: <span className="font-semibold text-white">{`\u20AC${cartTotals.vat.toFixed(2)}`}</span></span>
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-widest text-white/70 font-semibold">Totali</div>
                <div className="text-4xl font-extrabold text-white leading-none">{`\u20AC${cartTotals.total.toFixed(2)}`}</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Right Side - Action Buttons */}
      <div className="w-full lg:w-52 flex flex-row lg:flex-col gap-2 flex-wrap lg:flex-nowrap lg:overflow-y-auto">
        <Button
          className="flex-1 lg:h-16 flex items-center justify-center gap-2 bg-gradient-to-br from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold shadow-lg shadow-emerald-500/25 rounded-2xl text-base"
          onClick={() => cart.length > 0 && setShowPayment(true)}
          disabled={cart.length === 0}
          data-testid="pos-print-btn"
        >
          <Printer className="h-5 w-5" />
          <span className="hidden lg:inline">Shtyp</span>
          <span className="text-xs bg-white/20 px-2 py-0.5 rounded-md ml-1">F2</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-blue-200 text-blue-600 hover:bg-blue-50 hover:border-blue-300"
          onClick={() => handlePrintA4()}
          disabled={cart.length === 0}
          data-testid="pos-print-a4-btn"
        >
          <FileDown className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Printo A4</span>
          <span className="text-xs bg-blue-100 px-1.5 py-0.5 rounded-md ml-1">F4</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={() => setShowProductSearch(true)}
          data-testid="pos-add-product-btn"
        >
          <Package className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">{'K\u00EBrko artikullin'}</span>
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-md ml-1">F12</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={() => setShowDocuments(true)}
          data-testid="pos-documents-btn"
        >
          <FileText className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Dokumentin</span>
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-md ml-1">F6</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={handlePrintNote}
          data-testid="pos-print-note-btn"
        >
          <Receipt className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Shtyp Noten</span>
        </Button>

        {companySettings?.show_warranty_in_pos !== false && (
          <>
            <Button
              variant="outline"
              className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-emerald-200 text-emerald-600 hover:bg-emerald-50 hover:border-emerald-300"
              onClick={() => setShowWarranty(true)}
              data-testid="pos-warranty-btn"
            >
              <Shield className="h-5 w-5" strokeWidth={1.75} />
              <span className="hidden lg:inline">Garancioni</span>
              <span className="text-xs bg-emerald-100 px-1.5 py-0.5 rounded-md ml-1">F7</span>
            </Button>

            <Button
              variant="outline"
              className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-emerald-200 text-emerald-500 hover:bg-emerald-50 hover:border-emerald-300"
              onClick={() => {
                loadWarranties();
                setShowWarrantyList(true);
              }}
              data-testid="pos-warranty-list-btn"
            >
              <List className="h-5 w-5" strokeWidth={1.75} />
              <span className="hidden lg:inline">Garancione</span>
            </Button>
          </>
        )}

        <Button
          variant="outline"
          className={`flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300 ${customerName ? 'border-[#00a79d] text-[#00a79d] bg-[#00a79d]/5' : ''}`}
          onClick={() => setShowCustomer(true)}
          data-testid="pos-customer-btn"
        >
          <User className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Konsumatori</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={() => setShowParams(true)}
          data-testid="pos-params-btn"
        >
          <Settings className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Parametrat</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={deleteSelectedItem}
          data-testid="pos-delete-btn"
        >
          <Trash2 className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">{'Fshij artikullin'}</span>
          <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded-md ml-1">Del</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-red-200 text-red-500 hover:bg-red-50 hover:border-red-300"
          onClick={clearCart}
          data-testid="pos-clear-btn"
        >
          <Trash2 className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">Pastro</span>
        </Button>

        <Button
          variant="outline"
          className="flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl border-gray-200 hover:bg-gray-50 hover:border-gray-300"
          onClick={handleCloseDrawer}
          data-testid="pos-close-drawer-btn"
        >
          <XCircle className="h-5 w-5" strokeWidth={1.75} />
          <span className="hidden lg:inline">{'Mbyll Ark\u00EBn'}</span>
        </Button>

        {(user?.role === 'admin' || user?.role === 'manager') && (
          <Button
            className={`flex-1 lg:h-14 flex items-center justify-center gap-2 rounded-2xl text-white ${applyNoVat ? 'bg-orange-500 hover:bg-orange-600' : 'bg-[#00a79d] hover:bg-[#008f86]'}`}
            onClick={handleNoVat}
            data-testid="pos-no-vat-btn"
          >
            <Percent className="h-5 w-5" strokeWidth={1.75} />
            <span className="hidden lg:inline">{applyNoVat ? 'Me TVSH' : 'Pa TVSH'}</span>
          </Button>
        )}
      </div>
'@

$before = $content.Substring(0, $startIdx)
$after = $content.Substring($endIdx)
$content = $before + $newBlock + "`r`n`r`n      {/* Payment Dialog */}`r`n      " + $after

[System.IO.File]::WriteAllText($target, $content, $utf8)
Write-Host "OK: POS.jsx u modernizua!" -ForegroundColor Green

if (Select-String -Path $target -Pattern "shadow-emerald-500/25" -SimpleMatch -Quiet) {
  Write-Host "Verifikim: OK - POS-i i ri eshte ne vend" -ForegroundColor Green
} else {
  Write-Host "Verifikim: DESHTOI" -ForegroundColor Red
}