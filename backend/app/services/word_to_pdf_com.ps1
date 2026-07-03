param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$word = $null
$document = $null

try {
    $resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
    $outputDirectory = [System.IO.Path]::GetDirectoryName($resolvedOutput)

    if (-not [System.IO.Directory]::Exists($outputDirectory)) {
        [System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
    }

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    $document = $word.Documents.Open($resolvedInput)
    if ($document -eq $null) {
        throw "Microsoft Word could not open the input document."
    }

    try {
        # 17 is wdExportFormatPDF / wdFormatPDF.
        $document.ExportAsFixedFormat($resolvedOutput, 17)
    }
    catch {
        $document.SaveAs($resolvedOutput, 17)
    }
}
finally {
    if ($document -ne $null) {
        $saveChanges = $false
        $document.Close([ref]$saveChanges) | Out-Null
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null
    }

    if ($word -ne $null) {
        $word.Quit() | Out-Null
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }

    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
