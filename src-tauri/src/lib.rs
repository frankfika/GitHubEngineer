use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::{Manager, WindowEvent};

#[derive(Default)]
struct BackendProcess(Mutex<Option<Child>>);

fn packaged_backend_path() -> Result<PathBuf, String> {
    let executable = std::env::current_exe()
        .map_err(|error| format!("could not locate desktop executable: {error}"))?;
    let directory = executable
        .parent()
        .ok_or_else(|| "desktop executable has no parent directory".to_string())?;
    let file_name = if cfg!(windows) {
        "github-engineer-backend.exe"
    } else {
        "github-engineer-backend"
    };
    let candidates = [
        directory.join(file_name),
        directory.join("../Resources").join(file_name),
        directory.join("resources").join(file_name),
    ];
    candidates
        .into_iter()
        .find(|candidate| candidate.is_file())
        .ok_or_else(|| format!("packaged backend sidecar {file_name} was not found"))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(BackendProcess::default())
        .setup(|app| {
            if !cfg!(debug_assertions) {
                let backend = packaged_backend_path()?;
                let data_dir = app.path().app_data_dir().map_err(|error| {
                    format!("could not locate application data directory: {error}")
                })?;
                std::fs::create_dir_all(&data_dir).map_err(|error| {
                    format!("could not create application data directory: {error}")
                })?;
                let config = data_dir.join(".ghe").join("config.yml");
                let child = Command::new(backend)
                    .arg("--serve")
                    .args(["--serve-host", "127.0.0.1"])
                    .arg("--config")
                    .arg(config)
                    .current_dir(data_dir)
                    .stdin(Stdio::null())
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .spawn()
                    .map_err(|error| format!("could not start packaged backend: {error}"))?;
                *app.state::<BackendProcess>()
                    .0
                    .lock()
                    .map_err(|_| "desktop backend process lock was poisoned".to_string())? =
                    Some(child);
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::Destroyed) {
                if let Ok(mut process) = window.state::<BackendProcess>().0.lock() {
                    if let Some(child) = process.as_mut() {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                    *process = None;
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running GitHub Engineer");
}
