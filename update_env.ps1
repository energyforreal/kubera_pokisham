# Update .env file with correct model path
$envFile = ".env"

if (Test-Path $envFile) {
    Write-Host "Updating .env file..." -ForegroundColor Yellow
    
    # Read the file
    $content = Get-Content $envFile -Raw
    
    # Replace the model path
    $content = $content -replace 'MODEL_PATH=models/xgboost_model\.pkl', 'MODEL_PATH=models/xgboost_BTCUSD_15m.pkl'
    
    # Write back to file
    Set-Content -Path $envFile -Value $content -NoNewline
    
    Write-Host "✅ Updated MODEL_PATH to: models/xgboost_BTCUSD_15m.pkl" -ForegroundColor Green
    
    # Show the updated line
    Write-Host "`nVerifying change:" -ForegroundColor Cyan
    Get-Content $envFile | Select-String "MODEL_PATH"
    
} else {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Creating new .env from template..." -ForegroundColor Yellow
    Copy-Item "config\env.example" ".env"
    Write-Host "✅ Created .env file. Please run this script again." -ForegroundColor Green
}

Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

