//! Exercise verification.
//!
//! Runs Python exercises and verifies their success via ZenML CLI.

use anyhow::{Context, Result};
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::mpsc::Sender;

use crate::exercise::Exercise;

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

    value
        .get("items")?
        .get(0)?
        .get("body")?
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

/// Get the current orchestrator type
pub fn get_orchestrator_type(opts: &VerifyOptions) -> Result<Option<String>> {
    let output = Command::new(&opts.zenml_bin)
        .args(["stack", "describe", "--output", "json"])
        .current_dir(&opts.working_dir)
        .output();

    match output {
        Ok(out) if out.status.success() => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(&stdout) {
                // Try to extract orchestrator flavor
                if let Some(orchestrator) = value.get("orchestrator") {
                    if let Some(flavor) = orchestrator.get("flavor") {
                        return Ok(flavor.as_str().map(|s| s.to_string()));
                    }
                }
            }
            Ok(None)
        }
        _ => Ok(None),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_zenml_status() {
        let json = r#"{"items":[{"body":{"status":"completed"}}]}"#;
        assert_eq!(parse_zenml_status(json), Some("completed".to_string()));

        let json_empty = r#"{"items":[]}"#;
        assert_eq!(parse_zenml_status(json_empty), None);
    }
}
