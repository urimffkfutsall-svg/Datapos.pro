$path = 'src\pages\POS.jsx'
$abs = (Resolve-Path $path).Path
Copy-Item $abs "$abs.bakdiscimg" -Force

$enc = New-Object System.Text.UTF8Encoding $false
$t = [System.IO.File]::ReadAllText($abs, [System.Text.Encoding]::UTF8)

function Apply($text, $label, $old, $new) {
    $cnt = ([regex]::Matches($text, [regex]::Escape($old))).Count
    Write-Host ("  [{0}x] {1}" -f $cnt, $label)
    return $text.Replace($old, $new)
}

$old1 = @'
current_stock: product.current_stock
'@
$new1 = @'
current_stock: product.current_stock, image_url: product.metadata?.image_url || null
'@
$t = Apply $t "R1 addToCart image_url" $old1 $new1

$old2 = @'
max_stock: product.current_stock
'@
$new2 = @'
max_stock: product.current_stock, image_url: product.metadata?.image_url || null
'@
$t = Apply $t "R2 row-swap image_url" $old2 $new2

$old3a = @'
<SelectValue>{item.product_name || 'Zgjidh'}</SelectValue>
'@
$new3a = @'
<SelectValue><span className="inline-flex items-center gap-2">{item.image_url ? <img src={item.image_url} alt="" className="h-6 w-6 rounded object-cover" /> : null}<span>{item.product_name || 'Zgjidh'}</span></span></SelectValue>
'@
$t = Apply $t "R3a SelectValue image" $old3a $new3a

$old3b = @'
<span className="font-semibold text-gray-800">{item.product_name || 'Produkt'}</span>
'@
$new3b = @'
<div className="flex items-center gap-2">{item.image_url ? <img src={item.image_url} alt="" className="h-8 w-8 rounded-md object-cover border border-gray-200" /> : null}<span className="font-semibold text-gray-800">{item.product_name || 'Produkt'}</span></div>
'@
$t = Apply $t "R3b non-edit row image" $old3b $new3b

$old4 = @'
(item.unit_price * (1 + item.vat_percent / 100)).toFixed(2)
'@
$new4 = @'
(item.unit_price * (1 - item.discount_percent / 100) * (1 + item.vat_percent / 100)).toFixed(2)
'@
$t = Apply $t "R4 Cmimi me TVSH me zbritje" $old4 $new4

$old5 = @'
const canEdit = user?.role === 'admin' || user?.role === 'manager';
'@
$new5 = @'
const canEdit = user?.role === 'admin' || user?.role === 'manager' || user?.role === 'super_admin';
'@
$t = Apply $t "R5 canEdit super_admin" $old5 $new5

[System.IO.File]::WriteAllText($abs, $t, $enc)
Write-Host "OK: POS.jsx u rregullua" -ForegroundColor Green