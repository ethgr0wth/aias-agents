# Cybersecurity Agents Specification

**Recon Agent + Vulnerability Scanner Agent**

**Version:** 1.0  
**Date:** January 16, 2026  
**Status:** Draft  
**Author:** AiAS Engineering

---

## Executive Summary

This specification defines two complementary agentic workflows for cybersecurity reconnaissance and vulnerability assessment within the AiAssist Secure platform. These agents leverage LLM orchestration to automate security research tasks, synthesize findings, and generate actionable reports.

**Recon Agent** — Automated OSINT and attack surface discovery  
**Vuln Scanner Agent** — Targeted vulnerability detection and risk assessment

Both agents integrate with AiAS's existing infrastructure:
- BYOK multi-provider LLM support for analysis
- WebExtractionService for content fetching
- Custom Tooling framework for external tool execution
- Keystone environment for isolated execution

---

## Table of Contents

1. [Use Cases](#use-cases)
2. [Architecture Overview](#architecture-overview)
3. [Recon Agent](#recon-agent)
4. [Vuln Scanner Agent](#vuln-scanner-agent)
5. [Shared Components](#shared-components)
6. [Data Schemas](#data-schemas)
7. [API Endpoints](#api-endpoints)
8. [LLM Prompt Strategies](#llm-prompt-strategies)
9. [Security & Guardrails](#security--guardrails)
10. [UI/UX Design](#uiux-design)
11. [Implementation Phases](#implementation-phases)
12. [Future Enhancements](#future-enhancements)

---

## Use Cases

### Primary Users

| User Type | Use Case |
|-----------|----------|
| **Security Consultants** | Client engagement prep, scope validation, initial assessment |
| **DevOps/SREs** | Pre-deployment security checks, infrastructure audits |
| **Bug Bounty Hunters** | Target reconnaissance, vulnerability discovery |
| **Developers** | Security self-assessment before launch |
| **Compliance Teams** | External attack surface inventory |

### Example Workflows

**Workflow 1: Pre-Engagement Recon**
```
User: "Run recon on example.com - we're doing a pentest next week"
Agent: Discovers subdomains, tech stack, exposed services, employee info
Output: Structured report with prioritized attack surface
```

**Workflow 2: Vulnerability Assessment**
```
User: "Scan the login page at app.example.com for common vulns"
Agent: Tests for SQLi, XSS, auth bypass, info disclosure
Output: Findings with severity, evidence, remediation steps
```

**Workflow 3: Chained Pipeline**
```
User: "Full security assessment of example.com"
Agent: Recon → Vuln Scan → Consolidated Report
Output: Complete security posture with executive summary
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AiAS Cybersecurity Agents                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Agent Orchestrator                           │    │
│  │  ┌─────────────────┐              ┌─────────────────┐               │    │
│  │  │   Recon Agent   │──────────────▶│ VulnScan Agent │               │    │
│  │  │                 │   Findings    │                 │               │    │
│  │  │  • Subdomain    │   Handoff     │  • Nuclei       │               │    │
│  │  │  • Tech Stack   │               │  • SQLi/XSS     │               │    │
│  │  │  • OSINT        │               │  • Auth Tests   │               │    │
│  │  └────────┬────────┘               └────────┬────────┘               │    │
│  │           │                                  │                        │    │
│  │           └──────────────┬───────────────────┘                        │    │
│  │                          │                                            │    │
│  │                 ┌────────▼────────┐                                   │    │
│  │                 │  Report Engine  │                                   │    │
│  │                 │  • Synthesis    │                                   │    │
│  │                 │  • Prioritize   │                                   │    │
│  │                 │  • Export       │                                   │    │
│  │                 └─────────────────┘                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────┴─────────────────────────────────────┐  │
│  │                          Tool Execution Layer                          │  │
│  │                                                                        │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │
│  │  │ Subfinder  │ │   httpx    │ │  Nuclei    │ │  Shodan    │         │  │
│  │  │ (subdoms)  │ │ (probing)  │ │ (vulns)    │ │  (API)     │         │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘         │  │
│  │                                                                        │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │
│  │  │ Wappalyzer │ │  WHOIS     │ │  nmap      │ │ Custom     │         │  │
│  │  │ (techstack)│ │ (domain)   │ │  (ports)   │ │ Scripts    │         │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘         │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│  ┌─────────────────────────────────┴─────────────────────────────────────┐  │
│  │                           Storage Layer                                │  │
│  │                                                                        │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │  │
│  │  │ Redis          │  │ PostgreSQL     │  │ File Storage   │           │  │
│  │  │ • Sessions     │  │ • Targets      │  │ • Raw outputs  │           │  │
│  │  │ • Job queue    │  │ • Findings     │  │ • Reports      │           │  │
│  │  │ • Rate limits  │  │ • Reports      │  │ • Evidence     │           │  │
│  │  └────────────────┘  └────────────────┘  └────────────────┘           │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Recon Agent

### Purpose

Automated reconnaissance and OSINT gathering to map an organization's external attack surface.

### Capabilities

| Category | Data Collected |
|----------|----------------|
| **Subdomain Discovery** | All subdomains via DNS enumeration, certificate transparency |
| **Technology Stack** | Frameworks, CMS, server software, CDN, WAF detection |
| **Port/Service Scan** | Open ports, service versions, banners |
| **WHOIS/DNS** | Registrar, nameservers, DNS records, IP ranges |
| **Content Discovery** | robots.txt, sitemap, exposed directories |
| **Social/OSINT** | Employee names (LinkedIn), email patterns, leaked credentials (HaveIBeenPwned) |
| **Cloud Assets** | S3 buckets, Azure blobs, GCP storage (permutation-based) |

### Tool Integrations

```yaml
tools:
  subdomain_discovery:
    - name: subfinder
      type: cli
      command: "subfinder -d {domain} -silent -o {output}"
      output_format: lines
      
    - name: amass
      type: cli  
      command: "amass enum -passive -d {domain} -o {output}"
      output_format: lines
      
    - name: crt.sh
      type: api
      endpoint: "https://crt.sh/?q=%.{domain}&output=json"
      output_format: json
      
  technology_detection:
    - name: wappalyzer
      type: api
      endpoint: "https://api.wappalyzer.com/v2/lookup/?urls={url}"
      requires_key: true
      
    - name: httpx
      type: cli
      command: "httpx -u {url} -title -status-code -tech-detect -json"
      output_format: json
      
  port_scanning:
    - name: nmap
      type: cli
      command: "nmap -sV -sC -T4 --top-ports 1000 {target} -oX {output}"
      output_format: xml
      requires_authorization: true
      
    - name: shodan
      type: api
      endpoint: "https://api.shodan.io/shodan/host/{ip}?key={api_key}"
      requires_key: true
      
  whois_dns:
    - name: whois
      type: cli
      command: "whois {domain}"
      output_format: text
      
    - name: dig
      type: cli
      command: "dig {domain} ANY +noall +answer"
      output_format: text
      
  content_discovery:
    - name: web_extraction
      type: internal
      service: WebExtractionService
      endpoints: ["/robots.txt", "/sitemap.xml", "/.well-known/security.txt"]
```

### Recon Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Recon Agent Workflow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. TARGET VALIDATION                                                │
│     ├─ Parse input (domain, IP, URL)                                │
│     ├─ Validate format and scope                                    │
│     └─ Check authorization/consent                                  │
│                              │                                       │
│                              ▼                                       │
│  2. PASSIVE RECON (No direct contact)                               │
│     ├─ Subdomain enumeration (crt.sh, DNS)                          │
│     ├─ WHOIS lookup                                                 │
│     ├─ Shodan/Censys data                                           │
│     ├─ Technology fingerprinting (Wappalyzer)                       │
│     └─ Social OSINT (optional)                                      │
│                              │                                       │
│                              ▼                                       │
│  3. ACTIVE RECON (Direct contact - requires auth)                   │
│     ├─ HTTP probing (httpx)                                         │
│     ├─ Port scanning (nmap)                                         │
│     ├─ Content discovery                                            │
│     └─ Screenshot capture                                           │
│                              │                                       │
│                              ▼                                       │
│  4. LLM SYNTHESIS                                                   │
│     ├─ Correlate findings across sources                            │
│     ├─ Identify attack surface priorities                           │
│     ├─ Flag interesting/unusual findings                            │
│     └─ Generate narrative summary                                   │
│                              │                                       │
│                              ▼                                       │
│  5. OUTPUT                                                          │
│     ├─ Structured JSON (for VulnScan handoff)                       │
│     ├─ Markdown report                                              │
│     └─ Evidence artifacts (screenshots, raw data)                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Recon Output Schema

```typescript
interface ReconResult {
  target: {
    input: string;              // Original input
    domain: string;             // Normalized domain
    ip_addresses: string[];     // Resolved IPs
    scope: string[];            // In-scope assets
  };
  
  subdomains: {
    total_count: number;
    live_count: number;
    items: SubdomainInfo[];
  };
  
  technology_stack: {
    web_servers: string[];      // nginx, Apache, etc.
    frameworks: string[];       // React, Django, etc.
    cms: string[];              // WordPress, Drupal
    cdn_waf: string[];          // Cloudflare, Akamai
    analytics: string[];        // Google Analytics, etc.
    javascript_libs: string[];
  };
  
  infrastructure: {
    hosting_provider: string;
    ip_ranges: string[];
    asn: string;
    nameservers: string[];
    mail_servers: string[];
  };
  
  exposed_services: {
    port: number;
    service: string;
    version: string;
    banner: string;
    risk_level: 'info' | 'low' | 'medium' | 'high';
  }[];
  
  content_findings: {
    robots_txt: string | null;
    sitemap_urls: string[];
    security_txt: string | null;
    interesting_paths: string[];
  };
  
  osint: {
    whois: WhoisData;
    employee_patterns: string[];   // email format detected
    social_profiles: string[];
    leaked_credentials: boolean;   // HaveIBeenPwned check
  };
  
  llm_analysis: {
    summary: string;               // Natural language summary
    attack_surface_priority: AttackSurfaceItem[];
    interesting_findings: string[];
    recommendations: string[];
  };
  
  metadata: {
    scan_id: string;
    started_at: string;
    completed_at: string;
    tools_used: string[];
    errors: string[];
  };
}

interface SubdomainInfo {
  subdomain: string;
  ip: string | null;
  status_code: number | null;
  title: string | null;
  tech_stack: string[];
  screenshot_path: string | null;
  is_interesting: boolean;
  notes: string;
}

interface AttackSurfaceItem {
  asset: string;
  type: 'subdomain' | 'service' | 'endpoint' | 'credential';
  priority: 'critical' | 'high' | 'medium' | 'low';
  reason: string;
}
```

---

## Vuln Scanner Agent

### Purpose

Targeted vulnerability detection against discovered assets, with LLM-assisted analysis and remediation guidance.

### Capabilities

| Category | Tests Performed |
|----------|-----------------|
| **Injection Attacks** | SQLi, NoSQLi, Command Injection, LDAP Injection |
| **XSS Testing** | Reflected, Stored, DOM-based XSS |
| **Authentication** | Default creds, brute-force, session issues, JWT weaknesses |
| **Authorization** | IDOR, privilege escalation, access control bypass |
| **Information Disclosure** | Version exposure, stack traces, sensitive files |
| **Misconfigurations** | CORS, security headers, SSL/TLS issues |
| **Known CVEs** | Nuclei templates for specific CVEs |
| **API Security** | Broken auth, rate limiting, injection in APIs |

### Tool Integrations

```yaml
tools:
  vulnerability_scanning:
    - name: nuclei
      type: cli
      command: "nuclei -u {url} -t {templates} -json -o {output}"
      templates:
        - cves/
        - vulnerabilities/
        - exposures/
        - misconfigurations/
      output_format: jsonl
      
    - name: nikto
      type: cli
      command: "nikto -h {url} -Format json -o {output}"
      output_format: json
      
  injection_testing:
    - name: sqlmap
      type: cli
      command: "sqlmap -u {url} --batch --level=2 --risk=2 --output-dir={output}"
      requires_authorization: true
      output_format: directory
      
    - name: xsstrike
      type: cli
      command: "xsstrike -u {url} --crawl --json"
      output_format: json
      
  ssl_analysis:
    - name: testssl
      type: cli
      command: "testssl.sh --json {url}"
      output_format: json
      
    - name: sslyze
      type: cli
      command: "sslyze {host} --json_out={output}"
      output_format: json
      
  header_analysis:
    - name: security_headers
      type: api
      endpoint: "https://securityheaders.com/?q={url}&followRedirects=on"
      output_format: html_parse
      
  custom_checks:
    - name: cors_check
      type: internal
      tests: ["origin_reflection", "null_origin", "wildcard"]
      
    - name: jwt_check
      type: internal
      tests: ["alg_none", "weak_secret", "expiry"]
```

### VulnScan Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     VulnScan Agent Workflow                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. INPUT PROCESSING                                                │
│     ├─ Accept targets (URLs, IPs, or Recon handoff)                 │
│     ├─ Parse scope limitations                                      │
│     ├─ Verify authorization token/consent                           │
│     └─ Select scan profile (quick/standard/deep)                    │
│                              │                                       │
│                              ▼                                       │
│  2. PASSIVE VULNERABILITY CHECKS                                    │
│     ├─ Security header analysis                                     │
│     ├─ SSL/TLS configuration                                        │
│     ├─ Known CVE matching (version-based)                           │
│     └─ Information disclosure checks                                │
│                              │                                       │
│                              ▼                                       │
│  3. ACTIVE VULNERABILITY TESTS (Authorized only)                    │
│     ├─ Nuclei template scanning                                     │
│     ├─ SQLi/XSS probing (safe payloads)                             │
│     ├─ Authentication testing                                       │
│     ├─ IDOR/access control checks                                   │
│     └─ API endpoint fuzzing                                         │
│                              │                                       │
│                              ▼                                       │
│  4. FINDING VALIDATION                                              │
│     ├─ Deduplicate findings                                         │
│     ├─ Verify exploitability                                        │
│     ├─ Collect evidence (request/response)                          │
│     └─ Assign severity (CVSS-based)                                 │
│                              │                                       │
│                              ▼                                       │
│  5. LLM ANALYSIS                                                    │
│     ├─ Explain each finding in plain English                        │
│     ├─ Assess business impact                                       │
│     ├─ Generate remediation steps                                   │
│     ├─ Prioritize by risk                                           │
│     └─ Create executive summary                                     │
│                              │                                       │
│                              ▼                                       │
│  6. OUTPUT                                                          │
│     ├─ Findings report (JSON/Markdown/PDF)                          │
│     ├─ Evidence package                                             │
│     └─ Remediation checklist                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### VulnScan Output Schema

```typescript
interface VulnScanResult {
  target: {
    input: string;
    urls_scanned: string[];
    scope: string;
    authorization_id: string;  // Reference to consent/auth
  };
  
  scan_config: {
    profile: 'quick' | 'standard' | 'deep';
    tools_enabled: string[];
    categories: string[];      // injection, xss, misconfig, etc.
  };
  
  findings: VulnerabilityFinding[];
  
  summary: {
    total_findings: number;
    by_severity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
    };
    top_risks: string[];
    overall_risk_score: number;  // 0-100
  };
  
  llm_analysis: {
    executive_summary: string;
    technical_summary: string;
    business_impact: string;
    prioritized_actions: ActionItem[];
    positive_findings: string[];  // What's done well
  };
  
  metadata: {
    scan_id: string;
    started_at: string;
    completed_at: string;
    duration_seconds: number;
    requests_made: number;
    errors: string[];
  };
}

interface VulnerabilityFinding {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  cvss_score: number | null;
  cvss_vector: string | null;
  cve_id: string | null;
  cwe_id: string | null;
  
  category: string;           // sqli, xss, misconfig, etc.
  affected_url: string;
  affected_parameter: string | null;
  
  description: string;        // Technical description
  plain_english: string;      // LLM-generated explanation
  business_impact: string;    // LLM-generated impact assessment
  
  evidence: {
    request: string;
    response: string;
    screenshot: string | null;
    payload_used: string | null;
  };
  
  remediation: {
    summary: string;
    steps: string[];
    code_example: string | null;
    references: string[];
  };
  
  tool_source: string;        // nuclei, custom, etc.
  confidence: 'confirmed' | 'likely' | 'potential';
  false_positive: boolean;
  verified_at: string | null;
}

interface ActionItem {
  priority: number;
  finding_ids: string[];
  action: string;
  effort: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
}
```

---

## Shared Components

### Job Queue System

Both agents use a shared job queue for async execution:

```typescript
interface ScanJob {
  id: string;
  type: 'recon' | 'vulnscan' | 'full';
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  
  input: {
    targets: string[];
    options: Record<string, any>;
    authorization_id: string;
  };
  
  progress: {
    current_stage: string;
    stages_completed: string[];
    stages_remaining: string[];
    percent_complete: number;
    current_tool: string | null;
    findings_count: number;
  };
  
  output: {
    recon_result: ReconResult | null;
    vulnscan_result: VulnScanResult | null;
    report_paths: string[];
  };
  
  user_id: string;
  workspace_id: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}
```

### Rate Limiting

```typescript
const rateLimits = {
  // Per-target limits
  requests_per_second: 10,
  concurrent_tools: 3,
  
  // Per-user limits (daily)
  recon_scans_per_day: {
    free: 2,
    basic: 10,
    pro: 50,
    enterprise: 'unlimited'
  },
  vulnscans_per_day: {
    free: 1,
    basic: 5,
    pro: 25,
    enterprise: 'unlimited'
  },
  
  // Global limits
  max_subdomains_per_scan: 500,
  max_urls_per_vulnscan: 100,
  scan_timeout_minutes: 30
};
```

### Tool Executor

Unified interface for running external tools:

```typescript
interface ToolExecutor {
  // Execute a tool and return parsed output
  execute(tool: ToolDefinition, params: Record<string, string>): Promise<ToolResult>;
  
  // Check if tool is available
  isAvailable(toolName: string): Promise<boolean>;
  
  // Get tool health status
  healthCheck(): Promise<ToolHealthStatus[]>;
}

interface ToolResult {
  tool: string;
  success: boolean;
  output: any;           // Parsed output
  raw_output: string;    // Raw stdout
  stderr: string;
  exit_code: number;
  duration_ms: number;
  error: string | null;
}
```

---

## API Endpoints

### Recon Agent API

```yaml
POST /api/v1/security/recon
  description: Start a new reconnaissance scan
  auth: required
  body:
    target: string          # Domain, IP, or URL
    options:
      passive_only: boolean # Skip active scanning (default: false)
      include_osint: boolean
      subdomain_limit: number
      screenshot: boolean
  response:
    job_id: string
    status: 'queued'
    estimated_duration: string

GET /api/v1/security/recon/{job_id}
  description: Get recon job status and results
  auth: required
  response:
    job: ScanJob
    result: ReconResult | null

GET /api/v1/security/recon/{job_id}/stream
  description: SSE stream for real-time progress
  auth: required
  events:
    - stage_started
    - stage_completed
    - finding_discovered
    - scan_completed
    - scan_failed

DELETE /api/v1/security/recon/{job_id}
  description: Cancel a running scan
  auth: required
```

### VulnScan Agent API

```yaml
POST /api/v1/security/vulnscan
  description: Start a vulnerability scan
  auth: required
  body:
    targets: string[]       # URLs to scan
    recon_job_id: string?   # Optional: use recon output
    profile: 'quick' | 'standard' | 'deep'
    categories: string[]    # sqli, xss, misconfig, etc.
    authorization:
      consent_type: 'self_owned' | 'written_permission' | 'bug_bounty'
      consent_evidence: string  # Reference or upload ID
  response:
    job_id: string
    status: 'queued'
    
GET /api/v1/security/vulnscan/{job_id}
  description: Get vulnscan job status and results
  auth: required
  response:
    job: ScanJob
    result: VulnScanResult | null

GET /api/v1/security/vulnscan/{job_id}/findings
  description: Get paginated findings
  auth: required
  query:
    severity: string[]
    category: string[]
    page: number
    limit: number
  response:
    findings: VulnerabilityFinding[]
    total: number

POST /api/v1/security/vulnscan/{job_id}/findings/{finding_id}/verify
  description: Manually verify/dismiss a finding
  auth: required
  body:
    status: 'confirmed' | 'false_positive' | 'accepted_risk'
    notes: string
```

### Reports API

```yaml
GET /api/v1/security/reports/{job_id}
  description: Generate/download report
  auth: required
  query:
    format: 'json' | 'markdown' | 'pdf' | 'html'
    include_evidence: boolean
    executive_summary_only: boolean
  response:
    report_url: string
    expires_at: string

GET /api/v1/security/history
  description: List past scans
  auth: required
  query:
    type: 'recon' | 'vulnscan' | 'all'
    page: number
    limit: number
  response:
    scans: ScanJob[]
    total: number
```

---

## LLM Prompt Strategies

### Recon Synthesis Prompt

```markdown
You are a cybersecurity reconnaissance analyst. Given the following raw data from multiple reconnaissance tools, synthesize a comprehensive attack surface analysis.

## Raw Data
{tool_outputs}

## Your Task
1. **Correlate Findings**: Connect related data points across sources
2. **Prioritize Attack Surface**: Rank assets by potential risk/interest
3. **Identify Anomalies**: Flag unusual configurations or exposures
4. **Generate Summary**: Write a clear, actionable summary

## Output Format
Provide your analysis in the following structure:
- Executive Summary (2-3 sentences)
- Top 5 Priority Targets (with reasoning)
- Interesting Findings (unusual/notable items)
- Technology Stack Summary
- Recommendations for Next Steps

Be concise but thorough. Focus on actionable intelligence.
```

### Vulnerability Explanation Prompt

```markdown
You are a security consultant explaining a vulnerability to a development team.

## Vulnerability Details
- Title: {finding.title}
- Severity: {finding.severity}
- Location: {finding.affected_url}
- Technical Details: {finding.description}
- Evidence: {finding.evidence}

## Your Task
1. **Plain English Explanation**: What is this vulnerability? (for non-security people)
2. **Business Impact**: What could happen if exploited?
3. **Remediation Steps**: How to fix it? (specific, actionable)
4. **Code Example**: If applicable, show before/after code

Keep explanations clear and jargon-free where possible. Prioritize actionable advice.
```

### Prioritization Prompt

```markdown
You are a security risk analyst. Given these vulnerability findings, create a prioritized remediation plan.

## Findings
{all_findings_summary}

## Context
- Application Type: {app_type}
- Business Criticality: {criticality}
- Available Resources: {resource_level}

## Your Task
Create a prioritized action plan considering:
1. Severity and exploitability
2. Business impact
3. Effort to remediate
4. Dependencies between fixes

Output a numbered action list with:
- Action to take
- Which findings it addresses
- Effort estimate (low/medium/high)
- Expected impact
```

---

## Security & Guardrails

### Authorization Requirements

```typescript
interface ScanAuthorization {
  id: string;
  user_id: string;
  target_domain: string;
  
  consent_type: 
    | 'self_owned'           // User owns the target
    | 'written_permission'   // Has written consent from owner
    | 'bug_bounty'           // Public bug bounty program
    | 'pentest_agreement';   // Formal pentest contract
  
  evidence: {
    type: 'declaration' | 'document' | 'url';
    content: string;         // Text, file path, or URL to program
    verified: boolean;
  };
  
  scope: {
    domains: string[];       // Allowed domains
    ip_ranges: string[];     // Allowed IP ranges
    excluded: string[];      // Explicitly excluded
  };
  
  valid_until: string;
  created_at: string;
}
```

### Scope Enforcement

```typescript
const scopeEnforcement = {
  // Always blocked (never scan)
  global_blocklist: [
    'gov', 'mil', 'edu',     // Government/military/education TLDs
    'localhost', '127.0.0.1',
    '10.*', '172.16-31.*', '192.168.*',  // Private ranges
  ],
  
  // Require explicit authorization
  require_auth_for: [
    'active_scanning',       // Anything that sends payloads
    'port_scanning',
    'brute_force',
    'exploitation'
  ],
  
  // Allowed without auth (passive only)
  passive_allowed: [
    'dns_lookup',
    'whois',
    'certificate_transparency',
    'shodan_lookup',         // Uses cached data
    'wappalyzer'            // Just HTTP headers
  ]
};
```

### Abuse Prevention

```yaml
abuse_prevention:
  # Rate limiting per user
  max_scans_per_hour: 10
  max_targets_per_scan: 50
  
  # Payload restrictions
  no_destructive_payloads: true
  no_dos_testing: true
  no_data_exfiltration: true
  
  # Monitoring
  log_all_scan_requests: true
  alert_on_blocklist_attempts: true
  require_mfa_for_active_scans: true
  
  # Legal
  terms_acceptance_required: true
  disclaimer_shown: true
  user_responsibility_acknowledged: true
```

### Audit Logging

```typescript
interface SecurityAuditLog {
  timestamp: string;
  user_id: string;
  action: 'scan_started' | 'scan_completed' | 'finding_exported' | 'authorization_created';
  target: string;
  authorization_id: string;
  ip_address: string;
  user_agent: string;
  details: Record<string, any>;
}
```

---

## UI/UX Design

### Scan Launcher

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Security Assessment                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Target: [example.com________________________] [+ Add More]         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Assessment Type                                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │    │
│  │  │ ◉ Recon     │  │ ○ VulnScan  │  │ ○ Full      │          │    │
│  │  │   Only      │  │   Only      │  │   Assessment│          │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Authorization                                               │    │
│  │  ○ I own this domain                                        │    │
│  │  ○ I have written permission from the owner                 │    │
│  │  ○ This is a public bug bounty target                       │    │
│  │    Program URL: [_______________________________________]    │    │
│  │                                                              │    │
│  │  ☑ I understand I am responsible for ensuring I have        │    │
│  │    authorization to scan this target                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  [Advanced Options ▼]                                               │
│                                                                      │
│                              [ Start Scan ]                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Progress View

```
┌─────────────────────────────────────────────────────────────────────┐
│  Reconnaissance: example.com                          [Cancel Scan] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Progress: ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  45%           │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Stage                          Status         Findings      │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ ✓ DNS Enumeration              Complete       12 records    │    │
│  │ ✓ Subdomain Discovery          Complete       47 subdomains │    │
│  │ ✓ WHOIS Lookup                 Complete       1 record      │    │
│  │ ● Technology Detection         Running...     —             │    │
│  │ ○ Port Scanning                Queued         —             │    │
│  │ ○ Content Discovery            Queued         —             │    │
│  │ ○ LLM Analysis                 Queued         —             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Live Findings:                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 🔵 Found: admin.example.com (nginx 1.21.0)                  │    │
│  │ 🔵 Found: api.example.com (CloudFlare)                      │    │
│  │ 🟡 Interesting: dev.example.com (no WAF detected)           │    │
│  │ 🔵 Found: blog.example.com (WordPress 6.4)                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Findings Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│  Vulnerability Findings: example.com                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ CRITICAL │ │   HIGH   │ │  MEDIUM  │ │   LOW    │ │   INFO   │  │
│  │    2     │ │    5     │ │    12    │ │    8     │ │    23    │  │
│  │   🔴     │ │   🟠     │ │   🟡     │ │   🔵     │ │   ⚪     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                                      │
│  Filter: [All Severities ▼] [All Categories ▼] [🔍 Search...]      │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 🔴 CRITICAL | SQL Injection in login form                   │    │
│  │    login.example.com/api/auth                               │    │
│  │    Parameter: username                                       │    │
│  │    [View Details] [Mark Verified] [False Positive]          │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ 🔴 CRITICAL | Remote Code Execution (CVE-2024-XXXX)         │    │
│  │    admin.example.com/upload                                  │    │
│  │    Unrestricted file upload allows PHP execution            │    │
│  │    [View Details] [Mark Verified] [False Positive]          │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ 🟠 HIGH | Cross-Site Scripting (Reflected)                  │    │
│  │    search.example.com?q=<script>                            │    │
│  │    User input reflected without sanitization                │    │
│  │    [View Details] [Mark Verified] [False Positive]          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  [Export Report ▼]  [Generate Remediation Plan]                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Deliverables:**
- [ ] Data schemas in PostgreSQL
- [ ] Job queue system (Redis-based)
- [ ] Authorization/consent management
- [ ] Basic API endpoints
- [ ] Tool executor framework

**Tools Integrated:**
- WHOIS lookup
- DNS enumeration (dig)
- crt.sh API

### Phase 2: Recon Agent MVP (Week 3-4)

**Deliverables:**
- [ ] Subdomain discovery (subfinder, crt.sh)
- [ ] Technology detection (httpx, wappalyzer)
- [ ] Content discovery (robots.txt, sitemap)
- [ ] LLM synthesis pipeline
- [ ] Basic report generation
- [ ] Scan launcher UI

**Tools Integrated:**
- subfinder
- httpx
- Wappalyzer API

### Phase 3: VulnScan Agent MVP (Week 5-6)

**Deliverables:**
- [ ] Nuclei integration (safe templates)
- [ ] Security header analysis
- [ ] SSL/TLS checking
- [ ] LLM finding explanation
- [ ] Remediation generation
- [ ] Findings dashboard UI

**Tools Integrated:**
- nuclei (core templates)
- testssl.sh
- Security Headers API

### Phase 4: Pipeline & Polish (Week 7-8)

**Deliverables:**
- [ ] Recon → VulnScan chained workflow
- [ ] Real-time progress streaming (SSE)
- [ ] PDF report generation
- [ ] Scan history & comparison
- [ ] Rate limiting enforcement
- [ ] Audit logging

### Phase 5: Advanced Features (Future)

**Potential Enhancements:**
- Port scanning (nmap) with user-provided auth
- OSINT integration (LinkedIn, HaveIBeenPwned)
- Shodan/Censys API integration
- SQLMap for authorized deep SQLi testing
- Screenshot comparison for visual changes
- Scheduled/recurring scans
- Webhook notifications
- API for CI/CD integration

---

## Future Enhancements

### Integrations Roadmap

| Integration | Purpose | Priority |
|-------------|---------|----------|
| **Shodan** | Passive port/banner data | High |
| **Censys** | Certificate & host data | High |
| **VirusTotal** | Domain/URL reputation | Medium |
| **HaveIBeenPwned** | Credential exposure | Medium |
| **Slack/Discord** | Scan notifications | Medium |
| **Jira/Linear** | Auto-create tickets | Medium |
| **GitHub** | Security advisory matching | Low |

### Advanced Agent Capabilities

- **Exploit Verification**: Safe PoC execution in sandbox
- **Remediation Validation**: Re-scan after fix to confirm
- **Trend Analysis**: Track security posture over time
- **Competitive Analysis**: Compare against industry benchmarks
- **AI-Assisted Triage**: Auto-prioritize based on context

---

## Appendix A: Tool Installation

```bash
# Subdomain discovery
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# HTTP probing
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Vulnerability scanning
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
nuclei -update-templates

# SSL testing
git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl

# DNS tools (usually pre-installed)
apt-get install -y dnsutils whois
```

---

## Appendix B: Example Reports

### Recon Report (Markdown)

```markdown
# Reconnaissance Report: example.com

**Generated:** 2026-01-16 09:30 UTC  
**Scan Duration:** 4 minutes 23 seconds

## Executive Summary

example.com has a moderate attack surface with 47 live subdomains. 
The primary technologies are React (frontend) and Django (backend) 
hosted on AWS. Notable findings include an exposed development 
environment and outdated WordPress installation on the blog subdomain.

## Attack Surface Priority

| Priority | Asset | Reason |
|----------|-------|--------|
| 🔴 High | dev.example.com | No WAF, debug mode enabled |
| 🔴 High | blog.example.com | WordPress 5.9 (outdated) |
| 🟠 Medium | api.example.com | Version header exposed |
| 🟡 Low | admin.example.com | Behind Cloudflare |

## Subdomains (47 total)

[Full list with status codes, titles, and tech stack...]

## Recommendations

1. Remove or restrict access to dev.example.com
2. Update WordPress to latest version
3. Remove server version headers from API responses
```

---

*End of Specification*
