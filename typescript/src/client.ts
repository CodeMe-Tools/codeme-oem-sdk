import { execFile } from "child_process";
import { promisify } from "util";
import { CodemeCommand, DiagnosticItem, InvocationOptions, InvocationResult, TokenMetrics } from "./types";

const execFileAsync = promisify(execFile);

export class CodemeEngineClient {
  private binDir: string;
  private workingDir: string;

  constructor(options?: { binDir?: string; workingDir?: string }) {
    this.binDir = options?.binDir || "";
    this.workingDir = options?.workingDir || process.cwd();
  }

  private resolveBinary(name: string): string {
    if (this.binDir) {
      return `${this.binDir}/${name}`;
    }
    return name;
  }

  public async invoke(
    command: CodemeCommand,
    targetPath: string,
    options?: InvocationOptions
  ): Promise<InvocationResult> {
    const startTime = Date.now();
    const runId = `run_ts_${Math.random().toString(36).substring(2, 10)}`;

    const binaryMap: Record<CodemeCommand, string> = {
      syntax: "codeme-syntax",
      quality: "codeme-quality",
      verify: "codeme-verify",
      invariant: "codeme-invariant",
      toolchain: "codeme-toolchain",
    };

    const binName = binaryMap[command] || command;
    const binary = this.resolveBinary(binName);

    const args: string[] = ["run"];
    if (command === "syntax" || command === "quality") {
      args.push("--repo", targetPath);
    } else {
      args.push("--repo", targetPath);
    }

    if (options?.fix) {
      args.push("--fix");
    }
    if (options?.verbose) {
      args.push("--verbose");
    }

    try {
      const { stdout, stderr } = await execFileAsync(binary, args, {
        cwd: this.workingDir,
      });

      const rawBytes = Buffer.byteLength(stdout) + Buffer.byteLength(stderr);
      return {
        run_id: runId,
        status: "success",
        exit_code: 0,
        duration_ms: Date.now() - startTime,
        diagnostics: [],
        token_metrics: {
          raw_output_bytes: rawBytes,
          diagnostic_bytes: 0,
          suppressed_bytes: rawBytes,
          estimated_tokens_saved: Math.floor(rawBytes / 4),
        },
      };
    } catch (error: any) {
      const exitCode = error.code || 1;
      const stdout = error.stdout || "";
      const stderr = error.stderr || "";
      const rawBytes = Buffer.byteLength(stdout) + Buffer.byteLength(stderr);

      const diags: DiagnosticItem[] = [
        {
          code: `CDM-${command.toUpperCase().substring(0, 3)}-ERR`,
          file: targetPath,
          line: 1,
          column: 1,
          severity: "error",
          message: stderr.trim() || stdout.trim() || error.message,
          remediation: "Inspect engine output and fix detected violation.",
        },
      ];

      return {
        run_id: runId,
        status: exitCode === 3 ? "licensing_error" : "violation",
        exit_code: exitCode,
        duration_ms: Date.now() - startTime,
        diagnostics: diags,
        token_metrics: {
          raw_output_bytes: rawBytes,
          diagnostic_bytes: Buffer.byteLength(diags[0].message),
          suppressed_bytes: 0,
          estimated_tokens_saved: 0,
        },
      };
    }
  }
}
