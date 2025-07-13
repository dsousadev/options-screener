# Auto Options Screener

An automated options screening and analysis platform.

## Project Structure

```
.
├── infra/          # Infrastructure as Code
│   ├── docker/     # Docker Compose configurations
│   └── terraform/  # Terraform configurations
├── services/       # Microservices
│   ├── api/        # FastAPI service
│   ├── worker/     # Background job processor
│   └── data_ingest/ # Data ingestion service
└── tests/          # Test suites
```

## Development

### Prerequisites

- Git 2.40+
- Docker Desktop 4.30+
- Terraform CLI 1.9+
- Node.js 20.x+
- Python 3.12+

### Quick Start

```bash
# Start local development environment
make up

# Run tests
make test

# Format code
make fmt
```

## License

Private - All rights reserved
