//! Zenlings - Interactive ZenML Dynamic Pipelines Learning Tool
//!
//! A Rustlings-inspired CLI for learning ZenML's dynamic pipelines feature
//! through hands-on exercises with instant feedback.

mod app_state;
mod exercise;
mod hints;
mod term;
mod verify;
mod watch;

use anyhow::{Context, Result, bail};
use clap::Parser;
use std::path::PathBuf;
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

use app_state::AppState;
use term::{Action, CursorGuard, StartupCheckItem, StartupCheckStatus};
use verify::{OutputLine, PythonVersion, VerifyOptions, VerifyResult};
use watch::{Debouncer, WatchEvent};

/// Zenlings - Learn ZenML Dynamic Pipelines
#[derive(Parser, Debug)]
#[command(name = "zenlings", version, about)]
struct Args {
    /// Path to zenlings pack (directory containing info.toml)
    #[arg(long)]
    path: Option<PathBuf>,

    /// Disable file watching
    #[arg(long)]
    no_watch: bool,

    /// Python binary to use
    #[arg(long, default_value = "python")]
    python: String,

    /// ZenML binary to use
    #[arg(long, default_value = "zenml")]
    zenml: String,

    /// Jump to a specific exercise by name
    #[arg(long)]
    exercise: Option<String>,

    /// Use simple verification (exit code only, no ZenML check)
    #[arg(long)]
    simple_verify: bool,

    /// Skip startup checks
    #[arg(long)]
    skip_checks: bool,
}

/// Message to the verification worker thread
enum VerifyRequest {
    Run(exercise::Exercise),
    Stop,
}

/// Message from the verification worker
enum VerifyMessage {
    Output(OutputLine),
    Result(VerifyResult),
}

fn main() -> Result<()> {
    let args = Args::parse();

    // Load application state
    let pack_root = match &args.path {
        Some(path) => path.clone(),
        None => exercise::find_pack_root(&std::env::current_dir()?)?,
    };

    // Startup checks
    if !args.skip_checks {
        run_startup_checks(&pack_root, &args)?;
    }

    let mut state = AppState::load(pack_root.clone())
        .context("Failed to load zenlings pack")?;

    // Jump to specific exercise if requested
    if let Some(ref name) = args.exercise {
        state.set_current_by_name(name)?;
    }

    // Set up verification options (with smart binary detection)
    let verify_opts = VerifyOptions {
        python_bin: verify::find_python_binary(&pack_root, &args.python),
        zenml_bin: verify::find_zenml_binary(&pack_root, &args.zenml),
        working_dir: pack_root.clone(),
    };

    // Channels for verification
    let (verify_tx, verify_rx) = mpsc::channel::<VerifyRequest>();
    let (result_tx, result_rx) = mpsc::channel::<VerifyMessage>();

    // Spawn verification worker thread
    let simple_verify = args.simple_verify;
    let verify_opts_clone = verify_opts.clone();
    let verify_handle = thread::spawn(move || {
        verification_worker(verify_rx, result_tx, verify_opts_clone, simple_verify);
    });

    // Set up file watcher (optional)
    let (watch_tx, watch_rx) = mpsc::channel::<WatchEvent>();
    let _watch_handle = if !args.no_watch {
        let exercises_dir = pack_root.join("exercises");
        Some(watch::start_watch(&exercises_dir, watch_tx)?)
    } else {
        None
    };

    // Enter terminal UI
    let _terminal = term::Terminal::enter()?;

    // Show welcome message on first run
    if state.progress.started_at.is_none() || state.completed_count() == 0 {
        if let Some(msg) = state.welcome_message() {
            term::render_welcome(msg)?;
            wait_for_continue()?;
        }
    }

    // Streaming output buffer
    let mut output_buffer: Vec<String> = Vec::new();

    // Main event loop
    let mut debouncer = Debouncer::new(300);
    let mut pending_verify = false;

    loop {
        // Render current state
        if state.all_completed() {
            if let Some(msg) = state.final_message() {
                term::render_complete(msg)?;
            } else {
                term::render_main(&state, &output_buffer)?;
            }
        } else {
            term::render_main(&state, &output_buffer)?;
        }

        // Check for verification messages (non-blocking)
        while let Ok(msg) = result_rx.try_recv() {
            match msg {
                VerifyMessage::Output(line) => {
                    match line {
                        OutputLine::Stdout(s) | OutputLine::Stderr(s) => {
                            output_buffer.push(s);
                            // Keep buffer manageable
                            if output_buffer.len() > 100 {
                                output_buffer.remove(0);
                            }
                        }
                        OutputLine::Done(_) => {
                            // Process completion will come via Result message
                        }
                    }
                }
                VerifyMessage::Result(result) => {
                    // Only apply result if it matches current exercise
                    if result.exercise_name == state.current_exercise().name {
                        if result.passed() {
                            state.mark_completed(&result.exercise_name);
                            state.save_progress()?;
                        }
                        state.last_verify = Some(result);
                        state.verifying = false;
                    }
                }
            }
        }

        // Check for file changes (non-blocking)
        while let Ok(event) = watch_rx.try_recv() {
            if let WatchEvent::FileChanged(path) = event {
                // Only trigger if the changed file is the current exercise
                if path == state.current_exercise().path {
                    debouncer.should_process();
                    pending_verify = true;
                }
            }
        }

        // Trigger verification after debounce
        if pending_verify && debouncer.ready_to_trigger() && !state.verifying {
            state.verifying = true;
            state.last_verify = None;
            output_buffer.clear();
            verify_tx.send(VerifyRequest::Run(state.current_exercise().clone()))?;
            pending_verify = false;
            debouncer.reset();
        }

        // Poll for keyboard input
        if let Some(action) = term::poll_key(Duration::from_millis(50))? {
            match action {
                Action::Quit => break,

                Action::Hint => {
                    // Clone values we need to avoid borrow conflicts
                    let exercise_name = state.current_exercise().name.clone();
                    let hint = state.current_exercise().hint.clone();

                    if let Some(hint_text) = hint {
                        hints::record_hint_used(&mut state.progress, &exercise_name);
                        state.save_progress()?;
                        term::render_modal("Hint", &hint_text)?;
                        wait_for_continue()?;
                    } else {
                        term::render_modal("Hint", "No hint available for this exercise.")?;
                        wait_for_continue()?;
                    }
                }

                Action::Next => {
                    state.next();
                    state.save_progress()?;
                    output_buffer.clear();
                    state.last_verify = None;
                }

                Action::Prev => {
                    state.prev();
                    state.save_progress()?;
                    output_buffer.clear();
                    state.last_verify = None;
                }

                Action::List => {
                    term::render_list(&state)?;
                    wait_for_continue()?;
                }

                Action::Rerun => {
                    if !state.verifying {
                        state.verifying = true;
                        state.last_verify = None;
                        output_buffer.clear();
                        verify_tx.send(VerifyRequest::Run(state.current_exercise().clone()))?;
                    }
                }

                Action::Solution => {
                    let exercise = state.current_exercise();
                    match std::fs::read_to_string(&exercise.solution_path) {
                        Ok(content) => {
                            term::render_modal("Solution", &content)?;
                            wait_for_continue()?;
                        }
                        Err(_) => {
                            term::render_modal(
                                "Solution",
                                "Solution file not found. Keep trying!",
                            )?;
                            wait_for_continue()?;
                        }
                    }
                }

                Action::Open => {
                    let exercise = state.current_exercise();
                    let path = &exercise.path;
                    
                    // Use platform-appropriate open command
                    #[cfg(target_os = "macos")]
                    let result = std::process::Command::new("open").arg(path).spawn();
                    
                    #[cfg(target_os = "linux")]
                    let result = std::process::Command::new("xdg-open").arg(path).spawn();
                    
                    #[cfg(target_os = "windows")]
                    let result = std::process::Command::new("cmd")
                        .args(["/C", "start", "", &path.to_string_lossy()])
                        .spawn();
                    
                    #[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
                    let result: Result<std::process::Child, std::io::Error> = Err(std::io::Error::new(
                        std::io::ErrorKind::Unsupported,
                        "Platform not supported",
                    ));

                    if let Err(e) = result {
                        term::render_modal("Open", &format!("Could not open file: {}", e))?;
                        wait_for_continue()?;
                    }
                }

                Action::Continue | Action::None => {}
            }
        }
    }

    // Clean up
    let _ = verify_tx.send(VerifyRequest::Stop);
    let _ = verify_handle.join();

    Ok(())
}

/// Outcome of a single startup check
enum CheckOutcome {
    Pass { details: String },
    Warn { details: String },
    Fail { error: String, help: Vec<String> },
}

/// Run a check with spinner animation
fn run_check_with_spinner<F>(
    items: &mut [StartupCheckItem],
    idx: usize,
    check_fn: F,
) -> Result<CheckOutcome>
where
    F: FnOnce() -> Result<CheckOutcome> + Send + 'static,
{
    use std::sync::mpsc;

    // Start the check in a background thread
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let result = check_fn();
        let _ = tx.send(result);
    });

    // Animate spinner while waiting
    let mut frame = 0usize;
    loop {
        items[idx].status = StartupCheckStatus::Running { frame };
        term::render_startup_checklist("Zenlings - Startup Checks", items, None)?;

        // Check if result is ready (non-blocking)
        match rx.try_recv() {
            Ok(result) => return result,
            Err(mpsc::TryRecvError::Empty) => {
                // Still running, continue animation
                thread::sleep(Duration::from_millis(80));
                frame = frame.wrapping_add(1);
            }
            Err(mpsc::TryRecvError::Disconnected) => {
                // Thread panicked or dropped sender
                return Ok(CheckOutcome::Fail {
                    error: "Check crashed unexpectedly".to_string(),
                    help: vec![],
                });
            }
        }
    }
}

/// Apply check outcome to the checklist item
fn apply_outcome(items: &mut [StartupCheckItem], idx: usize, outcome: &CheckOutcome) {
    items[idx].status = match outcome {
        CheckOutcome::Pass { details } => StartupCheckStatus::Passed {
            details: details.clone(),
        },
        CheckOutcome::Warn { details } => StartupCheckStatus::Warn {
            details: details.clone(),
        },
        CheckOutcome::Fail { error, help } => StartupCheckStatus::Failed {
            error: error.clone(),
            help: help.clone(),
        },
    };
}

/// Run startup checks with visual feedback
fn run_startup_checks(pack_root: &PathBuf, args: &Args) -> Result<()> {
    // Hide cursor during checks (restored automatically on drop)
    let _cursor = CursorGuard::new()?;

    // Smart binary detection: prefer .venv binaries if they exist
    let python_bin = verify::find_python_binary(pack_root, &args.python);
    let zenml_bin = verify::find_zenml_binary(pack_root, &args.zenml);

    // Build verification options
    let opts = VerifyOptions {
        python_bin,
        zenml_bin,
        working_dir: pack_root.clone(),
    };

    // Initialize checklist items
    let mut items = vec![
        StartupCheckItem {
            label: "Python version".to_string(),
            status: StartupCheckStatus::Pending,
        },
        StartupCheckItem {
            label: "ZenML installed".to_string(),
            status: StartupCheckStatus::Pending,
        },
        StartupCheckItem {
            label: "ZenML initialized".to_string(),
            status: StartupCheckStatus::Pending,
        },
        StartupCheckItem {
            label: "Orchestrator".to_string(),
            status: StartupCheckStatus::Pending,
        },
    ];

    // Render initial state
    term::render_startup_checklist("Zenlings - Startup Checks", &items, None)?;

    // -------------------------------------------------------------------------
    // Check 1: Python version >= 3.9
    // -------------------------------------------------------------------------
    let opts_clone = opts.clone();
    let outcome = run_check_with_spinner(&mut items, 0, move || {
        match verify::get_python_version(&opts_clone) {
            Ok(version) => {
                if version.meets_minimum() {
                    Ok(CheckOutcome::Pass {
                        details: format!("Python {}", version),
                    })
                } else {
                    Ok(CheckOutcome::Fail {
                        error: format!("Python {} (need >= {})", version, PythonVersion::MIN_REQUIRED),
                        help: vec![
                            "Install Python 3.9 or newer".to_string(),
                            format!("Or use --python <path> to specify a different interpreter"),
                        ],
                    })
                }
            }
            Err(e) => Ok(CheckOutcome::Fail {
                error: format!("Could not detect Python: {}", e),
                help: vec![
                    "Ensure Python is installed and in your PATH".to_string(),
                    "Or use --python <path> to specify the interpreter".to_string(),
                ],
            }),
        }
    })?;

    apply_outcome(&mut items, 0, &outcome);
    term::render_startup_checklist("Zenlings - Startup Checks", &items, None)?;

    if matches!(outcome, CheckOutcome::Fail { .. }) {
        thread::sleep(Duration::from_millis(100)); // Brief pause to show final state
        bail!("Python check failed");
    }

    // -------------------------------------------------------------------------
    // Check 2: ZenML installed
    // -------------------------------------------------------------------------
    let opts_clone = opts.clone();
    let outcome = run_check_with_spinner(&mut items, 1, move || {
        let probe = verify::probe_zenml(&opts_clone);

        if !probe.python_import_ok {
            return Ok(CheckOutcome::Fail {
                error: "ZenML not found in Python environment".to_string(),
                help: vec![
                    "Install with: pip install \"zenml[local]\"".to_string(),
                    format!("Make sure to install in the same environment as --python"),
                ],
            });
        }

        if !probe.zenml_cli_ok {
            return Ok(CheckOutcome::Fail {
                error: "ZenML CLI not accessible".to_string(),
                help: vec![
                    "Ensure 'zenml' command is in your PATH".to_string(),
                    "Or use --zenml <path> to specify the CLI location".to_string(),
                ],
            });
        }

        // Both OK - show versions
        let version_info = match (&probe.zenml_version, &probe.zenml_cli_version) {
            (Some(py_ver), Some(_cli_ver)) => format!("v{}", py_ver),
            (Some(py_ver), None) => format!("v{}", py_ver),
            (None, Some(cli_ver)) => format!("CLI v{}", cli_ver),
            (None, None) => "installed".to_string(),
        };

        Ok(CheckOutcome::Pass { details: version_info })
    })?;

    apply_outcome(&mut items, 1, &outcome);
    term::render_startup_checklist("Zenlings - Startup Checks", &items, None)?;

    if matches!(outcome, CheckOutcome::Fail { .. }) {
        thread::sleep(Duration::from_millis(100));
        bail!("ZenML installation check failed");
    }

    // -------------------------------------------------------------------------
    // Check 3: ZenML initialized (.zen directory)
    // -------------------------------------------------------------------------
    let pack_root_clone = pack_root.clone();
    let outcome = run_check_with_spinner(&mut items, 2, move || {
        if verify::check_zenml_init(&pack_root_clone) {
            Ok(CheckOutcome::Pass {
                details: ".zen directory found".to_string(),
            })
        } else {
            Ok(CheckOutcome::Fail {
                error: "ZenML not initialized".to_string(),
                help: vec![
                    format!("cd {}", pack_root_clone.display()),
                    "zenml init".to_string(),
                ],
            })
        }
    })?;

    apply_outcome(&mut items, 2, &outcome);
    term::render_startup_checklist("Zenlings - Startup Checks", &items, None)?;

    if matches!(outcome, CheckOutcome::Fail { .. }) {
        thread::sleep(Duration::from_millis(100));
        bail!("ZenML not initialized");
    }

    // -------------------------------------------------------------------------
    // Check 4: Orchestrator is 'local' (warn only, don't fail)
    // -------------------------------------------------------------------------
    let opts_clone = opts.clone();
    let outcome = run_check_with_spinner(&mut items, 3, move || {
        use verify::OrchestratorCheckResult;
        match verify::get_orchestrator_type(&opts_clone) {
            OrchestratorCheckResult::Found(flavor) if flavor == "local" => Ok(CheckOutcome::Pass {
                details: "local".to_string(),
            }),
            OrchestratorCheckResult::Found(flavor) => Ok(CheckOutcome::Warn {
                details: format!("'{}' (recommend 'local' for fast feedback)", flavor),
            }),
            OrchestratorCheckResult::NotFound => Ok(CheckOutcome::Warn {
                details: "no active orchestrator found".to_string(),
            }),
            OrchestratorCheckResult::CommandFailed(err) => Ok(CheckOutcome::Warn {
                details: err,
            }),
        }
    })?;

    apply_outcome(&mut items, 3, &outcome);
    term::render_startup_checklist("Zenlings - Startup Checks", &items, Some("All checks passed! Starting Zenlings..."))?;

    // Brief pause so user can see the final checklist before TUI clears it
    thread::sleep(Duration::from_millis(800));

    Ok(())
}

/// Wait for user to press Enter/Esc to continue
fn wait_for_continue() -> Result<()> {
    loop {
        if let Some(action) = term::poll_key(Duration::from_millis(100))? {
            match action {
                Action::Continue | Action::Quit => break,
                _ => {}
            }
        }
    }
    Ok(())
}

/// Verification worker thread with streaming output
fn verification_worker(
    rx: mpsc::Receiver<VerifyRequest>,
    tx: mpsc::Sender<VerifyMessage>,
    opts: VerifyOptions,
    simple_mode: bool,
) {
    for request in rx {
        match request {
            VerifyRequest::Run(exercise) => {
                // Create a channel for streaming output
                let (output_tx, output_rx) = mpsc::channel::<OutputLine>();

                // Forward output to main thread
                let tx_clone = tx.clone();
                let output_forwarder = thread::spawn(move || {
                    for line in output_rx {
                        let is_done = matches!(line, OutputLine::Done(_));
                        let _ = tx_clone.send(VerifyMessage::Output(line));
                        if is_done {
                            break;
                        }
                    }
                });

                // Run the exercise with streaming
                let python_ok = verify::run_python_streaming(&exercise.path, &opts, output_tx)
                    .unwrap_or(false);

                // Wait for output forwarding to complete
                let _ = output_forwarder.join();

                // Build result
                let result = if simple_mode {
                    VerifyResult {
                        exercise_name: exercise.name.clone(),
                        outcome: if python_ok {
                            verify::VerifyOutcome::Passed
                        } else {
                            verify::VerifyOutcome::Failed
                        },
                        python_exit_ok: python_ok,
                        python_output: String::new(), // Output was streamed
                        zenml_checked: false,
                        zenml_output: String::new(),
                        message: if python_ok {
                            "Exercise completed successfully".to_string()
                        } else {
                            "Python script failed".to_string()
                        },
                    }
                } else if !python_ok {
                    VerifyResult {
                        exercise_name: exercise.name.clone(),
                        outcome: verify::VerifyOutcome::Failed,
                        python_exit_ok: false,
                        python_output: String::new(),
                        zenml_checked: false,
                        zenml_output: String::new(),
                        message: "Python script failed".to_string(),
                    }
                } else {
                    // Check ZenML status
                    match verify::verify_exercise(&exercise, &opts) {
                        Ok(r) => r,
                        Err(e) => VerifyResult {
                            exercise_name: exercise.name.clone(),
                            outcome: verify::VerifyOutcome::Failed,
                            python_exit_ok: true,
                            python_output: String::new(),
                            zenml_checked: false,
                            zenml_output: format!("Error: {}", e),
                            message: format!("Verification error: {}", e),
                        },
                    }
                };

                let _ = tx.send(VerifyMessage::Result(result));
            }
            VerifyRequest::Stop => break,
        }
    }
}
