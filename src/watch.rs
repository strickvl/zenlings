//! File system watching for exercise changes.
//!
//! Uses the notify crate to watch for file modifications
//! and trigger re-verification.

use anyhow::{Context, Result};
use notify::{Config, Event, RecommendedWatcher, RecursiveMode, Watcher};
use std::path::{Path, PathBuf};
use std::sync::mpsc::{self, Receiver, Sender};
use std::time::Duration;

/// Events emitted by the file watcher
#[derive(Debug)]
pub enum WatchEvent {
    /// An exercise file was modified
    FileChanged(PathBuf),
    /// An error occurred while watching
    Error(String),
}

/// Handle to a running file watcher
pub struct WatchHandle {
    _watcher: RecommendedWatcher,
}

/// Start watching a directory for file changes
///
/// Returns a handle that keeps the watcher alive, and a receiver
/// for watch events.
pub fn start_watch(
    watch_root: &Path,
    tx: Sender<WatchEvent>,
) -> Result<WatchHandle> {
    // Create a channel for notify events
    let (notify_tx, notify_rx) = mpsc::channel();

    // Create the watcher with a short delay for debouncing
    let mut watcher = RecommendedWatcher::new(
        move |res: notify::Result<Event>| {
            let _ = notify_tx.send(res);
        },
        Config::default().with_poll_interval(Duration::from_millis(200)),
    )
    .context("Failed to create file watcher")?;

    // Watch the exercises directory recursively
    watcher
        .watch(watch_root, RecursiveMode::Recursive)
        .with_context(|| format!("Failed to watch directory: {:?}", watch_root))?;

    // Spawn a thread to convert notify events to our WatchEvents
    let watch_root_owned = watch_root.to_path_buf();
    std::thread::spawn(move || {
        process_notify_events(notify_rx, tx, &watch_root_owned);
    });

    Ok(WatchHandle { _watcher: watcher })
}

/// Process raw notify events and emit WatchEvents
fn process_notify_events(
    notify_rx: Receiver<notify::Result<Event>>,
    tx: Sender<WatchEvent>,
    _watch_root: &Path,
) {
    for res in notify_rx {
        match res {
            Ok(event) => {
                // Only care about modify/create events
                if matches!(
                    event.kind,
                    notify::EventKind::Modify(_) | notify::EventKind::Create(_)
                ) {
                    for path in event.paths {
                        // Only watch .py files
                        if path.extension().map(|e| e == "py").unwrap_or(false) {
                            if tx.send(WatchEvent::FileChanged(path)).is_err() {
                                // Receiver dropped, exit thread
                                return;
                            }
                        }
                    }
                }
            }
            Err(e) => {
                let _ = tx.send(WatchEvent::Error(e.to_string()));
            }
        }
    }
}

/// Simple debouncer for watch events
pub struct Debouncer {
    last_event_time: Option<std::time::Instant>,
    debounce_duration: Duration,
}

impl Debouncer {
    pub fn new(debounce_ms: u64) -> Self {
        Self {
            last_event_time: None,
            debounce_duration: Duration::from_millis(debounce_ms),
        }
    }

    /// Record an event and return true if it should be processed
    /// (i.e., enough time has passed since the last event)
    pub fn should_process(&mut self) -> bool {
        let now = std::time::Instant::now();

        if let Some(last) = self.last_event_time {
            if now.duration_since(last) < self.debounce_duration {
                // Too soon, update timestamp but don't process
                self.last_event_time = Some(now);
                return false;
            }
        }

        self.last_event_time = Some(now);
        true
    }

    /// Check if we should trigger (enough time passed since last event)
    pub fn ready_to_trigger(&self) -> bool {
        if let Some(last) = self.last_event_time {
            std::time::Instant::now().duration_since(last) >= self.debounce_duration
        } else {
            false
        }
    }

    /// Reset the debouncer
    pub fn reset(&mut self) {
        self.last_event_time = None;
    }
}
