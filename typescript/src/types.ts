export type CodemeCommand = "syntax" | "quality" | "verify" | "invariant" | "toolchain";
export type DiagnosticSeverity = "error" | "warning" | "info";

export interface DiagnosticItem {
  code: string;
  file: string;
  line: number;
  column: number;
  severity: DiagnosticSeverity;
  message: string;
  remediation: string;
  rule_id?: string;
}

export interface TokenMetrics {
  raw_output_bytes: number;
  diagnostic_bytes: number;
  suppressed_bytes: number;
  estimated_tokens_saved: number;
}

export interface InvocationResult {
  run_id: string;
  status: "success" | "violation" | "configuration_error" | "licensing_error" | "fatal";
  exit_code: number;
  duration_ms: number;
  diagnostics: DiagnosticItem[];
  token_metrics: TokenMetrics;
}

export interface InvocationOptions {
  fix?: boolean;
  verbose?: boolean;
  format?: "text" | "json" | "sarif";
  sandbox?: boolean;
  options?: Record<string, unknown>;
}
