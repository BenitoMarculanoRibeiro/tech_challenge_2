param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Profile,
    [string]$Region = "us-east-1",
    [string]$StackName = "tc2-pipeline",
    [string]$WorkGroup = "primary"
)

$ErrorActionPreference = "Stop"

$awsCommand = Get-Command aws -ErrorAction Stop

$goldBucket = & $awsCommand.Source cloudformation describe-stacks `
    --stack-name $StackName `
    --profile $Profile `
    --region $Region `
    --query "Stacks[0].Outputs[?OutputKey=='GoldBucketName'].OutputValue | [0]" `
    --output text

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($goldBucket) -or $goldBucket -eq "None") {
    throw "Nao foi possivel localizar o output GoldBucketName no stack $StackName."
}

$accountId = & $awsCommand.Source sts get-caller-identity `
    --profile $Profile `
    --region $Region `
    --query Account `
    --output text

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($accountId)) {
    throw "Nao foi possivel identificar a conta AWS do perfil $Profile."
}

$resultLocation = "s3://$goldBucket/resultados-athena/"
$configuration = @{
    EnforceWorkGroupConfiguration = $true
    ResultConfigurationUpdates = @{
        OutputLocation = $resultLocation
        ExpectedBucketOwner = $accountId
        EncryptionConfiguration = @{
            EncryptionOption = "SSE_S3"
        }
        AclConfiguration = @{
            S3AclOption = "BUCKET_OWNER_FULL_CONTROL"
        }
    }
} | ConvertTo-Json -Depth 5 -Compress

& $awsCommand.Source athena update-work-group `
    --work-group $WorkGroup `
    --configuration-updates $configuration `
    --profile $Profile `
    --region $Region

if ($LASTEXITCODE -ne 0) {
    throw "Falha ao atualizar o workgroup Athena $WorkGroup."
}

Write-Host "Workgroup $WorkGroup configurado com resultados em $resultLocation"
