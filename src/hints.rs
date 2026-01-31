//! Hint display and usage tracking.

use crate::app_state::ProgressFile;
use crate::exercise::Exercise;

/// Get the hint for an exercise
pub fn hint_for(exercise: &Exercise) -> Option<&str> {
    exercise.hint.as_deref()
}

/// Record that a hint was used for an exercise
pub fn record_hint_used(progress: &mut ProgressFile, exercise_name: &str) {
    let count = progress
        .hints_used
        .entry(exercise_name.to_string())
        .or_insert(0);
    *count += 1;
}

/// Get the number of times hints were used for an exercise
pub fn hints_used_count(progress: &ProgressFile, exercise_name: &str) -> u32 {
    progress
        .hints_used
        .get(exercise_name)
        .copied()
        .unwrap_or(0)
}
