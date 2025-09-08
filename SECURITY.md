# Security & Privacy

## Privacy Guarantees

### Local-First Architecture

- **No External Dependencies**: Runs completely offline by default
- **No Telemetry**: No usage data collected or transmitted
- **No Cloud Storage**: All data stored locally
- **Explicit Opt-in**: External API calls require explicit configuration

### Data Protection

- **Local Storage**: All documents and indices stored on your machine
- **No Sharing**: Documents never leave your system unless you enable LLM mode
- **Checksum Verification**: Detect tampering or corruption
- **Access Control**: Respects file system permissions

## LLM Mode Considerations

When LLM mode is enabled:

### Data Transmission

- **Minimal Context**: Only relevant chunks sent to API
- **No Raw Files**: Original documents never transmitted
- **Query Only**: Only your question and retrieved context sent
- **Secure Transport**: HTTPS for all API communications

### API Key Management

- **Environment Variables**: Keys stored in `.env` file
- **Never Logged**: API keys redacted from logs
- **Never Committed**: `.env` in `.gitignore`

### Provider Security

- **OpenAI**: Data retention per OpenAI policies
- **Mistral**: European data protection standards
- **Anthropic**: Constitutional AI principles

## Log Redaction

Automatic redaction of:
- Email addresses
- Phone numbers
- Credit card numbers
- Social Security Numbers
- API keys and tokens

## Best Practices

### Deployment

1. **File Permissions**: Restrict access to data directories
2. **Network Security**: Use firewall to limit access
3. **HTTPS**: Use reverse proxy with SSL for production
4. **Authentication**: Add authentication layer if needed

### Data Management

1. **Regular Backups**: Use backup feature regularly
2. **Encryption**: Consider disk encryption for sensitive data
3. **Access Logs**: Monitor file access logs
4. **Data Retention**: Implement retention policies

### API Keys

1. **Rotate Regularly**: Change API keys periodically
2. **Limit Scope**: Use read-only keys where possible
3. **Monitor Usage**: Track API usage for anomalies
4. **Separate Environments**: Different keys for dev/prod

## Compliance

### GDPR Considerations

- **Data Locality**: All processing happens locally
- **Right to Delete**: Remove documents anytime
- **Data Portability**: Export via backup feature
- **Transparency**: Open source codebase

### Industry Standards

- **No PCI Scope**: No payment processing
- **HIPAA**: Can be configured for compliance
- **SOC2**: Follows security best practices