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
use term::Action;
use verify::{OutputLine, VerifyOptions, VerifyResult};
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

    // Set up verification options
    let verify_opts = VerifyOptions {
        python_bin: args.python.clone(),
        zenml_bin: args.zenml.clone(),
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

                Action::Continue | Action::None => {}
            }
        }
    }

    // Clean up
    let _ = verify_tx.send(VerifyRequest::Stop);
    let _ = verify_handle.join();

    Ok(())
}

/// Run startup checks
fn run_startup_checks(pack_root: &PathBuf, args: &Args) -> Result<()> {
    // Check if ZenML is initialized
    if !verify::check_zenml_init(pack_root) {
        eprintln!("\n❌ ZenML is not initialized in this directory.");
        eprintln!("\nPlease run:");
        eprintln!("  cd {}", pack_root.display());
        eprintln!("  zenml init");
        eprintln!("\nThen try again.");
        bail!("ZenML not initialized");
    }

    // Check orchestrator type
    let opts = VerifyOptions {
        python_bin: args.python.clone(),
        zenml_bin: args.zenml.clone(),
        working_dir: pack_root.clone(),
    };

    if let Ok(Some(orchestrator)) = verify::get_orchestrator_type(&opts) {
        if orchestrator != "local" {
            eprintln!("\n⚠️  Note: You're using the '{}' orchestrator.", orchestrator);
            eprintln!("   Zenlings works best with the 'local' orchestrator for fast feedback.");
            eprintln!("   To switch: zenml stack set default");
            eprintln!("");
            // Don't fail, just warn
        }
    }

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
