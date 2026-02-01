//! Exercise verification.
//!
//! Runs Python exercises and verifies their success via ZenML CLI.

use anyhow::{Context, Result};
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::mpsc::Sender;

use crate::exercise::Exercise;
use std::fmt;
use regex::Regex;

/// Outcome of a verification attempt
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VerifyOutcome {
    Passed,
    Failed,
}

/// Result of verifying an exercise
#[derive(Debug, Clone)]
pub struct VerifyResult {
    pub exercise_name: String,
    pub outcome: VerifyOutcome,

    /// Whether Python exited successfully
    pub python_exit_ok: bool,
    pub python_output: String,

    /// Whether ZenML CLI check was performed
    pub zenml_checked: bool,
    pub zenml_output: String,

    /// Human-readable status message
    pub message: String,
}

impl VerifyResult {
    pub fn passed(&self) -> bool {
        self.outcome == VerifyOutcome::Passed
    }

    /// Get the output to display
    pub fn display_output(&self) -> &str {
        if !self.python_exit_ok || !self.python_output.is_empty() {
            &self.python_output
        } else {
            &self.zenml_output
        }
    }
}

/// Options for verification
#[derive(Debug, Clone)]
pub struct VerifyOptions {
    pub python_bin: String,
    pub zenml_bin: String,
    pub working_dir: PathBuf,
}

impl Default for VerifyOptions {
    fn default() -> Self {
        Self {
            python_bin: "python".to_string(),
            zenml_bin: "zenml".to_string(),
            working_dir: std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")),
        }
    }
}

/// Message type for streaming output
#[derive(Debug, Clone)]
pub enum OutputLine {
    Stdout(String),
    Stderr(String),
    Done(bool), // exit success
}

/// Verify an exercise by running it and checking the result
pub fn verify_exercise(exercise: &Exercise, opts: &VerifyOptions) -> Result<VerifyResult> {
    // Step 1: Run the Python exercise
    let (python_ok, python_output) = run_python_capture(&exercise.path, opts)?;

    if !python_ok {
        return Ok(VerifyResult {
            exercise_name: exercise.name.clone(),
            outcome: VerifyOutcome::Failed,
            python_exit_ok: false,
            python_output,
            zenml_checked: false,
            zenml_output: String::new(),
            message: "Python script failed".to_string(),
        });
    }

    // Step 2: Check ZenML pipeline status
    let (zenml_ok, zenml_output, status) =
        run_zenml_status_check(&exercise.pipeline_name, opts)?;

    if !zenml_ok {
        return Ok(VerifyResult {
            exercise_name: exercise.name.clone(),
            outcome: VerifyOutcome::Failed,
            python_exit_ok: true,
            python_output,
            zenml_checked: true,
            zenml_output,
            message: "ZenML status check failed".to_string(),
        });
    }

    // Step 3: Verify the status matches expected
    let status_matches = status
        .as_ref()
        .map(|s| s == &exercise.verify_status)
        .unwrap_or(false);

    if status_matches {
        Ok(VerifyResult {
            exercise_name: exercise.name.clone(),
            outcome: VerifyOutcome::Passed,
            python_exit_ok: true,
            python_output,
            zenml_checked: true,
            zenml_output,
            message: format!("Pipeline {}", exercise.verify_status),
        })
    } else {
        let actual_status = status.unwrap_or_else(|| "unknown".to_string());
        Ok(VerifyResult {
            exercise_name: exercise.name.clone(),
            outcome: VerifyOutcome::Failed,
            python_exit_ok: true,
            python_output,
            zenml_checked: true,
            zenml_output,
            message: format!(
                "Pipeline status '{}', expected '{}'",
                actual_status, exercise.verify_status
            ),
        })
    }
}

/// Run a Python exercise with streaming output
pub fn run_python_streaming(
    exercise_path: &Path,
    opts: &VerifyOptions,
    output_tx: Sender<OutputLine>,
) -> Result<bool> {
    let mut child = Command::new(&opts.python_bin)
        .arg(exercise_path)
        .current_dir(&opts.working_dir)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .with_context(|| format!("Failed to run Python: {:?}", exercise_path))?;

    // Read stdout in a thread
    let stdout = child.stdout.take().expect("stdout piped");
    let tx_out = output_tx.clone();
    let stdout_handle = std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line) = line {
                let _ = tx_out.send(OutputLine::Stdout(line));
            }
        }
    });

    // Read stderr in a thread
    let stderr = child.stderr.take().expect("stderr piped");
    let tx_err = output_tx.clone();
    let stderr_handle = std::thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line) = line {
                let _ = tx_err.send(OutputLine::Stderr(line));
            }
        }
    });

    // Wait for process to complete
    let status = child.wait()?;

    // Wait for readers to finish
    let _ = stdout_handle.join();
    let _ = stderr_handle.join();

    let success = status.success();
    let _ = output_tx.send(OutputLine::Done(success));

    Ok(success)
}

/// Run Python and capture all output (non-streaming)
fn run_python_capture(exercise_path: &Path, opts: &VerifyOptions) -> Result<(bool, String)> {
    let output = Command::new(&opts.python_bin)
        .arg(exercise_path)
        .current_dir(&opts.working_dir)
        .output()
        .with_context(|| format!("Failed to run Python: {:?}", exercise_path))?;

    let mut combined = String::new();
    combined.push_str(&String::from_utf8_lossy(&output.stdout));
    if !output.stderr.is_empty() {
        if !combined.is_empty() {
            combined.push_str("\n");
        }
        combined.push_str(&String::from_utf8_lossy(&output.stderr));
    }

    Ok((output.status.success(), combined))
}

/// Check ZenML pipeline run status
fn run_zenml_status_check(
    pipeline_name: &str,
    opts: &VerifyOptions,
) -> Result<(bool, String, Option<String>)> {
    let output = Command::new(&opts.zenml_bin)
        .args([
            "pipeline",
            "runs",
            "list",
            "--pipeline",
            pipeline_name,
            "--size",
            "1",
            "--sort_by",
            "desc:created",
            "--output",
            "json",
        ])
        .current_dir(&opts.working_dir)
        .output()
        .with_context(|| "Failed to run zenml CLI")?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = if stderr.is_empty() { stdout.clone() } else { format!("{}\n{}", stdout, stderr) };

    if !output.status.success() {
        return Ok((false, combined, None));
    }

    // Parse JSON to extract status
    let status = parse_zenml_status(&stdout);

    Ok((true, combined, status))
}

/// Parse the status from ZenML JSON output
fn parse_zenml_status(json_str: &str) -> Option<String> {
    let value: serde_json::Value = serde_json::from_str(json_str).ok()?;

    // Status is directly on the item (not nested in "body")
    // JSON structure: { "items": [{ "status": "completed", ... }] }
    value
        .get("items")?
        .get(0)?
        .get("status")?
        .as_str()
        .map(|s| s.to_string())
}

/// Simple verification that just checks Python exit code (no ZenML check)
pub fn verify_exercise_simple(exercise: &Exercise, opts: &VerifyOptions) -> Result<VerifyResult> {
    let (python_ok, python_output) = run_python_capture(&exercise.path, opts)?;

    let outcome = if python_ok {
        VerifyOutcome::Passed
    } else {
        VerifyOutcome::Failed
    };

    let message = if python_ok {
        "Exercise completed successfully".to_string()
    } else {
        "Python script failed".to_string()
    };

    Ok(VerifyResult {
        exercise_name: exercise.name.clone(),
        outcome,
        python_exit_ok: python_ok,
        python_output,
        zenml_checked: false,
        zenml_output: String::new(),
        message,
    })
}

/// Check if ZenML is initialized in a directory
pub fn check_zenml_init(dir: &Path) -> bool {
    dir.join(".zen").exists()
}

/// Get current ZenML stack info
pub fn get_zenml_stack_info(opts: &VerifyOptions) -> Result<Option<String>> {
    let output = Command::new(&opts.zenml_bin)
        .args(["stack", "describe"])
        .current_dir(&opts.working_dir)
        .output();

    match output {
        Ok(out) if out.status.success() => {
            Ok(Some(String::from_utf8_lossy(&out.stdout).to_string()))
        }
        _ => Ok(None),
    }
}

/// Result of checking the orchestrator type
#[derive(Debug, Clone)]
pub enum OrchestratorCheckResult {
    /// Successfully found the active orchestrator's flavor
    Found(String),
    /// ZenML CLI command failed (with error details)
    CommandFailed(String),
    /// Command succeeded but couldn't parse/find active orchestrator
    NotFound,
}

/// Get the current orchestrator type (flavor) from the active orchestrator
pub fn get_orchestrator_type(opts: &VerifyOptions) -> OrchestratorCheckResult {
    let output = Command::new(&opts.zenml_bin)
        .args(["orchestrator", "list", "--output", "json"])
        .current_dir(&opts.working_dir)
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(&stdout) {
                // Find the active orchestrator and return its flavor
                if let Some(items) = value.get("items").and_then(|i| i.as_array()) {
                    for item in items {
                        if item.get("active").and_then(|a| a.as_bool()) == Some(true) {
                            if let Some(flavor) = item.get("flavor").and_then(|f| f.as_str()) {
                                return OrchestratorCheckResult::Found(flavor.to_string());
                            }
                        }
                    }
                }
            }
            OrchestratorCheckResult::NotFound
        }
        Ok(out) => {
            // Command ran but failed
            let stderr = String::from_utf8_lossy(&out.stderr);
            let error_msg = if stderr.contains("ModuleNotFoundError") || stderr.contains("ImportError") {
                "zenml CLI has import errors (broken installation?)".to_string()
            } else if stderr.is_empty() {
                "zenml command failed".to_string()
            } else {
                // Take first line of error
                stderr.lines().next().unwrap_or("unknown error").to_string()
            };
            OrchestratorCheckResult::CommandFailed(error_msg)
        }
        Err(e) => {
            // Couldn't even run the command
            if e.kind() == std::io::ErrorKind::NotFound {
                OrchestratorCheckResult::CommandFailed(format!("'{}' not found in PATH", opts.zenml_bin))
            } else {
                OrchestratorCheckResult::CommandFailed(format!("failed to run zenml: {}", e))
            }
        }
    }
}

// ============================================================================
// Startup check probes
// ============================================================================

/// Python version parsed from the interpreter
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct PythonVersion {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
}

impl PythonVersion {
    /// Minimum required Python version for Zenlings
    pub const MIN_REQUIRED: PythonVersion = PythonVersion { major: 3, minor: 9, patch: 0 };

    /// Check if this version meets the minimum requirement
    pub fn meets_minimum(&self) -> bool {
        *self >= Self::MIN_REQUIRED
    }
}

impl fmt::Display for PythonVersion {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

/// Get the Python version from the configured interpreter
pub fn get_python_version(opts: &VerifyOptions) -> Result<PythonVersion> {
    let output = Command::new(&opts.python_bin)
        .args(["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"])
        .output()
        .with_context(|| format!("Failed to run Python binary: {}", opts.python_bin))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Python command failed: {}", stderr.trim());
    }

    let version_str = String::from_utf8_lossy(&output.stdout);
    let version_str = version_str.trim();

    // Parse "3.11.5" format
    let re = Regex::new(r"^(\d+)\.(\d+)\.(\d+)$").unwrap();
    if let Some(caps) = re.captures(version_str) {
        let major: u32 = caps[1].parse().unwrap_or(0);
        let minor: u32 = caps[2].parse().unwrap_or(0);
        let patch: u32 = caps[3].parse().unwrap_or(0);
        Ok(PythonVersion { major, minor, patch })
    } else {
        anyhow::bail!("Could not parse Python version: {}", version_str);
    }
}

/// Result of probing for ZenML installation
#[derive(Debug, Clone)]
pub struct ZenmlProbe {
    /// ZenML Python package version (if importable)
    pub zenml_version: Option<String>,
    /// Whether the zenml Python package can be imported
    pub python_import_ok: bool,
    /// Whether zenml CLI is accessible and working
    pub zenml_cli_ok: bool,
    /// ZenML CLI version string
    pub zenml_cli_version: Option<String>,
}

/// Probe for ZenML installation status
pub fn probe_zenml(opts: &VerifyOptions) -> ZenmlProbe {
    // Check Python import and get version
    let (python_import_ok, zenml_version) = check_zenml_python_import(opts);

    // Check CLI
    let (zenml_cli_ok, zenml_cli_version) = check_zenml_cli(opts);

    ZenmlProbe {
        zenml_version,
        python_import_ok,
        zenml_cli_ok,
        zenml_cli_version,
    }
}

/// Check if zenml can be imported in Python and get its version
fn check_zenml_python_import(opts: &VerifyOptions) -> (bool, Option<String>) {
    let script = r#"
import sys
try:
    import importlib.metadata as md
    version = md.version("zenml")
    print(version)
    sys.exit(0)
except Exception:
    sys.exit(1)
"#;

    let output = Command::new(&opts.python_bin)
        .args(["-c", script])
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let version = String::from_utf8_lossy(&out.stdout).trim().to_string();
            (true, if version.is_empty() { None } else { Some(version) })
        }
        _ => (false, None),
    }
}

/// Check if zenml CLI is accessible and get its version
fn check_zenml_cli(opts: &VerifyOptions) -> (bool, Option<String>) {
    let output = Command::new(&opts.zenml_bin)
        .args(["--version"])
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let version_output = String::from_utf8_lossy(&out.stdout);
            // Parse "zenml, version 0.60.0" or similar
            let version = version_output
                .lines()
                .next()
                .and_then(|line| {
                    if let Some(idx) = line.find("version") {
                        Some(line[idx + 7..].trim().to_string())
                    } else {
                        Some(line.trim().to_string())
                    }
                });
            (true, version)
        }
        _ => (false, None),
    }
}

/// Try to find a working zenml binary, checking common locations
pub fn find_zenml_binary(working_dir: &Path, default_bin: &str) -> String {
    // First, check if there's a local .venv with zenml
    let venv_zenml = working_dir.join(".venv/bin/zenml");
    if venv_zenml.exists() {
        // Verify it actually works
        if let Ok(output) = Command::new(&venv_zenml).args(["--version"]).output() {
            if output.status.success() {
                return venv_zenml.to_string_lossy().to_string();
            }
        }
    }

    // Fall back to whatever is in PATH
    default_bin.to_string()
}

/// Try to find a working python binary, checking common locations
pub fn find_python_binary(working_dir: &Path, default_bin: &str) -> String {
    // First, check if there's a local .venv with python
    let venv_python = working_dir.join(".venv/bin/python");
    if venv_python.exists() {
        return venv_python.to_string_lossy().to_string();
    }

    // Fall back to whatever is in PATH
    default_bin.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_zenml_status() {
        // Status is directly on the item (not nested in "body")
        let json = r#"{"items":[{"status":"completed"}]}"#;
        assert_eq!(parse_zenml_status(json), Some("completed".to_string()));

        let json_empty = r#"{"items":[]}"#;
        assert_eq!(parse_zenml_status(json_empty), None);
    }

    #[test]
    fn test_python_version_comparison() {
        let v39 = PythonVersion { major: 3, minor: 9, patch: 0 };
        let v311 = PythonVersion { major: 3, minor: 11, patch: 5 };
        let v38 = PythonVersion { major: 3, minor: 8, patch: 10 };

        assert!(v39.meets_minimum());
        assert!(v311.meets_minimum());
        assert!(!v38.meets_minimum());

        assert!(v311 > v39);
        assert!(v39 > v38);
    }

    #[test]
    fn test_python_version_display() {
        let v = PythonVersion { major: 3, minor: 11, patch: 5 };
        assert_eq!(format!("{}", v), "3.11.5");
    }
}
