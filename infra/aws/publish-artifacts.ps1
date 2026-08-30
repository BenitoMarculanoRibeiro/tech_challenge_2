[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$')]
    [string]$ArtifactBucketName,

    [ValidateNotNullOrEmpty()]
    [string]$Region = 'us-east-1',

    [ValidateNotNullOrEmpty()]
    [string]$PythonCommand = 'python',

    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$buildRoot = Join-Path $projectRoot '.build'
$artifactRoot = Join-Path $buildRoot 'artifacts'
$layerRoot = Join-Path $buildRoot 'layer'
$requirementsPath = Join-Path $projectRoot 'infra\lambda\requirements.txt'

$sourceArtifacts = [ordered]@{
    'lambda/cargaFunction.zip' = Join-Path $projectRoot 'infra\lambda\cargaFunction\lambda_function.py'
    'lambda/cargaTabelaMunicipio.zip' = Join-Path $projectRoot 'infra\lambda\cargaTabelaMunicipio\lambda_function.py'
    'lambda/cargaMetaAlfabetizacaoBrasil.zip' = Join-Path $projectRoot 'infra\lambda\cargaMetaAlfabetizacaoBrasil\lambda_function.py'
    'glue/bronze_to_silver_aluno_job.py' = Join-Path $projectRoot 'glue\bronze_to_silver\bronze_to_silver_aluno_job.py'
    'glue/bronze_to_silver_municipio_job.py' = Join-Path $projectRoot 'glue\bronze_to_silver\bronze_to_silver_municipio_job.py'
    'glue/bronze_to_silver_uf_job.py' = Join-Path $projectRoot 'glue\bronze_to_silver\bronze_to_silver_uf_job.py'
    'glue/bronze_to_silver_meta_job.py' = Join-Path $projectRoot 'glue\bronze_to_silver\bronze_to_silver_meta_job.py'
    'glue/gold_job.py' = Join-Path $projectRoot 'glue\silver_to_gold\gold_job.py'
    'step-functions/tc2-steps.asl.json' = Join-Path $projectRoot 'infra\aws\step-functions\tc2-steps.asl.json'
}

$requiredFiles = @($sourceArtifacts.Values) + $requirementsPath
$missingFiles = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
if ($missingFiles.Count -gt 0) {
    throw "Arquivos obrigatorios ausentes:`n$($missingFiles -join "`n")"
}

if (-not (Get-Command $PythonCommand -ErrorAction SilentlyContinue)) {
    throw "Python nao encontrado: $PythonCommand"
}

if (Test-Path -LiteralPath $buildRoot) {
    Remove-Item -LiteralPath $buildRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null

function New-DeterministicZip {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDirectory,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $destinationDirectory = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    Add-Type -AssemblyName System.IO.Compression
    $archiveStream = [System.IO.File]::Open($Destination, [System.IO.FileMode]::Create)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new(
            $archiveStream,
            [System.IO.Compression.ZipArchiveMode]::Create,
            $false
        )
        try {
            foreach ($file in Get-ChildItem -LiteralPath $SourceDirectory -File -Recurse | Sort-Object FullName) {
                $entryName = $file.FullName.Substring($SourceDirectory.Length).TrimStart('\') -replace '\\', '/'
                $entry = $archive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = [System.DateTimeOffset]::new(2000, 1, 1, 0, 0, 0, [System.TimeSpan]::Zero)
                $inputStream = [System.IO.File]::OpenRead($file.FullName)
                $outputStream = $entry.Open()
                try {
                    $inputStream.CopyTo($outputStream)
                }
                finally {
                    $outputStream.Dispose()
                    $inputStream.Dispose()
                }
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $archiveStream.Dispose()
    }
}

Write-Host 'Gerando pacotes das Lambdas...'
New-DeterministicZip -SourceDirectory (Split-Path -Parent $sourceArtifacts['lambda/cargaFunction.zip']) -Destination (Join-Path $artifactRoot 'lambda\cargaFunction.zip')
New-DeterministicZip -SourceDirectory (Split-Path -Parent $sourceArtifacts['lambda/cargaTabelaMunicipio.zip']) -Destination (Join-Path $artifactRoot 'lambda\cargaTabelaMunicipio.zip')
New-DeterministicZip -SourceDirectory (Split-Path -Parent $sourceArtifacts['lambda/cargaMetaAlfabetizacaoBrasil.zip']) -Destination (Join-Path $artifactRoot 'lambda\cargaMetaAlfabetizacaoBrasil.zip')

Write-Host 'Gerando layer Google para Python 3.12 x86_64...'
$layerPythonDirectory = Join-Path $layerRoot 'python'
New-Item -ItemType Directory -Path $layerPythonDirectory -Force | Out-Null
& $PythonCommand -m pip install `
    --requirement $requirementsPath `
    --target $layerPythonDirectory `
    --platform manylinux2014_x86_64 `
    --implementation cp `
    --python-version 3.12 `
    --only-binary=:all: `
    --quiet `
    --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao instalar as dependencias da layer (codigo $LASTEXITCODE)."
}

Get-ChildItem -LiteralPath $layerPythonDirectory -Directory -Recurse -Filter '__pycache__' |
    Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $layerPythonDirectory -File -Recurse -Include '*.pyc', '*.pyo' |
    Remove-Item -Force
$generatedBinDirectory = Join-Path $layerPythonDirectory 'bin'
if (Test-Path -LiteralPath $generatedBinDirectory) {
    Remove-Item -LiteralPath $generatedBinDirectory -Recurse -Force
}
Get-ChildItem -LiteralPath $layerPythonDirectory -File -Recurse -Filter 'RECORD' |
    Where-Object { $_.DirectoryName -like '*.dist-info' } |
    Remove-Item -Force

$layerDestination = Join-Path $artifactRoot 'lambda\layers\google-dependencies.zip'
New-DeterministicZip -SourceDirectory $layerRoot -Destination $layerDestination

Write-Host 'Copiando scripts Glue e definicao da Step Function...'
foreach ($relativePath in $sourceArtifacts.Keys | Where-Object { $_ -notlike 'lambda/*' }) {
    $destination = Join-Path $artifactRoot ($relativePath -replace '/', '\')
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $sourceArtifacts[$relativePath] -Destination $destination
}

$generatedFiles = @(Get-ChildItem -LiteralPath $artifactRoot -File -Recurse | Sort-Object FullName)
$manifestArtifacts = foreach ($file in $generatedFiles) {
    [ordered]@{
        path = $file.FullName.Substring($artifactRoot.Length).TrimStart('\') -replace '\\', '/'
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        sizeBytes = $file.Length
    }
}
$hashText = ($manifestArtifacts | ForEach-Object { "$($_.path)=$($_.sha256)" }) -join "`n"
$hashBytes = [System.Text.Encoding]::UTF8.GetBytes($hashText)
$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $releaseHash = ([System.BitConverter]::ToString($sha256.ComputeHash($hashBytes))).Replace('-', '').ToLowerInvariant()
}
finally {
    $sha256.Dispose()
}
$artifactPrefix = "releases/$($releaseHash.Substring(0, 16))"

$manifest = [ordered]@{
    artifactPrefix = $artifactPrefix
    contentHash = $releaseHash
    artifacts = @($manifestArtifacts)
}
$manifestPath = Join-Path $artifactRoot 'manifest.json'
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$expectedPaths = @(
    'lambda/layers/google-dependencies.zip',
    'lambda/cargaFunction.zip',
    'lambda/cargaTabelaMunicipio.zip',
    'lambda/cargaMetaAlfabetizacaoBrasil.zip',
    'glue/bronze_to_silver_aluno_job.py',
    'glue/bronze_to_silver_municipio_job.py',
    'glue/bronze_to_silver_uf_job.py',
    'glue/bronze_to_silver_meta_job.py',
    'glue/gold_job.py',
    'step-functions/tc2-steps.asl.json',
    'manifest.json'
)
foreach ($relativePath in $expectedPaths) {
    $localPath = Join-Path $artifactRoot ($relativePath -replace '/', '\')
    if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) {
        throw "Artefato esperado nao foi gerado: $relativePath"
    }
}

Write-Host ''
Write-Host 'Plano de publicacao:'
foreach ($relativePath in $expectedPaths) {
    Write-Host "  $relativePath -> s3://$ArtifactBucketName/$artifactPrefix/$relativePath"
}

if ($Execute) {
    if (-not (Get-Command 'aws' -ErrorAction SilentlyContinue)) {
        throw 'AWS CLI nao encontrado. Instale e configure o AWS CLI antes de usar -Execute.'
    }

    Write-Host ''
    Write-Host 'Publicando artefatos...'
    foreach ($relativePath in $expectedPaths) {
        $localPath = Join-Path $artifactRoot ($relativePath -replace '/', '\')
        $destination = "s3://$ArtifactBucketName/$artifactPrefix/$relativePath"
        & aws s3 cp $localPath $destination --region $Region --only-show-errors
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao publicar $relativePath (codigo $LASTEXITCODE)."
        }
    }
    Write-Host 'Publicacao concluida.'
}
else {
    Write-Host ''
    Write-Host 'Dry-run concluido: nenhum comando AWS foi executado.'
    Write-Host 'Use -Execute somente depois de revisar o plano acima.'
}

Write-Host ''
Write-Host 'Parametros para application.yaml:'
Write-Host "  ArtifactBucketName = $ArtifactBucketName"
Write-Host "  ArtifactPrefix     = $artifactPrefix"
Write-Host "  Manifest           = $manifestPath"
