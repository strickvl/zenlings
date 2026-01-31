//! Exercise loading and info.toml parsing.
//!
//! This module handles parsing the exercise metadata from info.toml
//! and resolving exercise file paths.

use anyhow::{Context, Result, bail};
use serde::Deserialize;
use std::fs;
use std::path::{Path, PathBuf};

/// Root structure of info.toml
#[derive(Debug, Deserialize)]
pub struct InfoToml {
    pub format_version: u32,
    pub welcome_message: Option<String>,
    pub final_message: Option<String>,
    #[serde(default)]
    pub exercises: Vec<ExerciseEntry>,
}

/// Raw exercise entry from info.toml
#[derive(Debug, Deserialize, Clone)]
pub struct ExerciseEntry {
    pub name: String,
    pub dir: String,
    #[serde(default)]
    pub hint: Option<String>,
    #[serde(default)]
    pub pipeline_name: Option<String>,
    #[serde(default)]
    pub verify_status: Option<String>,
    #[serde(default)]
    pub verify_step_count: Option<u64>,
}

/// Resolved exercise with full paths
#[derive(Debug, Clone)]
pub struct Exercise {
    pub name: String,
    pub dir: String,
    pub hint: Option<String>,

    /// Full path to the exercise file (exercises/<dir>/<name>.py)
    pub path: PathBuf,
    /// Full path to the solution file (solutions/<dir>/<name>.py)
    pub solution_path: PathBuf,

    /// Pipeline name for verification (explicit or derived from name)
    pub pipeline_name: String,
    /// Expected status for verification (default: "completed")
    pub verify_status: String,
    /// Optional: expected step count
    pub verify_step_count: Option<u64>,
}

impl Exercise {
    /// Create a resolved Exercise from an ExerciseEntry and pack root
    pub fn from_entry(entry: &ExerciseEntry, pack_root: &Path) -> Self {
        let path = pack_root
            .join("exercises")
            .join(&entry.dir)
            .join(format!("{}.py", &entry.name));

        let solution_path = pack_root
            .join("solutions")
            .join(&entry.dir)
            .join(format!("{}.py", &entry.name));

        // Use explicit pipeline_name or derive from exercise name
        let pipeline_name = entry
            .pipeline_name
            .clone()
            .unwrap_or_else(|| format!("{}_pipeline", &entry.name));

        let verify_status = entry
            .verify_status
            .clone()
            .unwrap_or_else(|| "completed".to_string());

        Self {
            name: entry.name.clone(),
            dir: entry.dir.clone(),
            hint: entry.hint.clone(),
            path,
            solution_path,
            pipeline_name,
            verify_status,
            verify_step_count: entry.verify_step_count,
        }
    }

    /// Get the display path relative to exercises/
    pub fn display_path(&self) -> String {
        format!("{}/{}.py", self.dir, self.name)
    }
}

/// Load and parse info.toml from the given path
pub fn load_info_toml(info_path: &Path) -> Result<InfoToml> {
    let content = fs::read_to_string(info_path)
        .with_context(|| format!("Failed to read info.toml from {:?}", info_path))?;

    let info: InfoToml = toml::from_str(&content)
        .with_context(|| "Failed to parse info.toml")?;

    if info.format_version != 1 {
        bail!(
            "Unsupported info.toml format version: {} (expected 1)",
            info.format_version
        );
    }

    Ok(info)
}

/// Load all exercises from info.toml with resolved paths
pub fn load_exercises(pack_root: &Path, info: &InfoToml) -> Result<Vec<Exercise>> {
    let mut exercises = Vec::with_capacity(info.exercises.len());

    for entry in &info.exercises {
        let exercise = Exercise::from_entry(entry, pack_root);

        // Verify the exercise file exists
        if !exercise.path.exists() {
            bail!(
                "Exercise file not found: {:?} (defined in info.toml as '{}')",
                exercise.path,
                entry.name
            );
        }

        exercises.push(exercise);
    }

    if exercises.is_empty() {
        bail!("No exercises found in info.toml");
    }

    Ok(exercises)
}

/// Find the pack root by searching for info.toml in parent directories
pub fn find_pack_root(start: &Path) -> Result<PathBuf> {
    let mut current = start.to_path_buf();

    // If start is a file, use its parent
    if current.is_file() {
        current = current
            .parent()
            .map(|p| p.to_path_buf())
            .unwrap_or(current);
    }

    // Search upward for info.toml
    loop {
        let info_path = current.join("info.toml");
        if info_path.exists() {
            return Ok(current);
        }

        match current.parent() {
            Some(parent) => current = parent.to_path_buf(),
            None => bail!(
                "Could not find info.toml in {:?} or any parent directory",
                start
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exercise_display_path() {
        let entry = ExerciseEntry {
            name: "load1".to_string(),
            dir: "01_loading".to_string(),
            hint: None,
            pipeline_name: None,
            verify_status: None,
            verify_step_count: None,
        };

        let exercise = Exercise::from_entry(&entry, Path::new("/tmp/zenlings"));
        assert_eq!(exercise.display_path(), "01_loading/load1.py");
        assert_eq!(exercise.pipeline_name, "load1_pipeline");
        assert_eq!(exercise.verify_status, "completed");
    }
}
