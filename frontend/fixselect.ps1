$ErrorActionPreference = 'Stop'
$enc = New-Object System.Text.UTF8Encoding $false

function Fix-File($path, $pairs) {
    $abs = (Resolve-Path $path).Path
    Copy-Item $abs "$abs.selbak" -Force
    $t = [System.IO.File]::ReadAllText($abs, [System.Text.Encoding]::UTF8)
    foreach ($p in $pairs) {
        $old = $p[0]; $new = $p[1]
        $cnt = ([regex]::Matches($t, [regex]::Escape($old))).Count
        $t = $t.Replace($old, $new)
        Write-Host ("  [{0}x] {1}" -f $cnt, $old)
    }
    [System.IO.File]::WriteAllText($abs, $t, $enc)
    Write-Host "OK: $path" -ForegroundColor Green
}

Write-Host "=== AuditLogs.jsx ===" -ForegroundColor Cyan
Fix-File "src\pages\AuditLogs.jsx" @(
    @('value=""', 'value="all"'),
    @('value={filters.user_id}', 'value={filters.user_id || ''all''}'),
    @('value={filters.action}', 'value={filters.action || ''all''}'),
    @('value={filters.entity_type}', 'value={filters.entity_type || ''all''}'),
    @('setFilters({ ...filters, user_id: value })', 'setFilters({ ...filters, user_id: value === ''all'' ? '''' : value })'),
    @('setFilters({ ...filters, action: value })', 'setFilters({ ...filters, action: value === ''all'' ? '''' : value })'),
    @('setFilters({ ...filters, entity_type: value })', 'setFilters({ ...filters, entity_type: value === ''all'' ? '''' : value })')
)

Write-Host "=== Products.jsx ===" -ForegroundColor Cyan
Fix-File "src\pages\Products.jsx" @(
    @('value=""', 'value="all"'),
    @('value={formData.branch_id}', 'value={formData.branch_id || ''all''}'),
    @('setFormData({ ...formData, branch_id: value })', 'setFormData({ ...formData, branch_id: value === ''all'' ? '''' : value })')
)

Write-Host "=== Users.jsx ===" -ForegroundColor Cyan
Fix-File "src\pages\Users.jsx" @(
    @('value=""', 'value="all"'),
    @('value={formData.branch_id}', 'value={formData.branch_id || ''all''}'),
    @('setFormData({ ...formData, branch_id: value })', 'setFormData({ ...formData, branch_id: value === ''all'' ? '''' : value })')
)