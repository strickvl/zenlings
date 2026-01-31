//! Terminal UI using crossterm.
//!
//! Simplified terminal handling - just clears screen and prints.

use anyhow::Result;
use crossterm::{
    cursor::{Hide, MoveTo, Show},
    event::{self, Event, KeyCode, KeyEvent, KeyModifiers},
    execute,
    style::{Color, Print, ResetColor, SetForegroundColor},
    terminal::{self, Clear, ClearType, disable_raw_mode, enable_raw_mode},
};
use std::io::{self, Write};
use std::time::Duration;

use crate::app_state::AppState;
use crate::verify::VerifyOutcome;

/// Terminal wrapper that manages raw mode lifecycle
pub struct Terminal {
    _private: (),
}

impl Terminal {
    /// Enter raw mode (no alternate screen - keeps it simple)
    pub fn enter() -> Result<Self> {
        enable_raw_mode()?;
        // Clear screen and hide cursor
        let mut stdout = io::stdout();
        execute!(stdout, Hide, Clear(ClearType::All), MoveTo(0, 0))?;
        Ok(Self { _private: () })
    }
}

impl Drop for Terminal {
    fn drop(&mut self) {
        let mut stdout = io::stdout();
        let _ = execute!(stdout, Show, Clear(ClearType::All), MoveTo(0, 0));
        let _ = disable_raw_mode();
    }
}

/// Key actions the user can take
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    Quit,
    Hint,
    Next,
    Prev,
    List,
    Rerun,
    Solution,
    Continue,
    None,
}

/// Poll for keyboard input with timeout
pub fn poll_key(timeout: Duration) -> Result<Option<Action>> {
    if event::poll(timeout)? {
        if let Event::Key(key) = event::read()? {
            return Ok(Some(key_to_action(key)));
        }
    }
    Ok(None)
}

/// Convert a key event to an action
fn key_to_action(key: KeyEvent) -> Action {
    if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
        return Action::Quit;
    }

    match key.code {
        KeyCode::Char('q') => Action::Quit,
        KeyCode::Char('h') => Action::Hint,
        KeyCode::Char('n') => Action::Next,
        KeyCode::Char('p') => Action::Prev,
        KeyCode::Char('l') => Action::List,
        KeyCode::Char('r') => Action::Rerun,
        KeyCode::Char('s') => Action::Solution,
        KeyCode::Enter | KeyCode::Esc => Action::Continue,
        _ => Action::None,
    }
}

/// Clear screen and reset cursor
fn clear_screen() -> Result<()> {
    let mut stdout = io::stdout();
    execute!(stdout, Clear(ClearType::All), MoveTo(0, 0))?;
    Ok(())
}

/// Print a line with color
fn print_colored(text: &str, color: Color) -> Result<()> {
    let mut stdout = io::stdout();
    execute!(
        stdout,
        SetForegroundColor(color),
        Print(text),
        ResetColor
    )?;
    Ok(())
}

/// Render the main exercise view
pub fn render_main(state: &AppState, output_buffer: &[String]) -> Result<()> {
    clear_screen()?;
    let mut stdout = io::stdout();
    let (width, height) = terminal::size().unwrap_or((80, 24));
    let separator = "─".repeat(width as usize);

    // Title
    print_colored("🎯 Zenlings", Color::Cyan)?;
    writeln!(stdout, " - Learn ZenML Dynamic Pipelines\r")?;
    writeln!(stdout, "\r")?;

    // Progress bar
    let completed = state.completed_count();
    let total = state.total_count();
    let bar_width = 30usize;
    let filled = if total > 0 { (completed * bar_width) / total } else { 0 };
    let empty = bar_width - filled;

    write!(stdout, "Progress: [")?;
    print_colored(&"█".repeat(filled), Color::Green)?;
    print_colored(&"░".repeat(empty), Color::DarkGrey)?;
    writeln!(stdout, "] {}/{}\r", completed, total)?;
    writeln!(stdout, "\r")?;

    // Current exercise
    let exercise = state.current_exercise();
    write!(stdout, "Current exercise: ")?;
    print_colored(&exercise.display_path(), Color::Blue)?;
    writeln!(stdout, "\r")?;

    // Separator
    writeln!(stdout, "{}\r", separator)?;

    // Calculate available lines for output
    let header_lines = 8; // title, progress, exercise, separator, status line
    let footer_lines = 3; // separator, keys
    let max_output_lines = (height as usize).saturating_sub(header_lines + footer_lines);

    // Status and output
    if state.verifying {
        print_colored("⏳ RUNNING", Color::Yellow)?;
        writeln!(stdout, " - Verifying exercise...\r")?;
        writeln!(stdout, "\r")?;

        // Show streaming output (last N lines)
        let start_idx = output_buffer.len().saturating_sub(max_output_lines);
        for line in &output_buffer[start_idx..] {
            let display = if line.len() > width as usize - 2 {
                &line[..width as usize - 5]
            } else {
                line.as_str()
            };
            writeln!(stdout, "{}\r", display)?;
        }
    } else if let Some(ref result) = state.last_verify {
        match result.outcome {
            VerifyOutcome::Passed => {
                print_colored("✅ PASSED", Color::Green)?;
                writeln!(stdout, " - {}\r", result.message)?;
                writeln!(stdout, "\r")?;
                writeln!(stdout, "Press 'n' to continue to the next exercise.\r")?;

                // Show last few lines of output on success too
                if !output_buffer.is_empty() {
                    writeln!(stdout, "\r")?;
                    print_colored("Output:\r\n", Color::DarkGrey)?;
                    let start_idx = output_buffer.len().saturating_sub(10);
                    for line in &output_buffer[start_idx..] {
                        let display = if line.len() > width as usize - 2 {
                            &line[..width as usize - 5]
                        } else {
                            line.as_str()
                        };
                        writeln!(stdout, "{}\r", display)?;
                    }
                }
            }
            VerifyOutcome::Failed => {
                print_colored("❌ FAILED", Color::Red)?;
                writeln!(stdout, " - {}\r", result.message)?;
                writeln!(stdout, "\r")?;

                // Show streaming output buffer (last N lines)
                let start_idx = output_buffer.len().saturating_sub(max_output_lines);
                for line in &output_buffer[start_idx..] {
                    let display = if line.len() > width as usize - 2 {
                        &line[..width as usize - 5]
                    } else {
                        line.as_str()
                    };
                    writeln!(stdout, "{}\r", display)?;
                }
            }
        }
    } else {
        print_colored("Ready", Color::DarkGrey)?;
        writeln!(stdout, " - Press 'r' to run the exercise\r")?;
    }

    writeln!(stdout, "\r")?;

    // Footer
    writeln!(stdout, "{}\r", separator)?;
    print_colored("h", Color::DarkGrey)?;
    write!(stdout, " hint  ")?;
    print_colored("n", Color::DarkGrey)?;
    write!(stdout, " next  ")?;
    print_colored("p", Color::DarkGrey)?;
    write!(stdout, " prev  ")?;
    print_colored("l", Color::DarkGrey)?;
    write!(stdout, " list  ")?;
    print_colored("r", Color::DarkGrey)?;
    write!(stdout, " run  ")?;
    print_colored("s", Color::DarkGrey)?;
    write!(stdout, " solution  ")?;
    print_colored("q", Color::DarkGrey)?;
    writeln!(stdout, " quit\r")?;

    stdout.flush()?;
    Ok(())
}

/// Render the exercise list view
pub fn render_list(state: &AppState) -> Result<()> {
    clear_screen()?;
    let mut stdout = io::stdout();

    print_colored("📋 Exercise List\r\n\r\n", Color::Cyan)?;

    for (idx, exercise) in state.exercises.iter().enumerate() {
        let is_current = idx == state.current_index;
        let is_completed = state.is_completed(&exercise.name);

        let icon = if is_completed { "✅" } else { "⬜" };
        let marker = if is_current { "→ " } else { "  " };

        if is_current {
            print_colored(marker, Color::Cyan)?;
            write!(stdout, "{} {:2}. ", icon, idx + 1)?;
            print_colored(&exercise.display_path(), Color::Cyan)?;
            writeln!(stdout, "\r")?;
        } else {
            write!(stdout, "{}{} {:2}. {}\r\n", marker, icon, idx + 1, exercise.display_path())?;
        }
    }

    writeln!(stdout, "\r")?;
    print_colored("Press any key to return...\r\n", Color::DarkGrey)?;

    stdout.flush()?;
    Ok(())
}

/// Render a modal with text (for hints/solutions)
pub fn render_modal(title: &str, content: &str) -> Result<()> {
    clear_screen()?;
    let mut stdout = io::stdout();
    let (width, _) = terminal::size().unwrap_or((80, 24));

    // Title
    print_colored(&format!("💡 {}\r\n\r\n", title), Color::Yellow)?;

    // Content - simple line-by-line with basic wrapping
    for line in content.lines().take(30) {
        if line.is_empty() {
            writeln!(stdout, "\r")?;
        } else {
            // Simple truncation for now
            let display = if line.len() > width as usize - 4 {
                &line[..width as usize - 7]
            } else {
                line
            };
            writeln!(stdout, "  {}\r", display)?;
        }
    }

    writeln!(stdout, "\r")?;
    print_colored("Press Enter or Esc to return...\r\n", Color::DarkGrey)?;

    stdout.flush()?;
    Ok(())
}

/// Render the welcome message
pub fn render_welcome(message: &str) -> Result<()> {
    render_modal("Welcome to Zenlings!", message)
}

/// Render the completion message
pub fn render_complete(message: &str) -> Result<()> {
    clear_screen()?;
    let mut stdout = io::stdout();

    print_colored("🎉 Congratulations!\r\n\r\n", Color::Green)?;

    for line in message.lines() {
        writeln!(stdout, "{}\r", line)?;
    }

    writeln!(stdout, "\r")?;
    print_colored("Press 'q' to quit or 'l' to view exercise list...\r\n", Color::DarkGrey)?;

    stdout.flush()?;
    Ok(())
}
