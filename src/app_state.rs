//! Application state and progress persistence.
//!
//! Handles loading/saving progress to .zenlings-progress.json
//! and tracking the current exercise state.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::io::Write;
use std::path::PathBuf;

use crate::exercise::{Exercise, InfoToml, find_pack_root, load_exercises, load_info_toml};
use crate::verify::VerifyResult;

const PROGRESS_FILENAME: &str = ".zenlings-progress.json";

/// Persisted progress data
#[derive(Debug, Serialize, Deserialize, Default)]
pub struct ProgressFile {
    pub version: u32,
    #[serde(default)]
    pub completed: Vec<String>,
    pub current: Option<String>,
    #[serde(default)]
    pub hints_used: HashMap<String, u32>,
    pub started_at: Option<String>,
    pub last_activity: Option<String>,
}

impl ProgressFile {
    fn new() -> Self {
        Self {
            version: 1,
            completed: Vec::new(),
            current: None,
            hints_used: HashMap::new(),
            started_at: Some(Self::now_iso()),
            last_activity: Some(Self::now_iso()),
        }
    }

    fn now_iso() -> String {
        use std::time::SystemTime;
        let duration = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .unwrap_or_default();
        format!("{}", duration.as_secs())
    }
}

/// Main application state
pub struct AppState {
    pub pack_root: PathBuf,
    pub info: InfoToml,
    pub exercises: Vec<Exercise>,

    progress_path: PathBuf,
    pub progress: ProgressFile,

    pub current_index: usize,

    /// Last verification result (if any)
    pub last_verify: Option<VerifyResult>,

    /// Whether we're currently running a verification
    pub verifying: bool,
}

impl AppState {
    /// Load application state from pack root
    pub fn load(pack_root: PathBuf) -> Result<Self> {
        let info_path = pack_root.join("info.toml");
        let info = load_info_toml(&info_path)?;
        let exercises = load_exercises(&pack_root, &info)?;

        let progress_path = pack_root.join(PROGRESS_FILENAME);
        let progress = Self::load_progress(&progress_path)?;

        // Determine current index from progress
        let current_index = Self::resolve_current_index(&exercises, &progress);

        Ok(Self {
            pack_root,
            info,
            exercises,
            progress_path,
            progress,
            current_index,
            last_verify: None,
            verifying: false,
        })
    }

    /// Load from current directory (auto-discover pack root)
    pub fn load_from_cwd() -> Result<Self> {
        let cwd = std::env::current_dir()
            .context("Failed to get current directory")?;
        let pack_root = find_pack_root(&cwd)?;
        Self::load(pack_root)
    }

    /// Load progress file or create default
    fn load_progress(path: &PathBuf) -> Result<ProgressFile> {
        if path.exists() {
            let content = fs::read_to_string(path)
                .with_context(|| format!("Failed to read progress file: {:?}", path))?;
            let progress: ProgressFile = serde_json::from_str(&content)
                .with_context(|| "Failed to parse progress file")?;
            Ok(progress)
        } else {
            Ok(ProgressFile::new())
        }
    }

    /// Determine current exercise index from progress
    fn resolve_current_index(exercises: &[Exercise], progress: &ProgressFile) -> usize {
        let completed_set: HashSet<_> = progress.completed.iter().collect();

        // If progress has a current exercise, try to find it
        if let Some(ref current_name) = progress.current {
            if let Some(idx) = exercises.iter().position(|e| &e.name == current_name) {
                return idx;
            }
        }

        // Otherwise, find first incomplete exercise
        for (idx, exercise) in exercises.iter().enumerate() {
            if !completed_set.contains(&exercise.name) {
                return idx;
            }
        }

        // All complete? Return last exercise
        exercises.len().saturating_sub(1)
    }

    /// Save progress to file
    pub fn save_progress(&mut self) -> Result<()> {
        // Update timestamps
        self.progress.last_activity = Some(ProgressFile::now_iso());
        self.progress.current = Some(self.current_exercise().name.clone());

        // Write atomically via temp file
        let tmp_path = self.progress_path.with_extension("json.tmp");
        let content = serde_json::to_string_pretty(&self.progress)
            .context("Failed to serialize progress")?;

        let mut file = fs::File::create(&tmp_path)
            .with_context(|| format!("Failed to create temp file: {:?}", tmp_path))?;
        file.write_all(content.as_bytes())
            .context("Failed to write progress")?;
        file.sync_all()?;

        fs::rename(&tmp_path, &self.progress_path)
            .with_context(|| "Failed to rename temp progress file")?;

        Ok(())
    }

    /// Get current exercise
    pub fn current_exercise(&self) -> &Exercise {
        &self.exercises[self.current_index]
    }

    /// Check if an exercise is completed
    pub fn is_completed(&self, exercise_name: &str) -> bool {
        self.progress.completed.contains(&exercise_name.to_string())
    }

    /// Mark an exercise as completed
    pub fn mark_completed(&mut self, exercise_name: &str) {
        if !self.is_completed(exercise_name) {
            self.progress.completed.push(exercise_name.to_string());
        }
    }

    /// Move to next exercise
    pub fn next(&mut self) {
        if self.current_index < self.exercises.len() - 1 {
            self.current_index += 1;
            self.last_verify = None;
        }
    }

    /// Move to previous exercise
    pub fn prev(&mut self) {
        if self.current_index > 0 {
            self.current_index -= 1;
            self.last_verify = None;
        }
    }

    /// Set current exercise by name
    pub fn set_current_by_name(&mut self, name: &str) -> Result<()> {
        if let Some(idx) = self.exercises.iter().position(|e| e.name == name) {
            self.current_index = idx;
            self.last_verify = None;
            Ok(())
        } else {
            anyhow::bail!("Exercise not found: {}", name)
        }
    }

    /// Count completed exercises
    pub fn completed_count(&self) -> usize {
        self.progress.completed.len()
    }

    /// Total number of exercises
    pub fn total_count(&self) -> usize {
        self.exercises.len()
    }

    /// Check if all exercises are completed
    pub fn all_completed(&self) -> bool {
        self.completed_count() >= self.total_count()
    }

    /// Get the welcome message
    pub fn welcome_message(&self) -> Option<&str> {
        self.info.welcome_message.as_deref()
    }

    /// Get the final message
    pub fn final_message(&self) -> Option<&str> {
        self.info.final_message.as_deref()
    }
}
