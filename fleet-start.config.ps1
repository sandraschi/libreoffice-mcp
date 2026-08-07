# Per-repo fleet start config for libreoffice-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'libreoffice-mcp'
    BackendPort  = 10981
    FrontendPort = 10983
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\libreoffice-mcp\webapp'
    Backend = @{
        Kind       = 'custom'
        WorkDir    = 'D:\Dev\repos\libreoffice-mcp'
        SyncExtras = @('dev')
        Command    = 'uv run libreoffice-mcp --http --port 10981'
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
