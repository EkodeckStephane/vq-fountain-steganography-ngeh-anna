param(
    [string[]]$Queries,

    [string]$QueryFile,

    [int]$Limit = 10,

    [string]$OutputDir = "01_references/semantic_scholar"
)

if (-not $env:S2_API_KEY) {
    throw "Set S2_API_KEY in the environment before running this script."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if ($QueryFile) {
    $Queries = Get-Content -LiteralPath $QueryFile |
        Where-Object { $_.Trim().Length -gt 0 -and -not $_.Trim().StartsWith("#") }
}

if (-not $Queries -or $Queries.Count -eq 0) {
    throw "Provide queries with -Queries or -QueryFile."
}

$fields = "title,year,authors,venue,publicationVenue,externalIds,citationCount,influentialCitationCount,abstract,url,isOpenAccess,openAccessPdf"
$all = @()

for ($i = 0; $i -lt $Queries.Count; $i++) {
    $query = $Queries[$i]
    $encoded = [System.Uri]::EscapeDataString($query)
    $uri = "https://api.semanticscholar.org/graph/v1/paper/search?query=$encoded&limit=$Limit&fields=$fields"
    Write-Host "Query $($i + 1)/$($Queries.Count): $query"
    $response = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            $response = Invoke-RestMethod -Method Get -Uri $uri -Headers @{ "x-api-key" = $env:S2_API_KEY } -ErrorAction Stop
            break
        } catch {
            if ($attempt -eq 3) {
                Write-Warning "Failed query after 3 attempts: $query"
                Write-Warning $_.Exception.Message
            } else {
                Start-Sleep -Seconds (10 * $attempt)
            }
        }
    }

    if (-not $response) {
        continue
    }

    $safeName = ($query -replace '[^A-Za-z0-9]+','_').Trim('_').ToLowerInvariant()
    $rawPath = Join-Path $OutputDir "$safeName.json"
    $response | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $rawPath -Encoding UTF8

    foreach ($paper in $response.data) {
        $doi = $null
        if ($paper.externalIds -and $paper.externalIds.DOI) {
            $doi = $paper.externalIds.DOI
        }
        $all += [PSCustomObject]@{
            query = $query
            title = $paper.title
            year = $paper.year
            venue = $paper.venue
            doi = $doi
            citations = $paper.citationCount
            influential_citations = $paper.influentialCitationCount
            url = $paper.url
            open_access_pdf = if ($paper.openAccessPdf) { $paper.openAccessPdf.url } else { $null }
        }
    }

    if ($i -lt ($Queries.Count - 1)) {
        Start-Sleep -Seconds 4
    }
}

$csvPath = Join-Path $OutputDir "semantic_scholar_search_results.csv"
$all | Sort-Object -Property @{Expression="citations";Descending=$true}, year |
    Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

Write-Host "Saved results to $csvPath"
