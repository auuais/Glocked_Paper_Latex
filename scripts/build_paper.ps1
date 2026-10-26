param([int]$MaximumPages = 14)
$ErrorActionPreference = 'Stop'
$paperRoot = Split-Path -Parent $PSScriptRoot
$paperOutput = Join-Path $paperRoot 'output/pdf'
New-Item -ItemType Directory -Path $paperOutput -Force | Out-Null
$paperLatexmk = Get-Command latexmk -ErrorAction Stop
Push-Location -LiteralPath $paperRoot
try {
    & $paperLatexmk.Source -pdf -interaction=nonstopmode -halt-on-error -file-line-error '-synctex=1' ('-outdir=' + $paperOutput) 'g_locked_panorama_stabilization.tex'
    if ($LASTEXITCODE -ne 0) { throw 'LaTeX compilation failed; inspect output/pdf/*.log' }
    $paperPdf = Join-Path $paperOutput 'g_locked_panorama_stabilization.pdf'
    $paperInfo = & pdfinfo $paperPdf
    if ($LASTEXITCODE -ne 0) { throw 'PDF inspection failed; install Poppler pdfinfo' }
    $paperPageLine = $paperInfo | Where-Object { $_ -match '^Pages:\s+(\d+)' }
    if (-not $paperPageLine -or $paperPageLine -notmatch '^Pages:\s+(\d+)') { throw 'Missing PDF page count' }
    $paperPageCount = [int]$Matches[1]
    if ($paperPageCount -gt $MaximumPages) { throw "Page limit exceeded: $paperPageCount > $MaximumPages" }
    $paperLog = Get-Content -LiteralPath (Join-Path $paperOutput 'g_locked_panorama_stabilization.log') -Raw
    if ($paperLog -match 'There were undefined references|There were undefined citations|multiply defined|Overfull \\[hv]box') {
        throw 'Unresolved references or overfull boxes remain; inspect the LaTeX log'
    }
    Copy-Item -LiteralPath $paperPdf -Destination (Join-Path $paperRoot 'g_locked_panorama_stabilization.pdf') -Force
    Write-Host "PASS: $paperPageCount pages (limit $MaximumPages). $paperPdf"
} finally { Pop-Location }
