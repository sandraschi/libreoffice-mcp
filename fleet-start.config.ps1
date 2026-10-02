# Per-repo fleet start config for libreoffice-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'libreoffice-mcp'
    BackendPort  = 10981
    FrontendPort = 10983
    HealthPath   = '/health'
    WebRoot      = 'webapp'
    Backend = @{
        Kind       = 'module-serve'
        Module     = 'libreoffice_mcp'
        ServeArgs  = @('--http', '--port', '10981')
        SyncExtras = @('dev')
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
